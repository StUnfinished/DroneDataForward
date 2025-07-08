from dataclasses import dataclass
from typing import List

# 无人机飞行状态数据类
@dataclass
class FlightStatus:
    mode_code: int  # 0: 待机, 1: 手动飞行, 2: 自动飞行
    uav_lat: float  # 无人机位置纬度（°）
    uav_lon: float  # 无人机位置经度（°）
    uav_alt: float  # 无人机位置海拔高度（m）
    uav_rel_alt: float  # 无人机位置相对起飞点高度（m）
    uav_speed: float    # 无人机飞行速度（m/s）
    uav_yaw: float      # 无人机偏航角（°）
    uav_pitch: float    # 无人机俯仰角（°）
    uav_roll: float     # 无人机横滚角（°）
    battery_percent: int    # 无人机电池剩余电量百分比（%）
    wind_speed: float       # 当前风速（m/s）


# 载荷状态数据类
# 通用载荷基本信息
@dataclass
class PayloadBase:
    type: int         # 0: 可见光, 1: 热红外, 2: 激光雷达, 3: 四分量仪
    payload_id: str   # 载荷ID
    status: int       # 0: 待机, 1: 运行中

# 相机类载荷（继承基础载荷）
@dataclass
class CameraPayload(PayloadBase):
    cam_roll: float   # 相机横滚角（°）
    cam_yaw: float    # 相机偏航角（°）
    cam_pitch: float  # 相机俯仰角（°）

# 可见光相机载荷
@dataclass
class RGBCameraPayload(CameraPayload):
    zoom: float       # 光学变焦倍数
    # 可扩展其他可见光相机专有字段

# 热红外相机载荷
@dataclass
class ThermalCameraPayload(CameraPayload):
    pass  # 可扩展热红外专有字段

# 激光雷达载荷
@dataclass
class LidarPayload(PayloadBase):
    pass  # 可扩展激光雷达专有字段

# 多光谱相机载荷
@dataclass
class MultispectralPayload(PayloadBase):
    pass  # 可扩展四分量仪专有字段


# 无人机总体状态数据类
@dataclass
class DroneStatus:
    drone_id: str                   # 无人机ID
    timestamp: str                  # 时间戳（ISO8601 格式 UTC 时间）
    flight_status: FlightStatus     # 飞行状态数据
    payloads: List[PayloadBase]     # 载荷状态列表

# 机队数据类
@dataclass
class FleetData:
    fleet_id: str                   # 机队ID
    timestamp: str                  # 时间戳（ISO8601 格式 UTC 时间）
    drones: List[DroneStatus]       # 无人机列表
