import json
import time
import paho.mqtt.client as mqtt
import threading
import copy

# 参数配置
MQTT_BROKER = "127.0.0.1"   # MQTT Broker 主机地址
MQTT_PORT = 1883    # MQTT 端口号
username = "admin"   # MQTT 用户名
password = "public"  # MQTT 用户密码
MQTT_TOPIC_PUB = "uav/status/uav_osd"        # 发布目标主题
NUM_DRONES = 3  # 无人机数量

# 单架无人机的消息模板
drone_template = {
    "drone_id": "DJI_Matrice_4E_001",
    "timestamp": "2025-06-23T10:04:32.960000Z",
    "flight_status": {
        "mode_code": 1,
        "uav_lat": 22.123456,
        "uav_lon": 113.654321,
        "uav_alt": 87.0712203979492,
        "uav_rel_alt": 20.0,
        "uav_speed": 10.5,
        "uav_yaw": -72.6,
        "uav_pitch": 4.4,
        "uav_roll": 0.2,
        "battery_percent": 24,
        "wind_speed": 1.6
    },
    "payloads": [
        {
            "type": 0,
            "payload_id": "CAM_001",
            "status": 0,
            "parameters": {
                "cam_roll": 0,
                "cam_pitch": 0,
                "cam_yaw": -72.5,
                "zoom": 7
            }
        },
        {
            "type": 1,
            "payload_id": "THERM_001",
            "status": 0,
            "parameters": {
                "cam_roll": 0,
                "cam_pitch": 0,
                "cam_yaw": -72.5
            }
        },
        {
            "type": 2,
            "payload_id": "LIDAR_001",
            "status": 1,
            "parameters": {}
        },
        {
            "type": 3,
            "payload_id": "MS_001",
            "status": 0,
            "parameters": {}
        }
    ]
}

# 创建包含多架无人机的数据结构

fleet_data = {
    "fleet_id": "DJI_FLEET_001",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.localtime()),
    "drones": []
}

# 初始化多架无人机数据
for i in range(NUM_DRONES):
    drone = copy.deepcopy(drone_template)
    drone["drone_id"] = f"DJI_Matrice_4E_{i+1:03d}"
    fleet_data["drones"].append(drone)

# 当客户端成功连接到 MQTT Broker 后自动回调
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("成功连接到 MQTT Broker")
    else:
        print("连接失败，返回码:", reason_code)


# 创建并配置一个 MQTT 客户端实例
def create_mqtt_client() -> mqtt.Client:
    client = mqtt.Client()
    client.username_pw_set(username=username, password=password)
    client.on_connect = on_connect
    return client

# 连接到 MQTT Broker 并开始监听
def connect_and_subscribe(client: mqtt.Client):
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

message_count = 0   # 发布消息计数
# 发布消息到指定的 MQTT 主题
def publish_message(client: mqtt.Client, topic: str, message: dict):
    global message_count
    message_count += 1
    try:
        # 更新时间戳
        message["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.localtime())
        payload_str = json.dumps(message)
        client.publish(topic, payload_str)
        print(f"发布第 {message_count} 条消息")
        print(f"已发布消息到 {topic}：{payload_str}")
    except Exception as e:
        print("发布失败:", e)

# 模拟循环发布线程
def simulate_loop():
    while True:
        # 更新fleet时间戳
        fleet_data["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.localtime())
        # 发布整个机队数据
        publish_message(client, MQTT_TOPIC_PUB, fleet_data)
        time.sleep(2)

# 创建 MQTT 客户端并连接
client = create_mqtt_client()
connect_and_subscribe(client)

# 启动模拟线程,模拟每两秒一条消息发布
simulate_thread = threading.Thread(target=simulate_loop)
simulate_thread.daemon = True
simulate_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("中断退出。")
