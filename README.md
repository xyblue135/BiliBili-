# 示例
![](images/Pasted%20image%2020250605124429.png)
# 使用编译release版本需要什么
无→开箱即用
哔哩哔哩客户端
# 使用源码需要什么
## python3版本
## pip的相应扩展
pyqt6
```
import os
import shutil
import configparser
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QScrollArea, QGridLayout, QFrame, QHBoxLayout,
    QMessageBox, QProgressBar
)
from PyQt6.QtGui import QPixmap, QCursor, QIcon, QFont, QColor
from PyQt6.QtCore import Qt, QSize, QTimer
import sys
```
## ffmpeg
https://ffmpeg.org/
# 使用说明

1. 解压压缩包→内附三个按钮→📂设置目录【设置哔哩哔哩缓存所存储的位置 示例:C:/Users/用户名/Videos/bilibili】
2. 点击第二个按钮⚙️打开配置→绑定ffmpeg的位置【需绑定ffmpeg.exe 示例:D:\test\哔哩哔哩视频下载该工具\ffmpeg-N-105436-g98cef1ebbe-win64-gpl-shared\ffmpeg.exe】
3. 缓存b站视频,等待下载完成 点击🚀开始合并
4. 点击下方视频预览可以跳到目标文件夹.
5. 为避免滥用,如需将所有视频输出到桌面,请自行编写递归复制脚本

![](images/GIF%202025-6-5%2012-21-03%20(1)%201.gif)






