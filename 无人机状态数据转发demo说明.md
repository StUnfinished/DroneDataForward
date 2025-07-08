# 无人机状态数据转发 Demo 说明文档

本文档及所附带的Python脚本旨在进行无人机实时飞行状态数据与"中山大学极地"号信息系统的对接显示。其中`drone_simulator_public.py`模拟无人机数据聚合模块发布无人机状态数据，`drone_subscribe.py`展示如何订阅并解析这些数据。信息平台的解析程序可以参照`drone_subscribe.py`脚本进行编写。支持单机和多机两种数据发布模式。


---

## 一、脚本功能与用法

### 1. drone_simulator_public.py

- **功能**：模拟无人机端通过 MQTT 协议定时发布自定义格式的飞行状态数据到指定主题，实现无人机状态数据的模拟上报。支持单机和多机两种模式。
- **用法**：
1. 安装emqx MQTT Broker服务器：下载emqx5.3.2，[链接](https://pan.sysu.edu.cn/link/AA0280380EDB584DA5B54102158EF9691A)。
2. 解压后进入目录，在cmd或powershell执行以下命令启动服务：
        ```sh
        ./bin/emqx start
        ```
     确认服务已启动成功，可以通过访问 http://localhost:18083/ 登录管理界面（默认用户名为 `admin`，密码为`public`）。     
 3. 确保已安装 `paho-mqtt` 库：
     ```sh
     pip install paho-mqtt
     ```
  4. 配置 MQTT Broker 地址、端口、用户名、密码等参数（脚本 `参数配置` 下的变量），默认为本地，在船上实际运行时为局域网其他地址，信息平台服务器不需要安装emqx。
  5. （可选）修改 `NUM_DRONES` 变量设置无人机数量。
  6. 运行脚本：
     ```sh
     python drone_simulator_public.py
     ```
  7. 脚本会模拟无人机信息聚合模块每2秒向 `uav/status/dji_osd` 主题发布一条自定义格式的无人机状态消息，控制台可见发布日志。

### 2. drone_subscribe.py

- **功能**：作为下游订阅端，监听自定义主题，解析收到的无人机状态数据，并以结构化、可读的方式打印展示。支持解析单机和多机数据。
- **用法**：
  1. 配置 MQTT Broker 地址、端口、用户名、密码等参数（脚本底部 `参数配置` 下的变量）。
  2. 运行脚本：
     ```sh
     python drone_subscribe.py
     ```
  3. 脚本会自动订阅 `uav/status/dji_osd` 主题，收到消息后解析并打印无人机飞行状态与载荷状态详细信息。对于多机数据，会显示机队整体信息和每架无人机的详细状态。

---
## 二、自定义MQTT主题结构示例及字段说明（uav/status/dji_osd）

### 1. 单机数据结构示例：
```json
{
  "drone_id": "DJI_Matrice_001",
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
```

### 2. 多机数据结构示例：
```json
{
  "fleet_id": "DJI_FLEET_001",
  "timestamp": "2025-06-23T10:04:32.960000Z",
  "drones": [
    {
      "drone_id": "DJI_Matrice_4E_001",
      // ... 单机数据结构 ...
    },
    {
      "drone_id": "DJI_Matrice_4E_002",
      // ... 单机数据结构 ...
    },
    {
      "drone_id": "DJI_Matrice_4E_003",
      // ... 单机数据结构 ...
    }
  ]
}
```

## 三、自定义MQTT主题字段说明

### 1. 单机数据结构顶层字段

| 字段名        | 类型                 | 说明                         |
|---------------|----------------------|------------------------------|
| drone_id      | str                  | 无人机ID                     |
| timestamp     | str                  | 时间戳（ISO8601 格式 UTC）   |
| flight_status | object               | 飞行状态数据                 |
| payloads      | array                | 载荷状态列表                 |

### 2. 多机数据结构顶层字段

当主题消息为多机（机队）数据时，结构如下：

| 字段名        | 类型                 | 说明                         |
|---------------|----------------------|------------------------------|
| fleet_id      | str                  | 机队ID                       |
| timestamp     | str                  | 时间戳（ISO8601 格式 UTC）   |
| drones        | array                | 无人机状态对象列表，每项结构同单机数据结构 |

> 其中 `drones` 数组中的每个元素结构与上方“单机数据结构顶层字段”一致。

### 3. flight_status 对象

| 字段名           | 类型    | 说明                         |
|------------------|---------|------------------------------|
| mode_code        | int     | 飞行模式（0: 待机, 1: 手动飞行, 2: 自动飞行） |
| uav_lat          | float   | 无人机位置纬度（°）           |
| uav_lon          | float   | 无人机位置经度（°）           |
| uav_alt          | float   | 无人机位置海拔高度（m）       |
| uav_rel_alt      | float   | 无人机相对起飞点高度（m）     |
| uav_speed        | float   | 无人机飞行速度（m/s）         |
| uav_yaw          | float   | 无人机偏航角（°）             |
| uav_pitch        | float   | 无人机俯仰角（°）             |
| uav_roll         | float   | 无人机横滚角（°）             |
| battery_percent  | int     | 无人机电池剩余电量百分比（%） |
| wind_speed       | float   | 当前风速（m/s）               |

### 4. payloads 数组

每个元素为一个载荷对象，结构如下：

| 字段名      | 类型   | 说明                                 |
|-------------|--------|--------------------------------------|
| type        | int    | 载荷类型（0: 可见光, 1: 热红外, 2: 激光雷达, 3: 四分量仪） |
| payload_id  | str    | 载荷ID                               |
| status      | int    | 载荷状态（0: 待机, 1: 运行中）       |
| parameters  | object | 载荷参数，结构随载荷类型不同         |

#### 4.1 可见光相机（type=0）parameters 字段

| 字段名    | 类型   | 说明           |
|-----------|--------|----------------|
| cam_roll  | float  | 相机横滚角（°）|
| cam_pitch | float  | 相机俯仰角（°）|
| cam_yaw   | float  | 相机偏航角（°）|
| zoom      | float  | 光学变焦倍数   |

#### 4.2 热红外相机（type=1）parameters 字段

| 字段名    | 类型   | 说明           |
|-----------|--------|----------------|
| cam_roll  | float  | 相机横滚角（°）|
| cam_pitch | float  | 相机俯仰角（°）|
| cam_yaw   | float  | 相机偏航角（°）|

#### 4.3 激光雷达/多光谱相机（type=2/3）parameters 字段

- 目前为空对象，预留扩


## 四、注意事项
- 自定义 MQTT 主题消息可根据实际需求扩展自定义主题结构和字段内容。
- 订阅端可根据实际需求扩展数据解析与处理逻辑。
