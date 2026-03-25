#!/bin/bash

APP_NAME="PetkitAnnotationTool"
VERSION="1.0.0"
OUTPUT_DIR="dist"

rm -rf build dist *.spec

pyinstaller --name="$APP_NAME" \
    --windowed \
    --onefile \
    --add-data="icons:icons" \
    --add-data="config:config" \
    --add-data="modes:modes" \
    --add-data="core:core" \
    --add-data="utils:utils" \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=PyQt5.QtWidgets \
    --hidden-import=cv2 \
    --hidden-import=numpy \
    --hidden-import=json \
    --hidden-import=imghdr \
    main.py

echo "打包完成！输出目录: $OUTPUT_DIR/$APP_NAME"


