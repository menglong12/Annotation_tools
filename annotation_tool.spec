# annotation_tool.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# 获取 Python 环境路径
python_dir = Path(sys.executable)
site_packages = python_dir.parent / "Lib" / "site-packages"

# 定位 PyQt5 的 platforms 目录
def find_qt_platforms():
    # 尝试常见路径
    possible_paths = [
        site_packages / "PyQt5" / "Qt5" / "plugins" / "platforms",
        site_packages / "PyQt5" / "Qt" / "plugins" / "platforms",
        site_packages / "PyQt5" / "plugins" / "platforms"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # 如果没找到，尝试搜索
    for root, dirs, files in os.walk(str(site_packages)):
        if "platforms" in dirs:
            platform_path = Path(root) / "platforms"
            if any(f.endswith(".dll") for f in os.listdir(platform_path)):
                return platform_path
    
    raise FileNotFoundError("Could not find Qt platforms directory")

try:
    platforms_dir = find_qt_platforms()
    print(f"Found Qt platforms at: {platforms_dir}")
except Exception as e:
    print(f"Error finding Qt platforms: {e}")
    # 使用默认路径作为后备
    platforms_dir = site_packages / "PyQt5" / "Qt5" / "plugins" / "platforms"

# 收集数据文件
pyqt5_datas = collect_data_files("PyQt5")
pyqt5_binaries = collect_dynamic_libs("PyQt5")

# 准备数据列表
base_datas = [
    ('icons', 'icons'),
    ('config', 'config'),
    ('modes', 'modes'),
    ('core', 'core'),
    ('utils', 'utils'),
]

# 添加 platforms 目录
platforms_data = [(str(platforms_dir), "PyQt5/Qt5/plugins/platforms")]

# 合并所有数据
all_datas = base_datas + pyqt5_datas + platforms_data

# 创建 Analysis 对象 - 修复参数顺序
a = Analysis(
    ['main.py'],  # 位置参数
    pathex=[],  # 位置参数
    binaries=pyqt5_binaries,  # 位置参数
    datas=all_datas,  # 关键字参数
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'cv2',
        'numpy',
        'json',
        'imghdr',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tensorflow',
        'torch',
        'matplotlib',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PetkitAnnotationTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PetkitAnnotationTool',
)
