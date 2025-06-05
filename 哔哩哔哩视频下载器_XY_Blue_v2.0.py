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
from datetime import datetime

STYLE_SHEET = """
QMainWindow {
    background-color: #f0f4f8;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 14px;
    min-width: 100px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #1f6fb3;
}

QScrollArea {
    border: 1px solid #d6e4f0;
    background-color: white;
    border-radius: 4px;
}

QFrame {
    background-color: white;
    border: 1px solid #e0e8f0;
    border-radius: 4px;
}

QLabel {
    color: #2c3e50;
    font-size: 13px;
}
"""

def get_config(config_path='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    video_dir = config.get('settings', 'video_dir', fallback=None)
    ffmpeg_path = config.get('settings', 'ffmpeg_path', fallback='ffmpeg')
    return video_dir, ffmpeg_path

def copy_and_rename_m4s(directory):
    for root, _, files in os.walk(directory):
        if '1.m4s' in files and '2.m4s' in files:
            print(f"目录 {root} 已有 1.m4s 和 2.m4s，跳过。")
            continue

        m4s_files = [f for f in files if f.endswith('.m4s') and f not in ('1.m4s', '2.m4s')]
        
        # 按照文件创建时间排序
        m4s_files = sorted(
            m4s_files,
            key=lambda f: os.path.getctime(os.path.join(root, f))
        )[:2]

        if len(m4s_files) == 0:
            print(f"目录 {root} 没有找到可处理的 .m4s 文件，跳过。")
            continue

        for index, old_name in enumerate(m4s_files, start=1):
            old_path = os.path.join(root, old_name)
            new_name = f"{index}.m4s"
            new_path = os.path.join(root, new_name)

            if os.path.exists(new_path):
                os.remove(new_path)

            shutil.copy2(old_path, new_path)
            print(f"复制 {old_name} -> {new_name} 于目录 {root}")

def delete_first_9_bytes(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(('1.m4s', '2.m4s')) and 'delete8' not in filename:
                original_path = os.path.join(root, filename)
                new_filename = filename.replace('.m4s', '_delete8.m4s')
                new_path = os.path.join(root, new_filename)

                if os.path.exists(new_path):
                    print(f"跳过已存在的文件：{new_path}")
                    continue

                try:
                    shutil.copy2(original_path, new_path)
                    with open(new_path, 'r+b') as f:
                        content = f.read()
                        f.seek(0)
                        f.truncate()
                        f.write(content[9:])
                    print(f"成功复制并处理：{new_path}")
                except Exception as e:
                    print(f"处理文件时出错：{original_path}")
                    print(e)

def merge_m4s_to_mp4(base_dir, ffmpeg_path, progress_callback=None):
    # 获取所有文件夹并按创建时间排序（新视频在前）
    folders = [(os.path.getctime(os.path.join(base_dir, f)), f) 
              for f in os.listdir(base_dir) 
              if os.path.isdir(os.path.join(base_dir, f))]
    folders.sort(key=lambda x: x[0], reverse=True)  # 按创建时间倒序排序
    
    total = len(folders)
    
    for i, (ctime, folder_name) in enumerate(folders, start=1):
        folder_path = os.path.join(base_dir, folder_name)
        m4s1 = os.path.join(folder_path, "1_delete8.m4s")
        m4s2 = os.path.join(folder_path, "2_delete8.m4s")
        output_file = os.path.join(folder_path, f"{folder_name}.mp4")

        if progress_callback:
            progress_callback(i, total, f"✨ 正在处理: {folder_name}")

        if os.path.isfile(output_file):
            print(f"⚠️ 文件已存在，跳过合并：{output_file}")
            continue

        if os.path.isfile(m4s1) and os.path.isfile(m4s2):
            command = [
                ffmpeg_path,
                "-i", m4s1,
                "-i", m4s2,
                "-c", "copy",
                output_file
            ]

            print(f"Merging: {folder_path}")
            
            # 修改这里：添加 creationflags 参数
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(
                    command, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True,
                    startupinfo=startupinfo
                )
            else:
                result = subprocess.run(
                    command, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )

            if result.returncode == 0:
                print(f"✅ 成功合并：{output_file}")
            else:
                print(f"❌ 合并失败：{folder_path}\n{result.stderr}")
        else:
            print(f"⚠️ 缺少 1_delete8.m4s 或 2_delete8.m4s，{folder_path}")

class VideoMergerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_first_load = True
        self.setWindowTitle("哔哩哔哩视频合并器 - XY_Blue制作 🌞")
        self.resize(1250, 600)
        self.setStyleSheet(STYLE_SHEET)
        
        if os.path.exists('tubiao.ico'):
            self.setWindowIcon(QIcon('tubiao.ico'))

        self.video_dir, self.ffmpeg_path = get_config()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4a6fa5;
                width: 10px;
            }
        """)
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

        self.status_label = QLabel("1️⃣设置哔哩哔哩缓存目录   2️⃣设置ffmpeg.exe可执行文件   🌟删除资源需在哔哩哔哩清理缓存  🌟点击对应视频进入对应文件夹    🔒暂时禁用批量导出 避免滥用")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.config_button = QPushButton("📂 设置目录")
        self.config_button.clicked.connect(self.set_video_dir)
        
        self.ffmpeg_button = QPushButton("🔧 设置FFmpeg")
        self.ffmpeg_button.clicked.connect(self.set_ffmpeg_path)
        
        self.merge_button = QPushButton("🚀 开始合并")
        self.merge_button.clicked.connect(self.run_merge_process)
        
        button_layout.addWidget(self.config_button)
        button_layout.addWidget(self.ffmpeg_button)
        button_layout.addWidget(self.merge_button)
        self.layout.addLayout(button_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_area_widget)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.layout.addWidget(self.scroll_area)

        self.video_frames = []
        self.load_previews()

    def set_video_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择视频目录", self.video_dir or os.path.expanduser("~"))
        if directory:
            self.video_dir = directory
            self.save_config()
            self.load_previews()

    def set_ffmpeg_path(self):
        """设置FFmpeg路径，不再进行验证"""
        file_filter = "Executable files (*.exe);;All files (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择FFmpeg可执行文件", 
            os.path.dirname(self.ffmpeg_path) if self.ffmpeg_path and os.path.exists(self.ffmpeg_path) else "",
            file_filter
        )
        
        if file_path:
            self.ffmpeg_path = file_path
            self.save_config()
            QMessageBox.information(self, "成功", f"FFmpeg路径已设置为:\n{file_path}")

    def save_config(self):
        config = configparser.ConfigParser()
        config['settings'] = {
            'video_dir': self.video_dir,
            'ffmpeg_path': self.ffmpeg_path
        }
        with open('config.ini', 'w', encoding='utf-8') as f:
            config.write(f)

    def open_config(self):
        config_path = os.path.abspath('config.ini')
        if os.path.isfile(config_path):
            os.startfile(config_path)
        else:
            QMessageBox.information(self, "提示", "⚠️ config.ini 文件不存在")

    def run_merge_process(self):
        if not self.video_dir or not os.path.isdir(self.video_dir):
            QMessageBox.critical(self, "错误", "❌ 未找到有效的视频目录或目录不存在。请先设置视频目录。")
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("🔄 准备开始合并...")
        QApplication.processEvents()
        
        QTimer.singleShot(100, self._run_merge_process)

    def _run_merge_process(self):
        try:
            self.status_label.setText("🔄 正在复制和重命名m4s文件...")
            QApplication.processEvents()
            copy_and_rename_m4s(self.video_dir)
            
            self.status_label.setText("🔄 正在处理m4s文件...")
            QApplication.processEvents()
            delete_first_9_bytes(self.video_dir)
            
            self.status_label.setText("🔄 正在合并视频...")
            QApplication.processEvents()
            merge_m4s_to_mp4(self.video_dir, self.ffmpeg_path, self.update_progress)
            
            self.status_label.setText("✅ 所有处理完成！")
            self.progress_bar.setValue(100)
            QMessageBox.information(
                self, 
                "视频已合并", 
                "🎉【更新的视频见下方左】 😈【若未完成请校验路径和程序】"
            )
        except Exception as e:
            self.status_label.setText(f"❌ 处理出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"⚠️ 处理过程中发生错误:\n{str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            self.load_previews()

    def update_progress(self, current, total, message):
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        QApplication.processEvents()

    def get_video_thumbnail(self, mp4_path):
        folder = os.path.dirname(mp4_path)
        base = os.path.splitext(os.path.basename(mp4_path))[0]

        for ext in ['jpg', 'png', 'jpeg']:
            thumb_path = os.path.join(folder, base + '.' + ext)
            if os.path.isfile(thumb_path):
                pix = QPixmap(thumb_path)
                return pix.scaled(200, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        thumb_path = os.path.join(folder, base + '.jpg')
        if not os.path.isfile(thumb_path):
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', mp4_path,
                '-ss', '00:00:05',
                '-vframes', '1',
                '-q:v', '2',
                thumb_path
            ]

            # 修改这里：添加隐藏窗口的参数
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run(
                    cmd, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    startupinfo=startupinfo
                )
            else:
                subprocess.run(
                    cmd, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )

        if os.path.isfile(thumb_path):
            pix = QPixmap(thumb_path)
            return pix.scaled(200, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        default_pix = QPixmap(200, 120)
        default_pix.fill(QColor(200, 200, 200))
        return default_pix

    def open_folder(self, folder_path):
        """打开指定文件夹"""
        if os.path.isdir(folder_path):
            os.startfile(folder_path)

    def load_previews(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.video_frames.clear()

        if not self.video_dir or not os.path.isdir(self.video_dir):
            no_videos_label = QLabel("📁 没有找到可合并的视频，请先设置视频目录")
            no_videos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_videos_label.setStyleSheet("font-size: 14px; color: #666;")
            self.grid_layout.addWidget(no_videos_label, 0, 0, 1, 1)
            return

        # 获取所有文件夹并按创建时间排序（新视频在前）
        folders = []
        for folder in os.listdir(self.video_dir):
            full_path = os.path.join(self.video_dir, folder)
            if os.path.isdir(full_path):
                ctime = os.path.getctime(full_path)
                folders.append((ctime, folder, full_path))
        
        # 按创建时间倒序排序（新视频在前）
        folders.sort(key=lambda x: x[0], reverse=True)
        
        for ctime, folder, full_path in folders:
            mp4_file = os.path.join(full_path, f"{folder}.mp4")
            if os.path.isfile(mp4_file):
                frame = QFrame()
                frame.setFrameShape(QFrame.Shape.Box)
                frame.setLineWidth(1)
                frame.setFixedSize(220, 200)  # 增加高度以容纳创建时间
                frame.setStyleSheet("QFrame { background-color: white; border-radius: 5px; }")
                
                vbox = QVBoxLayout(frame)
                vbox.setContentsMargins(10, 10, 10, 10)
                vbox.setSpacing(5)
                
                thumb = self.get_video_thumbnail(mp4_file)
                thumb_label = QLabel()
                thumb_label.setPixmap(thumb)
                thumb_label.setFixedSize(200, 120)
                thumb_label.setScaledContents(True)
                thumb_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                thumb_label.mousePressEvent = lambda e, path=full_path: self.open_folder(path)
                vbox.addWidget(thumb_label)
                
                title_label = QLabel(folder)
                title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
                title_label.setWordWrap(True)
                title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                vbox.addWidget(title_label)
                
                # 添加创建时间显示
                create_time = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')
                time_label = QLabel(f"创建时间: {create_time}")
                time_label.setStyleSheet("color: #666; font-size: 10px;")
                time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                vbox.addWidget(time_label)
                
                status_label = QLabel("✅ 已合并")
                status_label.setStyleSheet("color: green; font-size: 11px;")
                status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                vbox.addWidget(status_label)
                
                self.video_frames.append(frame)

        self.relayout_videos()
        
        if self.is_first_load:
            self.is_first_load = False
            QTimer.singleShot(100, self.relayout_videos)

    def relayout_videos(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                self.grid_layout.removeWidget(widget)

        if not self.video_frames:
            no_videos_label = QLabel("📁 没有找到可合并的视频，请先设置视频目录")
            no_videos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_videos_label.setStyleSheet("font-size: 14px; color: #666;")
            self.grid_layout.addWidget(no_videos_label, 0, 0, 1, 1)
            return

        area_width = self.scroll_area.viewport().width()
        col_width = 240
        max_cols = max(1, area_width // col_width)

        row, col = 0, 0
        for frame in self.video_frames:
            self.grid_layout.addWidget(frame, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.relayout_videos()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont()
    font.setFamily("Microsoft YaHei" if sys.platform == "win32" else "PingFang SC")
    font.setPointSize(10)
    app.setFont(font)
    
    window = VideoMergerApp()
    window.show()
    sys.exit(app.exec())