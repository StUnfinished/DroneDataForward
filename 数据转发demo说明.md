# 大疆无人机 MQTT 数据转发与解析 Demo 说明文档

本项目包含两个主要脚本：`drone_public.py`（数据转发/模拟发布端）和 `drone_subscribe.py`（数据解析/订阅端）。适用于大疆无人机云API数据链路的模拟、转发与解析演示。

---

## 一、脚本功能

### 1. drone_public.py
- **功能**：模拟无人机端通过 MQTT 协议定时发布原始飞行状态数据，并将其转换为自定义格式后转发到另一个 MQTT 主题。

### 2. drone_subscribe.py
- **功能**：作为下游订阅端，监听自定义主题，解析转发后的无人机状态数据，并以结构化、可读的方式打印展示。

---

## 二、输入输出

### drone_public.py

- **输入**：
  - MQTT 原始主题（如 `thing/product/{device_sn}/osd`），本脚本内置模拟数据自动发布，可切换至接入真实无人机主题消息。
- **输出**：
  - MQTT 转发主题（如 `uav/status/dji_osd`），发布自定义格式的无人机状态数据至自定义主题。

### drone_subscribe.py

- **输入**：
  - 订阅自定义主题（如 `uav/status/dji_osd`），接收转发后的无人机状态数据。
- **输出**：
  - 控制台打印结构化的无人机飞行状态、载荷状态等详细信息。

---

## 三、运行逻辑

### drone_public.py

1. **模拟原始消息**：内置一条真实格式的无人机原始状态消息，每2s通过 `simulate_raw_message` 向原始主题发布，模拟真实无人机消息发布。
2. **MQTT 客户端连接**：使用 `paho.mqtt.client` 连接本地或云端 MQTT Broker，支持用户名密码。
3. **消息监听与转发**：订阅原始主题，收到消息后调用 `convert_dji_to_custom` 转换格式，并发布到自定义主题。
4. **数据结构转换**：提取飞行状态、载荷状态等关键信息，转换为自定义 JSON 结构。

### drone_subscribe.py

1. **MQTT 客户端连接**：连接到 MQTT Broker，订阅自定义主题。
2. **消息接收与解析**：收到消息后，调用 `payload_parser` 解析数据，映射为结构化对象。
3. **信息展示**：将飞行状态、载荷状态等信息以可读格式打印到控制台。

---

## 四、主要函数说明

### drone_public.py

- `simulate_raw_message(client)`：模拟无人机端发布一条原始状态消息。
- `convert_dji_to_custom(data, drone_id)`：将原始 DJI 消息转换为自定义格式。
- `on_connect(client, userdata, flags, reason_code, properties)`：MQTT 连接回调，自动订阅原始主题。
- `on_message(client, userdata, msg)`：消息回调，处理并转发数据。
- `publish_message(client, topic, message)`：发布消息到自定义主题。

### drone_subscribe.py

- `parse_payload(device)`：解析单个载荷状态。
- `parse_drone_status(data)`：解析无人机飞行状态及所有载荷状态。
- `payload_parser(data)`：主解析函数，打印无人机状态和载荷信息。
- `on_connect(client, userdata, flags, reason_code, properties)`：MQTT 连接回调，自动订阅主题。
- `on_message(client, userdata, msg)`：消息回调，解析并展示数据。

---

## 五、使用方法

### 1. 安装依赖

```sh
pip install paho-mqtt
```
### 2. 配置参数

- 在两个脚本底部可配置 MQTT Broker 地址、端口、用户名、密码、MQTT 主题、无人机编号等参数。
### 3. 启动模拟发布端

在项目文件夹下的终端输入：

```sh
python ./drone_public.py
```
- 控制台会打印模拟发布和转发后的消息内容。

### 4. 启动订阅解析端

在项目文件夹下的另一个终端输入：

```sh
python ./drone_subscribe.py
```
- 控制台会打印解析后的无人机状态和载荷详细信息。

### 5. 主题说明

