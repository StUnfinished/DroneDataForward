import paho.mqtt.client as mqtt
import json
from dataclasses import dataclass
from typing import Dict, Any, List
from drone_dataclasses import DroneStatus, FlightStatus, RGBCameraPayload, LidarPayload, MultispectralPayload, ThermalCameraPayload, PayloadBase, FleetData

# 主题消息解析函数
# 载荷状态信息解析函数
def parse_payload(device: Dict[str, Any]) -> PayloadBase:
    base_fields = {
        "type": device.get("type"),
        "payload_id": device.get("payload_id"),
        "status": device.get("status")
    }

    params = device.get("parameters", {})
    ptype = base_fields["type"]

    if ptype == 0:  # 可见光相机
        return RGBCameraPayload(**base_fields,
                             cam_roll=params.get("cam_roll", 0.0),
                             cam_pitch=params.get("cam_pitch", 0.0),
                             cam_yaw=params.get("cam_yaw", 0.0),
                             zoom=params.get("zoom", 0.0))
    elif ptype == 1:  # 热红外相机
        return ThermalCameraPayload(**base_fields,
                                    cam_roll=params.get("cam_roll", 0.0),
                                    cam_pitch=params.get("cam_pitch", 0.0),
                                    cam_yaw=params.get("cam_yaw", 0.0))
    elif ptype == 2:
        return LidarPayload(**base_fields)
    elif ptype == 3:
        return MultispectralPayload(**base_fields)
    else:
        return PayloadBase(**base_fields)

# 无人机飞行状态信息解析函数
def parse_drone_status(data: Dict[str, Any]) -> DroneStatus:
    flight_status_data = data.get("flight_status", {})
    flight_status = FlightStatus(
        mode_code=flight_status_data.get("mode_code", -1),
        uav_lat=flight_status_data.get("uav_lat", 0.0),
        uav_lon=flight_status_data.get("uav_lon", 0.0),
        uav_alt=flight_status_data.get("uav_alt", 0.0),
        uav_rel_alt=flight_status_data.get("uav_rel_alt", 0.0),
        uav_speed=flight_status_data.get("uav_speed", 0.0),
        uav_yaw=flight_status_data.get("uav_yaw", 0.0),
        uav_pitch=flight_status_data.get("uav_pitch", 0.0),
        uav_roll=flight_status_data.get("uav_roll", 0.0),
        battery_percent=flight_status_data.get("battery_percent", 0),
        wind_speed=flight_status_data.get("wind_speed", 0.0),
    )

    payloads_data = data.get("payloads", [])
    payloads = [parse_payload(p) for p in payloads_data]

    return DroneStatus(
        drone_id=data.get("drone_id", ""),
        timestamp=data.get("timestamp", ""),
        flight_status=flight_status,
        payloads=payloads
    )

# 机队数据解析函数
def parse_fleet_data(data: Dict[str, Any]) -> FleetData:
    drones_data = data.get("drones", [])
    drones = [parse_drone_status(d) for d in drones_data]
    
    return FleetData(
        fleet_id=data.get("fleet_id", ""),
        timestamp=data.get("timestamp", ""),
        drones=drones
    )

# 主解析函数
def payload_parser(data: Dict[str, Any]):
    # 判断是否为机队数据
    if "fleet_id" in data:
        fleet_data = parse_fleet_data(data)
        print(f"\n=== 机队状态信息 ===")
        print(f"机队ID：{fleet_data.fleet_id}")
        print(f"时间戳：{fleet_data.timestamp}")
        print(f"机队中无人机数量：{len(fleet_data.drones)}")
        print("========================")
        
        # 遍历并显示每台无人机的信息
        for drone in fleet_data.drones:
            print("\n--- 无人机详细信息 ---")
            display_drone_status(drone)
    else:
        # 单机数据处理
        drone_status = parse_drone_status(data)
        display_drone_status(drone_status)

def display_drone_status(drone_status: DroneStatus):
    fs = drone_status.flight_status
    mode_map = {0: "待机", 1: "手动飞行", 2: "自动飞行"}
    flight_mode = mode_map.get(fs.mode_code, "未知模式")

    print(f"无人机ID：{drone_status.drone_id}，当前飞行模式：{flight_mode}")
    print(f"时间戳：{drone_status.timestamp}")
    print(f"位置：纬度={fs.uav_lat}°，经度={fs.uav_lon}°，海拔高度={fs.uav_alt}m，相对起飞点高度={fs.uav_rel_alt}m")
    print(f"姿态：偏航角={fs.uav_yaw}°，俯仰角={fs.uav_pitch}°，横滚角={fs.uav_roll}°")
    print(f"风速：{fs.wind_speed} m/s，电池剩余电量：{fs.battery_percent}%，飞行速度: {fs.uav_speed} m/s")

    type_map = {0: "可见光相机", 1: "热红外相机", 2: "激光雷达", 3: "四分量仪"}

    print("-- 载荷信息 --")
    for payload in drone_status.payloads:
        dtype_str = type_map.get(payload.type, "未知载荷")
        status_str = "运行中" if payload.status == 1 else "待机"

        print(f"-载荷类型-：{dtype_str}")
        print(f"载荷ID：{payload.payload_id}")
        print(f"载荷状态：{status_str}")

        if isinstance(payload, RGBCameraPayload):
            print(f"相机变焦倍数：{payload.zoom}")
            print(f"相机姿态：横滚角={payload.cam_roll}°，俯仰角={payload.cam_pitch}°，偏航角={payload.cam_yaw}°")

        if isinstance(payload, ThermalCameraPayload):
            print(f"相机姿态：横滚角={payload.cam_roll}°，俯仰角={payload.cam_pitch}°，偏航角={payload.cam_yaw}°")

        if isinstance(payload, LidarPayload) or isinstance(payload, MultispectralPayload):
            print("（该载荷无详细参数）")


# 接收计数
message_count = 0
# 当连接到 MQTT Broker 成功时回调
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        client.subscribe(MQTT_TOPIC_SUB)
        print("已连接到 MQTT Broker，订阅主题：", MQTT_TOPIC_SUB)
    else:
        print("连接失败")

# 当收到订阅主题的消息时回调
def on_message(client, userdata, msg):
    global message_count
    message_count += 1

    try:
        json_data = json.loads(msg.payload.decode())
        print(f"\n ---收到第{message_count}条数据---")
        payload_parser(json_data)
    except Exception as e:
        print("解析失败:", e)

# 创建并配置一个 MQTT 客户端实例
def create_mqtt_client(on_message_callback=on_message) -> mqtt.Client:
    client = mqtt.Client()
    client.username_pw_set(username=username, password=password)    # 若使用本地MQTT Broker，默认不需要用户名密码，此行可省略
    client.on_connect = on_connect
    client.on_message = on_message_callback
    return client

# # 参数配置
# 配置 MQTT 参数
MQTT_BROKER = "127.0.0.1"       # MQTT broker 主机地址
MQTT_PORT = 1883            # MQTT port 端口号
MQTT_TOPIC_SUB = "uav/status/uav_osd"           # 要订阅的主题

# 若使用云端MQTT Broker，一般需要用户名和密码
username = "MQTT2"      # MQTT 用户名
password = "123456"     # MQTT 用户密码

client = create_mqtt_client()

# 连接到 Broker 并启动循环
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()

