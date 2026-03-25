# main.py
import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog,
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QGridLayout,
    QScrollArea, QMessageBox, QStatusBar, QStyle
)
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from utils.icon_utils import get_icon
from config.mode_configs import get_enabled_modes, get_mode_config
from modes import ColorImageLabel, KpsImageLabel, PoseImageLabel, ClumpsImageLabel, FaceImageLabel

MODE_CLASSES = {
    'color': ColorImageLabel,
    'kps': KpsImageLabel,
    'pose': PoseImageLabel,
    'clumps': ClumpsImageLabel,
    'face_body': FaceImageLabel,
}

class ModeCard(QWidget):
    clicked = pyqtSignal(str)
    
    def __init__(self, mode_key, config, parent=None):
        super().__init__(parent)
        self.mode_key = mode_key
        self.config = config
        
        self.setFixedSize(200, 220)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        icon_label = QLabel("🐱")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)
        
        name = QLabel(config['display_name'])
        name.setAlignment(Qt.AlignCenter)
        name.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        name.setStyleSheet("color: #61AFEF;")
        layout.addWidget(name)
        
        desc = QLabel(config['description'])
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        layout.addWidget(desc)
        
        self.setStyleSheet("""
            ModeCard {
                background-color: #3F3F46;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 10px;
            }
            ModeCard:hover {
                border: 2px solid #007ACC;
                background-color: #4A4A52;
            }
        """)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.mode_key)


class ModeSelector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小佩标注平台")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("QMainWindow { background-color: #2D2D30; }")
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        
        title = QLabel("🐱 小佩数据标注平台")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        title.setStyleSheet("color: #61AFEF; padding: 20px;")
        layout.addWidget(title)
        
        subtitle = QLabel("选择要标注的类型")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #888888; font-size: 16px;")
        layout.addWidget(subtitle)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(15)
        
