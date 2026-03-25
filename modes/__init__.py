# modes/__init__.py

"""
标注模式包
所有模式类从此处导入
"""

from .color_mode import ColorImageLabel
from .kps_mode import KpsImageLabel
from .pose_mode import PoseImageLabel
from .clumps_mode import ClumpsImageLabel
from .face_mode import FaceImageLabel

__all__ = [
    'ColorImageLabel',
    'KpsImageLabel', 
    'PoseImageLabel',
    'ClumpsImageLabel',
    'FaceImageLabel',
]
