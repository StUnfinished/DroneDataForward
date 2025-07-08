# MinIO无人机影像自动下载与FTP同步脚本说明

## 功能简介
本脚本实现了以下功能：

1. **自动从MinIO服务器实时下载最新航次的无人机影像**，并按航次自动分文件夹保存到本地。
2. **实时将下载的影像图片通过FTP同步上传到指定远程服务器**，每张图片下载后立即上传。
3. **自动检测本地拼接结果（tif文件）并定时通过FTP上传到指定目录**，支持总图和子图的自动同步。
4. **自动更新指定的launch文件参数**，同步最新影像文件夹路径。

## 目录结构
- `downloaded_images/`：本地影像保存根目录，按航次自动新建子文件夹。
- `output/`：拼接结果根目录，按任务自动新建子文件夹。
- `logs/`：日志文件目录。
- `your.launch`：需自动更新的launch配置文件。

## 主要配置项
在脚本开头的“配置区域”可自定义：
- MinIO服务器地址、账号、桶名等
- 本地保存路径
- FTP服务器地址、账号、根目录
- 拼接结果本地与FTP目录
- 是否启用FTP自动上传

## 运行环境依赖
- Python 3.7+
- minio
- ftplib（标准库）
- 其他标准库：os、re、time、logging、shutil、xml.etree.ElementTree、datetime、pathlib

安装依赖：
```bash
pip install minio
```

## 用法说明
1. **配置参数**：根据实际情况修改脚本顶部的MinIO、FTP、路径等参数。
2. **准备launch文件**：确保`your.launch`存在，且有`config/input`参数。
3. **运行脚本**：
```bash
python minio_downloader.py
```
4. **自动流程**：
   - 程序会定时扫描MinIO桶，发现新航次（以文件名`_0001_V.JPG`为起点）自动新建本地文件夹并下载该航次所有图片。
   - 每张图片下载后立即通过FTP上传到远程服务器对应任务目录。
   - 每隔10秒自动检测`output/`下最新拼接结果（tif文件），并同步上传到FTP指定目录。
   - 每次切换新航次时自动更新launch文件参数。

## 关键函数说明
- `download_incremental`：增量下载影像并实时FTP上传。
- `upload_single_file_via_ftp`：单张图片实时FTP上传。
- `upload_folder_via_ftp`：批量上传整个文件夹（在传输已有图片的本地文件夹时可选）。
- `upload_latest_stitch_result`：定时上传拼接结果tif文件。
- `update_launch_file`：自动更新launch文件参数。

## 注意事项
- FTP目录会自动递归创建，无需手动干预。
- 若FTP/MinIO连接异常，日志会详细记录。
- 支持断点续传（已下载图片不会重复下载/上传）。
- 拼接结果上传频率可通过代码调整（默认10秒检测一次）。

## 常见问题
- **MinIO/FTP连接失败**：请检查网络、防火墙、账号密码、端口等。
- 在 WSL2 中连接 MinIO 时，使用 `mc alias list` 命令查看 minio client 使用的网络配置，默认使用本地IP：`"127.0.0.1:9000"` 进行配置即可。
- **launch文件未更新**：请确认参数名与路径配置正确。
- **拼接结果未上传**：请确认output目录结构与配置一致。

---
如需定制功能或遇到问题，请联系开发者。
