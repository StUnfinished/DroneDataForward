import os
import re
import time
import logging
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from minio import Minio
from pathlib import Path
from ftplib import FTP

# === 配置区域 ===
# MinIO 配置
MINIO_ENDPOINT = "127.0.0.1:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "images"
MINIO_PREFIX = "images/"

# 本地保存配置
LOCAL_SAVE_ROOT = "./downloaded_images"
LAUNCH_FILE_PATH = "./your.launch"
TARGET_PARAM_NAME = "config/input"
POLL_INTERVAL = 5  # 秒

# MinIO 影像 FTP 上传配置
ENABLE_FTP_UPLOAD = True  # 是否开启FTP传输
FTP_HOST = "192.168.1.100"
FTP_PORT = 21
FTP_USER = "ftpuser"
FTP_PASS = "ftppassword"
FTP_ROOT_IMG_DIR = "/remote_path/store/images"

# 拼接结果 FTP 上传配置
ENABLE_RESULT_FTP_UPLOAD = True  # 是否启用拼接结果FTP上传
STITCH_OUTPUT_ROOT = "./output"  # 拼接结果总文件夹
FTP_ROOT_TIF_DIR = "/remote_path/store/tifs"  # FTP 上传根目录，如 "/upload"（请根据实际情况修改）

LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)
# =================

def setup_logger(logfile_name):
    logger = logging.getLogger("MissionLogger")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(logfile_name)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    return logger

def connect_minio():
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

def extract_info(filename):
    match = re.match(r'DJI_(\d{14})_(\d{4})_V\.JPG', filename)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

def find_all_mission_starts(objects):
    mission_starts = {}
    for obj in objects:
        fname = os.path.basename(obj.object_name)
        ts, idx = extract_info(fname)
        if ts and idx == 1:
            mission_starts[ts] = obj.object_name
    return mission_starts

def get_latest_mission_ts(mission_starts):
    return max(mission_starts.keys()) if mission_starts else None

def filter_objects_by_mission(objects, mission_start_ts):
    result = []
    for obj in objects:
        fname = os.path.basename(obj.object_name)
        ts, _ = extract_info(fname)
        if ts and ts >= mission_start_ts:
            result.append(obj)
    return result

def create_mission_folder(mission_ts):
    date_str = mission_ts[:8]
    counter = 1
    while True:
        base_path = os.path.join(LOCAL_SAVE_ROOT, f"{date_str}_{counter:03d}")
        temp_path = os.path.join(base_path, "temp")
        img_path = os.path.join(base_path, "img")
        if not os.path.exists(base_path):
            os.makedirs(temp_path)
            os.makedirs(img_path)
            return base_path, temp_path, img_path
        counter += 1

def update_launch_file(img_folder_path, logger):
    try:
        tree = ET.parse(LAUNCH_FILE_PATH)
        root = tree.getroot()
        for elem in root.iter("param"):
            if elem.attrib.get("name") == TARGET_PARAM_NAME:
                old_val = elem.attrib.get("value")
                new_val = os.path.abspath(img_folder_path)
                elem.set("value", new_val)
                logger.info(f"[LAUNCH] Updated '{old_val}' → '{new_val}'")
        tree.write(LAUNCH_FILE_PATH)
        logger.info(f"[LAUNCH] File updated: {LAUNCH_FILE_PATH}")
    except Exception as e:
        logger.error(f"[LAUNCH] Failed to update: {e}")