- 发布主题（模拟无人机原始数据）：`thing/product/{device_sn}/osd`，其中`"device_sn"`为无人机序列号。
- 转发主题（自定义格式数据）：`uav/status/dji_osd`。

## 六、注意事项

- 若连接云端 MQTT Broker，请确保用户名、密码正确。
- 若需对接真实无人机数据，只需将 `simulate_raw_message` 替换为实际订阅主题接收的数据接入即可。
- 本脚本默认每2秒模拟发布一次消息，若对接真实无人机发布的主题消息，可将脚本末尾的2s循环功能释掉。
- 订阅端可根据实际业务需求扩展数据解析和处理逻辑。

## 附录 A 自定义MQTT主题与原始无人机主题结构示例

## 原始主题（thing/product/{device_sn}/osd）
**示例结构：**
```json
{
  "bid": "00000000-0000-0000-0000-000000000000",
  "data": {
    "66-0-0": {
      "gimbal_pitch": 0,
      "gimbal_roll": 0,
      "gimbal_yaw": -72.5,
      "payload_index": "66-0-0",
      "zoom_factor": 0.56782334384858046
    },
    "activation_time": 1698260070,
    "attitude_head": -72.6,
    "attitude_pitch": 4.4,
    "attitude_roll": 0.2,
    "battery": {
      "batteries": [
        {
          "capacity_percent": 24,
          "firmware_version": "08.75.02.23",
          "high_voltage_storage_days": 0,
          "index": 0,
          "loop_times": 10,
          "sn": "4ERPLBQEA2KSCR",
          "sub_type": 0,
          "temperature": 39.2,
          "type": 0,
          "voltage": 14932
        }
      ],
      "capacity_percent": 24,
      "landing_power": 0,
      "remain_flight_time": 0,
      "return_home_power": 0
    },
    "cameras": [
      {
        "camera_mode": 0,
        "liveview_world_region": {
          "bottom": 0.54841738939285278,
          "left": 0.431539535522461,
          "right": 0.56274276971817,
          "top": 0.41614934802055359
        },
        "payload_index": "66-0-0",
        "photo_state": 0,
        "record_time": 0,
        "recording_state": 0,
        "remain_photo_num": 5309,
        "remain_record_duration": 0,
        "wide_calibrate_farthest_focus_value": 26,
        "wide_calibrate_nearest_focus_value": 75,
        "wide_exposure_mode": 1,
        "wide_exposure_value": 16,
        "wide_focus_mode": 0,
        "wide_focus_state": 0,
        "wide_focus_value": 26,
        "wide_iso": 5,
        "wide_max_focus_value": 75,
        "wide_min_focus_value": 26,
        "wide_shutter_speed": 22,
        "zoom_calibrate_farthest_focus_value": 26,
        "zoom_calibrate_nearest_focus_value": 75,
        "zoom_exposure_mode": 1,
        "zoom_exposure_value": 16,
        "zoom_factor": 7,
        "zoom_focus_mode": 0,
        "zoom_focus_state": 0,
        "zoom_focus_value": 26,
        "zoom_iso": 5,
        "zoom_max_focus_value": 75,
        "zoom_min_focus_value": 26,
        "zoom_shutter_speed": 22
      }
    ],
    "distance_limit_status": {
      "distance_limit": 3000,
      "is_near_distance_limit": 0,
      "state": 1
    },
    "elevation": 20.0,
    "exit_wayline_when_rc_lost": 0,
    "firmware_version": "14.01.0002",
    "gear": 1,
    "height": 87.0712203979492,
    "height_limit": 0,
    "home_distance": 0,
    "horizontal_speed": 10.5,
    "is_near_height_limit": 0,
    "latitude": 22.123456,
    "longitude": 113.654321,
    "maintain_status": {
      "maintain_status_array": [
        {
          "last_maintain_flight_sorties": 0,
          "last_maintain_flight_time": 0,
          "last_maintain_time": 0,
          "last_maintain_type": 1,
          "state": 0
        },
        {
          "last_maintain_flight_sorties": 0,
          "last_maintain_flight_time": 0,
          "last_maintain_time": 0,
          "last_maintain_type": 2,
          "state": 0
        },
        {
          "last_maintain_flight_sorties": 0,
          "last_maintain_flight_time": 0,
          "last_maintain_time": 0,
          "last_maintain_type": 3,
          "state": 0
        }
      ]
    },
    "mode_code": 0,
    "night_lights_state": 0,
    "obstacle_avoidance": {
      "downside": 1,
      "horizon": 1,
      "upside": 0
    },
    "position_state": {
      "gps_number": 0,
      "is_fixed": 0,
      "quality": 0,
      "rtk_number": 0
    },
    "rc_lost_action": 2,
    "rth_altitude": 200,
    "storage": {
      "total": 60082000,
      "used": 5656000
    },
    "total_flight_distance": 404167.679246531,
    "total_flight_sorties": 0,
    "total_flight_time": 0,
    "track_id": "",
    "vertical_speed": 0,
    "wind_direction": 0,
    "wind_speed": 1.6
  },
  "tid": "00000000-0000-0000-0000-000000000000",
  "timestamp": 1750673072960,
  "gateway": "5YSZL7L0032SVP"
}
```
## 自定义主题（uav/status/dji_osd）
**示例结构：**
```json
{
  "drone_id": "DJI_Matrice_001",
  "timestamp": "2025-06-23T10:04:32.960000Z",
  "flight_status": {
    "mode_code": 1,
    "uav_lat": 22.123456,
    "uav_lon": 113.654321,
    "uav_alt": 87.0712203979492,
    "uav_rel_alt": 20.0,
    "uav_speed": 10.5,
    "uav_yaw": -72.6,
    "uav_pitch": 4.4,
    "uav_roll": 0.2,
    "battery_percent": 24,
    "wind_speed": 1.6
  },
  "payloads": [
    {
      "type": 0,
      "payload_id": "CAM_001",
      "status": 0,
      "parameters": {
      "cam_roll": 0,
      "cam_pitch": 0,
      "cam_yaw": -72.5,
      "zoom": 7
      }
    },
    {
      "type": 1,
      "payload_id": "THERM_001",
      "status": 0,
      "parameters": {
        "cam_roll": 0,
        "cam_pitch": 0,
        "cam_yaw": -72.5
      }
    },
    {
      "type": 2,
      "payload_id": "LIDAR_001",
      "status": 1,
      "parameters": {}
    },
    {
      "type": 3,
      "payload_id": "MS_001",
      "status": 0,
      "parameters": {}
    }
  ]
}
```
# 附录 B 自定义MQTT主题字段介绍
## 自定义MQTT主题数据结构体(含字段解释)
```python
#  无人机飞行状态数据类
@dataclass
class FlightStatus:
    mode_code: int  # 0: 待机, 1: 手动飞行, 2: 自动飞行
    uav_lat: float  # 无人机位置纬度（°）
    uav_lon: float  # 无人机位置经度（°）
    uav_alt: float  # 无人机位置海拔高度（m）
    uav_rel_alt: float  # 无人机位置相对起飞点高度（m）
    uav_speed: float    # 无人机飞行速度（m/s）
    uav_yaw: float  # 无人机偏航角（°）
    uav_pitch: float    # 无人机俯仰角（°）
    uav_roll: float  # 无人机横滚角（°）
    battery_percent: int    # 无人机电池剩余电量百分比（%）
    wind_speed: float   # 当前风速（m/s）

#  载荷状态数据类
#  载荷基本信息
@dataclass
class PayloadBase:
    type: int  # 0: 可见光, 1: 热红外, 2: 激光雷达, 3: 四分量仪
    payload_id: str  # 载荷ID
    status: int  # 0: 待机, 1: 运行中

#  成像载荷（可见光相机和热红外相机）共有信息
@dataclass
class CameraPayload(PayloadBase):
    cam_roll: float  # 相机横滚角（°）
    cam_yaw: float  # 相机偏航角（°）
    cam_pitch: float    # 相机俯仰角（°）

# 可见光相机专有字段
@dataclass
class RGBCameraPayload(CameraPayload):
    zoom: float  # 光学变焦倍数

#  热红外相机扩展字段
@dataclass
class ThermalCameraPayload(CameraPayload):
    pass  # 可扩展激光雷达专有字段

#  激光雷达基本信息
@dataclass
class LidarPayload(PayloadBase):
    pass  # 可扩展激光雷达专有字段

#  四分量仪基本信息
@dataclass
class MultispectralPayload(PayloadBase):
    pass  # 可扩展四分量仪专有字段

# 无人机总状态
@dataclass
class DroneStatus:
    drone_id: str   # 无人机ID
    timestamp: str  # 时间戳(ISO8601 格式 UTC 时间)
    flight_status: FlightStatus  # 无人机飞行状态数据段
    payloads: List[PayloadBase]  # 载荷状态数据段
```
## 自定义主题与原始主题字段映射关系
### 字段映射表
| 自定义主题字段                | 原始主题字段（路径）                              | 说明                               |
|-----------------------------|--------------------------------------------------|------------------------------------|
| `drone_id`                  | `drone_id`（脚本参数）                           | 无人机编号                         |
| `timestamp`                 | `timestamp`                                     | 毫秒时间戳转 ISO8601 UTC 时间格式 |
| `flight_status.mode_code`  | `data.mode_code`                                | 飞行模式（需自定义映射）           |
| `flight_status.uav_lat`    | `data.latitude`                                 | 纬度                               |
| `flight_status.uav_lon`    | `data.longitude`                                | 经度                               |
| `flight_status.uav_alt`    | `data.height`                                   | 海拔高度                           |
| `flight_status.uav_rel_alt`| `data.elevation`                                | 相对起飞点高度                     |
| `flight_status.uav_speed`  | `data.horizontal_speed`                         | 水平速度                           |
| `flight_status.uav_yaw`    | `data.attitude_head`                            | 偏航角                             |
| `flight_status.uav_pitch`  | `data.attitude_pitch`                           | 俯仰角                             |
| `flight_status.uav_roll`   | `data.attitude_roll`                            | 横滚角                             |
| `flight_status.battery_percent` | `data.battery.capacity_percent`            | 电池剩余百分比                     |
| `flight_status.wind_speed` | `data.wind_speed`                               | 风速                               |
| `payloads[].type`          | `data.cameras[].type`                 | 载荷类型（0: 可见光等）           |
| `payloads[].payload_id`    | `data.cameras[].payload_index`          | 载荷 ID                            |
| `payloads[].status`        | `data.cameras[].recording_state`              | 载荷工作状态（自定义映射）         |
| `payloads[].parameters.cam_*` | `data["66-0-0"].gimbal_*`                    | 相机姿态                           |
| `payloads[].parameters.zoom`  | `data.cameras[].zoom_factor`                  | 变焦倍数                           |
### 映射逻辑说明
- 载荷类型、状态等字段根据实际业务需求和原始数据内容进行自定义映射。
- 若有多种载荷（如热红外、激光雷达等），可在 `payloads` 数组中扩展。
- **时间戳**：原始为毫秒时间戳，映射后转为 ISO8601 格式（UTC）。
- **飞行模式**：原始 `mode_code` 需与自定义模式码映射（映射为：0=待机，1=手动，2=自动）。
- **载荷信息**：根据 `cameras`、`66-0-0` 等字段组合，填充自定义载荷结构。
- **扩展性**：如有多种载荷类型，可在 `payloads` 数组中增加对应类型，在`parameters`数据块添加相关参数。
##
如需扩展字段或调整映射，请在 `convert_dji_to_custom`（`drone_public.py` 转发端）和 `parse_payload`（`drone_subscribe` 订阅端）中同步修改。
