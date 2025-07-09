import requests
import csv
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime, timezone, timedelta
import threading
# HTTP转发目标URL
SEND_URL = "http://192.168.5.248/api/gnss_pi.php"  # 可根据实际情况修改

def send_data(params, url=SEND_URL):
    try:
        r = requests.get(url, params)
        if r.status_code == 200:
            return r.text
        else:
            print("Error on HTTP request")
    except Exception as e:
        print(f"出错: {str(e)}")
        return False

# 从CSV文件加载无人机device_sn与drone_id映射
def load_drones_from_csv(csv_path):
    drones = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 假设csv有device_sn,drone_id两列
                if row.get("device_sn") and row.get("drone_id"):
                    drones.append({
                        "device_sn": row["device_sn"].strip(),
                        "drone_id": row["drone_id"].strip()
                    })
    except Exception as e:
        print(f"加载无人机映射CSV失败: {e}")
    return drones

# === 定时HTTP转发线程 ===
def periodic_http_publish():
    """每2秒自动遍历所有活跃无人机，转发最新消息"""
    while True:
        now_ms = int(time.time() * 1000)
        active_drones = []
        for drone_id, last_time in list(drone_time_cache.items()):
            if now_ms - last_time <= 5000:
                active_drones.append(drone_id)
            else:
                # 超时无人机移除
                drone_custom_cache.pop(drone_id, None)
                drone_time_cache.pop(drone_id, None)
        for drone_id in active_drones:
            custom_msg = drone_custom_cache[drone_id]
            print(f"[定时] 2s转发 {drone_id} 最新消息: {custom_msg}")
            http_resp = send_data(custom_msg)
            if http_resp:
                try:
                    response_data = json.loads(http_resp)
                    print(f"[定时] HTTP转发响应: {response_data}")
                except Exception:
                    print(f"[定时] HTTP转发响应: {http_resp}")
        time.sleep(2)

# 加载外部CSV
DRONES = load_drones_from_csv("drones_device_sn_id.csv")

# MQTT主题模板
MQTT_TOPIC_RAW_WILDCARD = "thing/product/+/osd"
MQTT_TOPIC_PUB = "uav/status/uav_osd"

# MQTT参数
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
username = "MQTT1"
password = "123456"

# 日志文件路径（带时间戳）
log_time = datetime.now().strftime("%Y%m%d_%H%M%S")
RAW_LOG_FILE = f"Log/dji_raw_mqtt_message_{log_time}.txt"
CONVERTED_LOG_FILE = f"Log/dji_converted_mqtt_message_{log_time}.txt"

# 记录原始和转换后的消息到日志文件
def log_to_file(filepath, data_dict):
    with open(filepath, "a", encoding="utf-8") as f:
        json.dump(data_dict, f, ensure_ascii=False)
        f.write("\n")

# 将DJI OSD数据转换为自定义格式
def convert_dji_to_custom(data: dict, drone_id: str) -> dict:
    """单机消息转换（保留，兼容单机osd消息）"""
    ts = datetime.fromtimestamp(int(data.get("timestamp", 0)) / 1000.0, tz=timezone.utc)
    dji_data = data.get("data", {})
    # 解析目标HTTP转发所需字段
    result = {
        "ID": drone_id,
        "UTC": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "Lon": dji_data.get("longitude", 0.0),
        "Lat": dji_data.get("latitude", 0.0),
        "ACT": "GPSSND"
    }
    return result

def convert_fleet_to_custom(fleet_id: str, timestamp: int, drones: list) -> dict:
    """多机消息转换，生成多机结构"""
    ts = datetime.fromtimestamp(timestamp / 1000.0, tz=timezone.utc)
    iso_time = ts.isoformat().replace("+00:00", "Z")
    return {
        "fleet_id": fleet_id,
        "timestamp": iso_time,
        "drones": drones
    }

# 接收计数
# message_count = 0

# 用于缓存所有无人机的最新自定义消息
drone_custom_cache = {}  # drone_id: custom_msg
drone_raw_cache = {}     # drone_id: raw_msg
drone_time_cache = {}    # drone_id: last_update_time(ms)

FLEET_ID = "fleet_001"

# 当连接到 MQTT Broker 成功时回调
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("成功连接到 MQTT Broker")
        client.subscribe(MQTT_TOPIC_RAW_WILDCARD)
        print(f"通配符订阅主题: {MQTT_TOPIC_RAW_WILDCARD}")
    else:
        print("连接失败，返回码:", reason_code)