def download_incremental(client, mission_start_ts, objects, temp_folder, img_folder, downloaded_set, logger):
    for obj in sorted(objects, key=lambda x: x.object_name):
        fname = os.path.basename(obj.object_name)
        ts, _ = extract_info(fname)
        if ts and ts >= mission_start_ts and fname not in downloaded_set:
            temp_path = os.path.join(temp_folder, fname)
            final_path = os.path.join(img_folder, fname)
            try:
                client.fget_object(BUCKET_NAME, obj.object_name, temp_path)
                # 确保文件下载完整后再移动
                if os.path.getsize(temp_path) > 0:
                    shutil.move(temp_path, final_path)
                    downloaded_set.add(fname)
                    logger.info(f"[DOWNLOAD] {fname} saved to {final_path}")
                    # 实时FTP上传图片
                    if ENABLE_FTP_UPLOAD:
                        try:
                            upload_single_file_via_ftp(final_path, fname, img_folder, logger)
                        except Exception as ftp_e:
                            logger.error(f"[FTP] 实时上传 {fname} 失败: {ftp_e}")
                else:
                    logger.warning(f"[SKIP] {fname} seems empty. Skipped.")
            except Exception as e:
                logger.error(f"[ERROR] Failed to download {fname}: {e}")

def upload_single_file_via_ftp(local_file_path, filename, img_folder, logger):
    """实时上传单张图片到FTP对应任务目录"""
    task_name = os.path.basename(os.path.dirname(img_folder))
    ftp = FTP()
    ftp.connect(FTP_HOST, FTP_PORT, timeout=10)
    ftp.login(FTP_USER, FTP_PASS)
    remote_task_dir = os.path.join(FTP_ROOT_IMG_DIR, task_name).replace("\\", "/")
    path_parts = remote_task_dir.strip("/").split("/")
    for part in path_parts:
        if part not in ftp.nlst():
            try:
                ftp.mkd(part)
            except Exception:
                pass
        ftp.cwd(part)
    with open(local_file_path, 'rb') as f:
        ftp.storbinary(f"STOR {filename}", f)
        logger.info(f"[FTP] 实时上传: {filename}")
    ftp.quit()

def upload_folder_via_ftp(local_img_folder, task_name, logger):
    if not ENABLE_FTP_UPLOAD:
        logger.info(f"[FTP] FTP上传未启用，跳过 {task_name}")
        return

    try:
        ftp = FTP()
        ftp.connect(FTP_HOST, FTP_PORT, timeout=10)
        ftp.login(FTP_USER, FTP_PASS)
        logger.info(f"[FTP] 已连接 FTP 服务器 {FTP_HOST}")

        # 创建远程目录（如不存在）
        remote_task_dir = os.path.join(FTP_ROOT_IMG_DIR, task_name).replace("\\", "/")
        path_parts = remote_task_dir.strip("/").split("/")
        for part in path_parts:
            if part not in ftp.nlst():
                try:
                    ftp.mkd(part)
                except Exception:
                    pass
            ftp.cwd(part)

        # 上传所有图片
        for filename in sorted(os.listdir(local_img_folder)):
            local_file_path = os.path.join(local_img_folder, filename)
            if os.path.isfile(local_file_path):
                with open(local_file_path, 'rb') as f:
                    ftp.storbinary(f"STOR {filename}", f)
                    logger.info(f"[FTP] 已上传: {filename}")

        ftp.quit()
        logger.info(f"[FTP] 任务 {task_name} 上传完成")
    except Exception as e:
        logger.error(f"[FTP] 上传失败: {e}")

