# annotation_tool.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# 收集 PyQt5 的数据文件
pyqt5_datas = collect_data_files('PyQt5')
pyqt5_binaries = collect_dynamic_libs('PyQt5')

# 收集 Qt 平台插件
qt_plugins = []
for root, dirs, files in os.walk(sys.executable):
    if 'PyQt5' in root and 'plugins' in root:
        for file in files:
            if file.endswith('.dll'):
                src = os.path.join(root, file)
                dst = os.path.join('PyQt5', 'Qt5', 'plugins', os.path.basename(root))
                qt_plugins.append((src, dst))
        break

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icons', 'icons'),
        ('config', 'config'),
        ('modes', 'modes'),
        ('core', 'core'),
        ('utils', 'utils'),
    ] + pyqt5_datas,
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
    upx=True,
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

# 收集所有必要的 DLL
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