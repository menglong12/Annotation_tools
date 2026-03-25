#!/usr/bin/env python3
"""
启动器：在完全隔离的环境中启动标注工具
确保 cv2 在 PyQt5 之后加载
"""

import os
import sys

# ========== 第 0 步：保存原始环境 ==========
original_environ = dict(os.environ)

# ========== 第 1 步：清除所有 Qt/cv2 相关环境变量 ==========
qt_keys = [k for k in os.environ.keys() if 'QT' in k or 'cv2' in k.lower()]
for key in qt_keys:
    del os.environ[key]
    print(f"✓ 删除环境变量: {key}")

# ========== 第 2 步：创建干净的 Python 环境 ==========
# 移除 cv2 相关的路径
original_path = sys.path.copy()
sys.path = [p for p in sys.path if 'cv2' not in p.lower()]

# ========== 第 3 步：先导入 PyQt5 并初始化 ==========
print("\n=== 初始化 PyQt5 ===")
from PyQt5.QtCore import QLibraryInfo, Qt
from PyQt5.QtWidgets import QApplication

# 获取 PyQt5 的插件路径
qt_plugins = QLibraryInfo.location(QLibraryInfo.PluginsPath)
print(f"✓ PyQt5 插件路径: {qt_plugins}")

# 设置环境变量（必须在 QApplication 创建前）
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugins
os.environ['QT_QPA_PLATFORM'] = 'xcb'

# ========== 第 4 步：创建 QApplication（此时 Qt 已初始化）==========
app = QApplication(sys.argv)
print("✓ QApplication 创建成功")

# ========== 第 5 步：恢复环境，现在可以安全导入 cv2 ==========
print("\n=== 恢复环境，准备加载其他模块 ===")
sys.path = original_path

# 设置 cv2 禁用 Qt
os.environ['OPENCV_VIDEOIO_PRIORITY_BACKEND'] = 'ffmpeg'

# 现在导入 main 的其他部分（此时 Qt 已经初始化，cv2 无法污染）
print("=== 加载主程序 ===")
from main import ModeSelector, setup_theme

# 运行
setup_theme(app)
window = ModeSelector()
window.show()
sys.exit(app.exec_())