def upload_latest_stitch_result(logger):
    if not ENABLE_RESULT_FTP_UPLOAD:
        logger.info("[RESULT FTP] 拼接结果上传未启用")
        return

    try:
        # 1. 获取 output/ 下最新的拼接结果目录
        subfolders = [f for f in os.listdir(STITCH_OUTPUT_ROOT) if os.path.isdir(os.path.join(STITCH_OUTPUT_ROOT, f))]
        if not subfolders:
            logger.warning("[RESULT FTP] 没有找到拼接结果文件夹")
            return

        latest_subfolder = sorted(subfolders, reverse=True)[0]  # 时间戳文件夹
        base_path = os.path.join(STITCH_OUTPUT_ROOT, latest_subfolder)
        final_result_path = os.path.join(base_path, "mosaicing", "ortho")
        sub_result_path = os.path.join(base_path, "mosaicing", "submaps", "ortho")

        if not os.path.exists(final_result_path) and not os.path.exists(sub_result_path):
            logger.warning(f"[RESULT FTP] 拼接结果路径不存在: {final_result_path} 和 {sub_result_path}")
            return

        # 2. 连接 FTP
        ftp = FTP()
        ftp.connect(FTP_HOST, FTP_PORT, timeout=10)
        ftp.login(FTP_USER, FTP_PASS)

        # 3. 进入 /FTP_ROOT_DIR/ortho/ 子目录
        ftp.cwd(FTP_ROOT_TIF_DIR)
        for subdir in ["ortho", latest_subfolder, "finalmap"]:
            if subdir not in ftp.nlst():
                try:
                    ftp.mkd(subdir)
                except:
                    pass
            ftp.cwd(subdir)

        # 4. 上传 final.tif（总图）
        if os.path.isdir(final_result_path):
            for f in os.listdir(final_result_path):
                if f.lower().endswith(".tif"):
                    local_path = os.path.join(final_result_path, f)
                    with open(local_path, "rb") as file:
                        ftp.storbinary(f"STOR {f}", file)
                        logger.info(f"[RESULT FTP] 上传总图: {f}")

        # 5. 回退到 ortho 目录，创建 submaps 子目录
        ftp.cwd("..")  # 回到最新文件夹
        if "submaps" not in ftp.nlst():
            ftp.mkd("submaps")
        ftp.cwd("submaps")

        # 6. 上传子图结果
        if os.path.isdir(sub_result_path):
            for f in os.listdir(sub_result_path):
                if f.lower().endswith(".tif"):
                    local_path = os.path.join(sub_result_path, f)
                    with open(local_path, "rb") as file:
                        ftp.storbinary(f"STOR {f}", file)
                        logger.info(f"[RESULT FTP] 上传子图: {f}")

        ftp.quit()
        logger.info("[RESULT FTP] 拼接结果上传完成")

    except Exception as e:
        logger.error(f"[RESULT FTP] 上传拼接结果失败: {e}")

def main():
    client = connect_minio()
    logger = setup_logger(os.path.join(LOG_DIR, f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
    logger.info("[INIT] Connected to MinIO")

    downloaded = set()
    current_mission_ts = None
    current_temp_folder = None
    current_img_folder = None

    last_stitch_upload_time = 0
    while True:
        try:
            all_objs = list(client.list_objects(BUCKET_NAME, prefix=MINIO_PREFIX, recursive=True))
            mission_starts = find_all_mission_starts(all_objs)
            latest_ts = get_latest_mission_ts(mission_starts)

            if not latest_ts:
                logger.warning("[SCAN] No '_0001_V.JPG' missions found")
                time.sleep(POLL_INTERVAL)
                continue

            if latest_ts != current_mission_ts:
                current_mission_ts = latest_ts
                base_folder, temp_folder, img_folder = create_mission_folder(current_mission_ts)
                current_temp_folder = temp_folder
                current_img_folder = img_folder
                task_name = os.path.basename(base_folder)
                downloaded.clear()
                update_launch_file(current_img_folder, logger)
                # 首次切换航次时可选：上传已存在的图片文件夹
                # upload_folder_via_ftp(current_img_folder, task_name, logger)
                logger.info(f"[MISSION] Switched to new mission {current_mission_ts}, folder: {base_folder}")

            mission_objs = filter_objects_by_mission(all_objs, current_mission_ts)
            download_incremental(client, current_mission_ts, mission_objs, current_temp_folder, current_img_folder, downloaded, logger)

            # 实时上传拼接结果tif文件
            now = time.time()
            if ENABLE_RESULT_FTP_UPLOAD and now - last_stitch_upload_time > 10:
                try:
                    upload_latest_stitch_result(logger)
                    last_stitch_upload_time = now
                except Exception as e:
                    logger.error(f"[RESULT FTP] 实时上传拼接结果失败: {e}")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("[EXIT] Stopped by user.")
            break
        except Exception as e:
            logger.error(f"[ERROR] {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