        modes = get_enabled_modes()
        row, col = 0, 0
        for key, config in modes.items():
            card = ModeCard(key, config)
            card.clicked.connect(self.select_mode)
            grid.addWidget(card, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        footer = QLabel("提示：支持图片(.jpg/.png/.bmp)和视频(.mp4/.avi/.mov) | Ctrl+拖拽平移 | 滚轮缩放 | 右键添加标注")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #666666; font-size: 12px; padding: 10px;")
        layout.addWidget(footer)
    
    def select_mode(self, mode_key):
        config = get_mode_config(mode_key)
        if not config:
            QMessageBox.warning(self, "错误", "模式配置不存在")
            return
        
        folder = QFileDialog.getExistingDirectory(
            self, f"选择要标注的文件夹 [{config['display_name']}]",
            str(Path.home())
        )
        if not folder:
            return
        
        annotator_class = MODE_CLASSES.get(mode_key)
        if annotator_class:
            from main import AnnotatorWindow
            self.annotator_window = AnnotatorWindow(mode_key, config, annotator_class, folder)
            self.annotator_window.show()


class AnnotatorWindow(QMainWindow):
    def __init__(self, mode_key, config, label_class, folder):
        super().__init__()
        self.mode_key = mode_key
        self.config = config
        self.folder = folder
        
        self.setWindowTitle(f"{config['display_name']} - {os.path.basename(folder)}")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建图像组件
        self.image_label = label_class(self, config)
        self.image_label.setStyleSheet("background-color: #252526; border: 2px solid #3F3F46;")
        
        self.setup_ui()
        self.load_file_list()
        self.load_current_file()

        # 连接信号
        self.image_label.status_message.connect(self.update_status)

        # 启动鼠标追踪，一遍捕获滚轮事件
        self.setMouseTracking(True)
        self.image_label.setFocusPolicy(Qt.StrongFocus) # 确保图像组件可以获得焦点
        self.image_label.setFocus()
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # 左侧面板
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_panel.setStyleSheet("background-color: #333337; border-right: 1px solid #555555;")
        left_layout = QVBoxLayout(left_panel)
        
        self.file_list = QLabel("文件列表")
        self.file_list.setStyleSheet("color: #61AFEF; font-weight: bold; padding: 5px;")
        left_layout.addWidget(self.file_list)
        
        # 文件列表滚动区
        self.file_scroll = QScrollArea()
        self.file_scroll.setWidgetResizable(True)
        self.file_list_widget = QWidget()
        self.file_layout = QVBoxLayout(self.file_list_widget)
        self.file_layout.setAlignment(Qt.AlignTop)
        self.file_scroll.setWidget(self.file_list_widget)
        left_layout.addWidget(self.file_scroll)
        
        self.progress_label = QLabel("0 / 0")
        self.progress_label.setStyleSheet("color: #CCCCCC; padding: 5px;")
        left_layout.addWidget(self.progress_label)
        
        # 提示标签
        self.hint_label = QLabel("")
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color: #61AFEF; background-color: #252526; padding: 8px; border-radius: 4px;")
        left_layout.addWidget(self.hint_label)
        
        # 连接信号
        self.image_label.status_message.connect(self.hint_label.setText)
        
        # 按钮
        btn_style = """
            QPushButton {
                background-color: #3F3F46;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #555555; }
            QPushButton:pressed { background-color: #007ACC; }
        """
        
        save_btn = QPushButton("保存 (Ctrl+S)")
        icon = get_icon('save')
        if isinstance(icon, QIcon):
            save_btn.setIcon(icon)
            save_btn.setIconSize(QSize(16, 16))
        else:
            save_btn.setText(f"{icon} 保存")
        save_btn.setStyleSheet(btn_style)
        save_btn.clicked.connect(self.save_current)
        
        prev_btn = QPushButton("上一张")
        icon = get_icon('prev')
        if isinstance(icon, QIcon):
            prev_btn.setIcon(icon)
            prev_btn.setIconSize(QSize(16, 16))
        else:
            prev_btn.setText(f"{icon} 上一张")
        prev_btn.setStyleSheet(btn_style)
        prev_btn.clicked.connect(self.prev_file)
        
        next_btn = QPushButton("下一张")
        icon = get_icon('next')
        if isinstance(icon, QIcon):
            next_btn.setIcon(icon)
            next_btn.setIconSize(QSize(16, 16))
        else:
            next_btn.setText(f"{icon} 下一张")
        next_btn.setStyleSheet(btn_style)
        next_btn.clicked.connect(self.next_file)
        
        left_layout.addWidget(save_btn)
        left_layout.addWidget(prev_btn)
        left_layout.addWidget(next_btn)
        
        # 视频控件
        self.video_controls = QWidget()
        self.video_controls.setVisible(False)
        vlayout = QHBoxLayout(self.video_controls)
        
        prev_frame = QPushButton("上一帧")
        icon = get_icon('prev_frame')
        if isinstance(icon, QIcon):
            prev_frame.setIcon(icon)
            prev_frame.setIconSize(QSize(16, 16))
        else:
            prev_frame.setText(f"{icon} 上一帧")
        prev_frame.clicked.connect(self.prev_frame)
        next_frame = QPushButton("下一帧")
        icon = get_icon('next_frame')
        if isinstance(icon, QIcon):
            next_frame.setIcon(icon)
            next_frame.setIconSize(QSize(16, 16))
        else:
            next_frame.setText(f"{icon} 下一帧")
        next_frame.clicked.connect(self.next_frame)
        
        vlayout.addWidget(prev_frame)
        vlayout.addWidget(next_frame)
        left_layout.addWidget(self.video_controls)
        
        left_layout.addStretch()
        layout.addWidget(left_panel)
        
        # 右侧：图像
        right_layout = QVBoxLayout()
        
        # 工具栏
        toolbar = QHBoxLayout()
        zoom_in = QPushButton("放大")
        icon = get_icon('zoom_in')
        if isinstance(icon, QIcon):
            zoom_in.setIcon(icon)
            zoom_in.setIconSize(QSize(16, 16))
        else:
            zoom_in.setText(f"{icon} 放大")
        zoom_in.clicked.connect(self.image_label.zoom_in)
        # zoom_out = QPushButton("🔍-")
        zoom_out = QPushButton("缩小")
        icon = get_icon('zoom_out')
        if isinstance(icon, QIcon):
            zoom_out.setIcon(icon)
            zoom_out.setIconSize(QSize(16, 16))
        else:
            zoom_out.setText(f"{icon} 缩小")
        zoom_out.clicked.connect(self.image_label.zoom_out)
        reset_zoom = QPushButton("重置")
        # reset_zoom = QPushButton("⟲ 重置")
        icon = get_icon('reset')
        if isinstance(icon, QIcon):
            reset_zoom.setIcon(icon)
            reset_zoom.setIconSize(QSize(16, 16))
        else:
            reset_zoom.setText(f"{icon} 重置")
        reset_zoom.clicked.connect(self.image_label.reset_view)
        
        toolbar.addWidget(zoom_in)
        toolbar.addWidget(zoom_out)
        toolbar.addWidget(reset_zoom)
        toolbar.addStretch()
        
        mode_info = QLabel(f"当前模式: {self.config['display_name']}")
        mode_info.setStyleSheet("color: #61AFEF; font-weight: bold;")
        toolbar.addWidget(mode_info)
        
        right_layout.addLayout(toolbar)
        right_layout.addWidget(self.image_label, 1)

        tip_label = QLabel("操作提示：鼠标滚轮切换图片 | ↑ ↓ ← → 上下键切换 | Ctrl+S 保存 | Esc 撤销 | Delete 删除")
        icon = get_icon('help')
        if isinstance(icon, QIcon):
            tip_label.setWindowIcon(icon)
        tip_label.setStyleSheet("color: #888888; font-size: 11px; padding: 5px;")
        tip_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(tip_label)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #CCCCCC; padding: 5px; border-top: 1px solid #555555;")
        right_layout.addWidget(self.status_label)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        right_layout.addWidget(self.status_bar)

        layout.addLayout(right_layout, 1)

    def update_status(self, message):
        """更新状态栏消息"""
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage(message)
        elif hasattr(self, 'hint_label'):
            self.hint_label.setText(message)
    
    def load_file_list(self):
        exts = ('.png', '.jpg', '.jpeg', '.bmp', '.mp4', '.avi', '.mov', '.mkv')
        self.files = []
        for f in os.listdir(self.folder):
            if f.lower().endswith(exts):
                self.files.append(os.path.join(self.folder, f))
        self.files.sort()
        self.current_idx = 0
        
        # 清空文件列表
        while self.file_layout.count():
            child = self.file_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for i, file_path in enumerate(self.files):
            filename = os.path.basename(file_path)
            btn = QPushButton(filename)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding: 5px; border: none; }
                QPushButton:hover { background-color: #4A4A52; }
            """)
            btn.clicked.connect(lambda checked, idx=i: self.goto_file(idx))
            self.file_layout.addWidget(btn)
        
        self.update_progress()

        # 设置图像组件可以获得键盘焦点
        self.image_label.setFocusPolicy(Qt.StrongFocus)
        self.image_label.setFocus()
    
    def goto_file(self, idx):
        if idx != self.current_idx:
            self.image_label.save_current_annotations()
            self.current_idx = idx
            self.load_current_file()
            self.update_progress()
            # 更新状态栏
            self.update_status(f"已切换到：{os.path.basename(self.files[self.current_idx])}")
    
    def load_current_file(self):
        if not self.files:
            self.status_label.setText("文件夹中没有支持的文件")
            return
        
        path = self.files[self.current_idx]
        success = self.image_label.load_media(path)
        
        self.video_controls.setVisible(self.image_label.is_video)
        
        if success:
            self.status_label.setText(f"已加载: {os.path.basename(path)}")
        else:
            self.status_label.setText(f"加载失败: {os.path.basename(path)}")
    
    def save_current(self):
        if self.image_label.save_current_annotations():
            self.status_label.setText("✓ 已保存")
        else:
            self.status_label.setText("✗ 保存失败")
    
    def prev_file(self):
        if self.files and self.current_idx > 0:
            # self.image_label.save_current_annotations()
            # self.current_idx -= 1
            # self.load_current_file()
            # self.update_progress()
            self.goto_file(self.current_idx - 1)
    
    def next_file(self):
        if self.files and self.current_idx < len(self.files) - 1:
            # self.image_label.save_current_annotations()
            # self.current_idx += 1
            # self.load_current_file()
            # self.update_progress()
            self.goto_file(self.current_idx + 1)
    
    def prev_frame(self):
        if self.image_label.is_video:
            self.image_label.save_current_annotations()
            self.image_label.seek_frame(self.image_label.current_frame_idx - 1)
            self.update_status(f"帧 {self.image_label.current_frame_idx + 1} / {self.image_label.total_frames}")
    
    def next_frame(self):
        if self.image_label.is_video:
            self.image_label.save_current_annotations()
            self.image_label.seek_frame(self.image_label.current_frame_idx + 1)
            self.update_status(f"帧 {self.image_label.current_frame_idx + 1} / {self.image_label.total_frames}")
    
    def update_progress(self):
        total = len(self.files)
        current = self.current_idx + 1 if self.files else 0
        self.progress_label.setText(f"{current} / {total}")
        
        for i in range(self.file_layout.count()):
            btn = self.file_layout.itemAt(i).widget()
            if btn:
                if i == self.current_idx:
                    btn.setStyleSheet("background-color: #007ACC; text-align: left; padding: 5px; border: none;")
                else:
                    btn.setStyleSheet("background-color: transparent; text-align: left; padding: 5px; border: none;")
    
    def wheelEvent(self, event):
        # 获取滚轮滑动方向
        delta = event.angleDelta().y()

        # 向下滚动（正数）表示向上滚动，向上滚动（负数）表示向下滚动
        # 向下滚动：下一张，向上滚动：下一张
        if delta > 0:
            # 上一张
            self.prev_file()
        elif delta < 0:
            self.next_file()

        # 接受事件，防止继续传播
        event.accept()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Left or key == Qt.Key_Up:
            self.prev_file()
        elif key == Qt.Key_Right or key == Qt.Key_Down:
            self.next_file()
        elif key == Qt.Key_Escape:
            if self.image_label.undo_last():
                self.update_status("已撤销")
        elif key == Qt.Key_Delete:
            if self.image_label.delete_selected():
                self.update_status("已删除")
        elif key == Qt.Key_S and event.modifiers() == Qt.ControlModifier:
            self.save_current()
        elif key == Qt.Key_Space and self.image_label.is_video:
            self.update_status("空格键：可添加视频播放功能")

        event.accept()

def setup_theme(app):
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(45, 45, 48))
    palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 48))
    palette.setColor(QPalette.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.Button, QColor(60, 60, 60))
    palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
    app.setPalette(palette)

def main():
    # 清除环境变量
    for key in list(os.environ.keys()):
        if 'QT_' in key:
            del os.environ[key]
    
    from PyQt5.QtCore import QLibraryInfo
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = QLibraryInfo.location(QLibraryInfo.PluginsPath)
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    app = QApplication(sys.argv)
    setup_theme(app)
    
    window = ModeSelector()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()