# 当接收到消息时回调
def on_message(client, userdata, msg):
    # global message_count
    # message_count += 1
    try:
        raw_payload = json.loads(msg.payload.decode())
        # 判断是否为多机结构（含有drones字段且为list）
        if isinstance(raw_payload, dict) and "drones" in raw_payload and isinstance(raw_payload["drones"], list):
            # 多机结构，逐台转发
            log_to_file(RAW_LOG_FILE, raw_payload)
            for drone in raw_payload["drones"]:
                drone_id = drone.get("drone_id", None)
                if not drone_id:
                    continue
                custom_msg = convert_dji_to_custom(drone, drone_id)
                log_to_file(CONVERTED_LOG_FILE, custom_msg)
                print(f"[多机] 即将转发参数：{custom_msg}")
                http_resp = send_data(custom_msg)
                if http_resp:
                    try:
                        response_data = json.loads(http_resp)
                        print(f"HTTP转发响应: {response_data}")
                    except Exception:
                        print(f"HTTP转发响应: {http_resp}")
        else:
            # 单机结构
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 4:
                device_sn = topic_parts[2]
            else:
                print(f"无法从topic解析device_sn: {msg.topic}")
                return
            if len(device_sn) != 20:
                print(f"过滤非无人机消息，device_sn: {device_sn}, topic: {msg.topic}")
                return
            drone_id = None
            for drone in DRONES:
                if drone["device_sn"] == device_sn:
                    drone_id = drone["drone_id"]
                    break
            if not drone_id:
                drone_id = device_sn
            print(f"收到消息，来自 {drone_id}")
            log_to_file(RAW_LOG_FILE, raw_payload)
            custom_msg = convert_dji_to_custom(raw_payload, drone_id)
            log_to_file(CONVERTED_LOG_FILE, custom_msg)
            # HTTP转发
            print("即将转发参数：", custom_msg)
            http_resp = send_data(custom_msg)
            if http_resp:
                try:
                    response_data = json.loads(http_resp)
                    print(f"HTTP转发响应: {response_data}")
                except Exception:
                    print(f"HTTP转发响应: {http_resp}")
    except Exception as e:
        print("消息处理失败:", e)

def create_mqtt_client(on_message_callback=on_message) -> mqtt.Client:
    client = mqtt.Client()
    client.username_pw_set(username=username, password=password)
    client.on_connect = on_connect
    client.on_message = on_message_callback
    return client

def connect_and_subscribe(client: mqtt.Client):
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

# 新增：记录已发出的消息条数
published_count = 0

def publish_message(client: mqtt.Client, topic: str, message: dict):
    global published_count
    try:
        payload_str = json.dumps(message)
        client.publish(topic, payload_str)
        published_count += 1
        print(f"发布消息到 {topic}，累计已发出 {published_count} 条消息")
    except Exception as e:
        print("发布失败:", e)

def periodic_publish(client: mqtt.Client):
    """每2秒自动判断当前缓存无人机数量，自动切换单机/多机格式发布"""
    while True:
        # 只保留5秒内活跃的无人机
        now_ms = int(time.time() * 1000)
        active_drones = []
        for drone_id, last_time in list(drone_time_cache.items()):
            if now_ms - last_time <= 5000:
                active_drones.append(drone_id)
            else:
                # 超时无人机移除
                drone_custom_cache.pop(drone_id, None)
                drone_time_cache.pop(drone_id, None)
        # 统一按机队格式发出
        if len(active_drones) > 0:
            drones_list = [drone_custom_cache[drone_id] for drone_id in active_drones]
            latest_ts = max([drone_time_cache[drone_id] for drone_id in active_drones])
            fleet_msg = convert_fleet_to_custom(FLEET_ID, latest_ts, drones_list)
            log_to_file(CONVERTED_LOG_FILE, fleet_msg)
            publish_message(client, MQTT_TOPIC_PUB, fleet_msg)
        # 没有活跃无人机则不发
        time.sleep(2)

# 创建 MQTT 客户端并连接
if __name__ == "__main__":
    client = create_mqtt_client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_TOPIC_RAW_WILDCARD)
    # 启动定时HTTP转发线程
    http_thread = threading.Thread(target=periodic_http_publish)
    http_thread.daemon = True
    http_thread.start()
    client.loop_forever()