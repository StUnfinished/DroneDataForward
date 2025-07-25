# 实现DJI视频流回传功能
参考链接：https://blog.csdn.net/m0_62317155/article/details/145038305
## 1. 搭建流媒体服务
参考链接：https://blog.csdn.net/m0_62317155/article/details/143662331
### 安装mediamtx  
- 安装mediamtx可以到官网地址：https://github.com/bluenviron/mediamtx/releases， 例如下`mediamtx_v1.9.3_windows_amd64` 这个版本；
- 下载解压，打开文件夹，修改 `mediamtx.yml` 配置文件中的端口号；
- 之后双击运行 `mediamtx.exe` 即可。

## 2. 修改上云API代码
### 修改前端代码
- 修改 `...\Cloud-API-Demo-Web\src\api\http\config.ts` 中的rtmp流媒体服务地址：  
```
// livestreaming
 
  rtmpURL: 'rtmp://192.168.5.148:1935/live/', // Example: 'rtmp://192.168.1.1/live/'
```
### 修改后端代码
- 修改 `...\DJI-Cloud-API-Demo\sample\src\main\resources\application.yml` 中的rtmp流媒体服务地址：
```
rtmp:
      url: rtmp://192.168.5.148:1935/live/  # Example: 'rtmp://192.168.1.1/live/'
```

## 3. 重启前后端，在遥控器开启rtmp直播功能
- 开启直播推流前，需要运行 `mediamtx.exe` ，目前该程序的启动已加入到一键启动脚本中，启动后会在弹出的终端窗口中显示 mediamtx 的运行状态信息，包括**推流地址**、**端口**等。
- 进入遥控器上云API界面，点击 `Livestream Manually` ，在 `Select Video Publish Mode` 中选择 `video-demand-aux-manual` ，在 `Select Livestream Type` 中选择 `RTMP` ，最后点击 `Play`。
- 如遥控器显示 `Living` ,则说明正在直播中，此时便可以把遥控器界面给出的地址复制到 VLC 播放器中进行播放（**步骤：打开VLC播放器—菜单栏—媒体—打开网络串流—输入直播地址**），可以在无人机飞行界面和mediamtx 运行终端中查看直播推流状态。

## 注意
- rtmp直播流的地址 `rtmp://root:root@{遥控器ip}:8554/streaming/live/...` 后的部分是开启直播推流时的时间戳，每次重新开启直播后刷新，只要不重新点击 `Play` 开启直播，VLC中输入的直播地址就不需要修改。
- 如遇到第一次在VLC播放器中输入rtmp直播地址后提示无法打开地址的情况，原因可能是rtmp存在直播延迟，需要在遥控器飞行界面检查无人机是否正在直播，并等待一分钟后重新在VLC开启播放。

