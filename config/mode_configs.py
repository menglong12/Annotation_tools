"""
所有标注模式的配置集中管理
新增模式只需在此添加配置，无需修改主程序
"""
import json
import numpy as np
from PyQt5.QtWidgets import QLabel, QMenu
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QImage, QFontMetrics, QCursor

MODE_CONFIGS = {
    'color': {
        'name': 'color',
        'display_name': '颜色标注',
        'description': '标注猫咪毛色和花纹',
        'icon': 'color_icon.png',
        'file_suffix': 'color',
        'is_video_support': True,
        'sample_rate': 5,
        
        # 标注类型定义
        'types': [
            "纯色-黑色", "纯色-白色", "纯色-橘色",
            "纯色-灰色(蓝色)", "纯色-褐色", "纯色-其他",
            "虎斑-黑白", "虎斑-橙白", "虎斑-黑色",
            "虎斑-橙色", "虎斑-褐色", "虎斑-其他",
            "渐层-金", "渐层-银", "渐层-褐",
            "双色-黑白", "双色-黄白", "双色-灰白",
            "双色-黑黄", "双色-白褐", "双色-其他",
            "三色-橘白黑", "三色-戴帽",
            "斑点-黑白", "斑点-黑黄",
            "长毛", "其他"
        ],
        
        # 功能开关
        'support_rectangle': False,  # 仅关键点
        'support_point': True,
        
        # 视觉配置
        'colors': [
            QColor(255, 0, 0), QColor(0, 0, 255), QColor(0, 255, 0),
            QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255),
            QColor(255, 128, 0), QColor(128, 0, 255), QColor(0, 255, 128),
            QColor(255, 0, 128), QColor(128, 255, 0), QColor(0, 128, 255),
        ],
        
        # 快捷键
        'shortcuts': {
            'next_type': 'Tab',  # 切换类型
        }
    },
    
    'kps': {
        'name': 'kps',
        'display_name': '关键点标注',
        'description': '标注21个身体关键点',
        'icon': 'kps_icon.png',
        'file_suffix': 'kps',
        'is_video_support': True,
        'sample_rate': 5,
        
        'types': [
            "左眼", "右眼", "鼻尖", "下巴",
            "左耳尖", "右耳尖", "后颈",
            "左前腿根部", "左前腿膝盖", "左前腿爪子",
            "右前腿根部", "右前腿膝盖", "右前腿爪子",
            "左后腿根部", "左后腿膝盖", "左后腿爪子",
            "右后腿根部", "右后腿膝盖", "右后腿爪子",
            "尾巴根部", "尾巴顶端"
        ],
        
        # 关键点分组（用于Shift+滚轮切换显示）
        'groups': [
            [0, 2, 3, 4, 6],      # 头部左侧
            [1, 2, 3, 5, 6],      # 头部右侧
            [7, 8, 9],            # 左前腿
            [10, 11, 12],         # 右前腿
            [13, 14, 15],         # 左后腿
            [16, 17, 18],         # 右后腿
            [19, 20]              # 尾巴
        ],
        
        'support_rectangle': True,   # 支持矩形框（身体区域）
        'support_point': True,
        
        'colors': [QColor(255, 0, 0), QColor(0, 0, 255)],  # 红/蓝双色
    },
    
    'pose': {
        'name': 'pose',
        'display_name': '姿势标注',
        'description': '标注猫咪姿势类型',
        'icon': 'pose_icon.png',
        'file_suffix': 'pose',
        'is_video_support': True,
        'sample_rate': 5,
        
        'types': [
            "站立", "坐下", "趴下", "侧躺",
            "蹲下", "后腿站立", "半侧卧",
            "蜷缩", "弓背", "其他"
        ],
        
        'support_rectangle': False,
        'support_point': True,
    },
    
    'clumps': {
        'name': 'clumps',
        'display_name': '便团标注',
        'description': '标注猫砂盆中的排泄物',
        'icon': 'clumps_icon.png',
        'file_suffix': 'clumps',
        'is_video_support': True,
        'sample_rate': 5,
        
        'types': ["尿团", "软便", "硬便", "粘壁", "其他"],
        'support_rectangle': False,
        'support_point': True,
    },
    
    'face_body': {
        'name': 'face_body',
        'display_name': '面部身体朝向',
        'description': '标注面部和身体朝向',
        'icon': 'face_icon.png',
        'file_suffix': 'face_body',
        'is_video_support': True,
        'sample_rate': 5,
        
        'types': ["正面", "左侧", "右侧", "头顶", "后脑勺", "其他"],
        'rect_types': [  # 矩形框专用类型
            "正面", "左侧", "右侧", "头顶", "后脑勺",
            "身体左侧", "身体右侧", "身体正面", "身体背面", "其他"
        ],
        
        'support_rectangle': True,  # 主要用矩形框
        'support_point': True,     # 保留关键点（可选）
    },
    
    # ========== 预留扩展接口 ==========
    'custom_1': {
        'name': 'custom_1',
        'display_name': '自定义标注 1',
        'description': '预留扩展位置',
        'icon': 'custom_icon.png',
        'file_suffix': 'custom',
        'is_video_support': True,
        'sample_rate': 5,
        'types': ["类型A", "类型B", "类型C"],
        'support_rectangle': True,
        'support_point': True,
        'enabled': False  # 未启用
    }
}

def get_enabled_modes():
    """获取所有启用的模式"""
    return {k: v for k, v in MODE_CONFIGS.items() 
            if v.get('enabled', True)}

def get_mode_config(mode_name):
    """获取指定模式配置"""
    return MODE_CONFIGS.get(mode_name)