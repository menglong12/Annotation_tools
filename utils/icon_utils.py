# utils/icon_utils.py
import os
import sys
from PyQt5.QtWidgets import QStyle
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

class IconManager:
    """图标管理器"""
    
    def __init__(self):
        self.icon_cache = {}
        self.use_emoji = True
        
    def get_icon(self, icon_name, size=16):
        """获取图标"""
        # 检查缓存
        cache_key = f"{icon_name}_{size}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        # 1. 尝试从资源文件加载
        icon = self._load_from_resource(icon_name, size)
        if icon:
            self.icon_cache[cache_key] = icon
            return icon
        
        # 2. 尝试从系统主题加载
        icon = self._load_from_system(icon_name, size)
        if icon:
            self.icon_cache[cache_key] = icon
            return icon
        
        # 3. 使用 Unicode 字符
        if self.use_emoji:
            unicode_char = self._get_unicode_char(icon_name)
            if unicode_char:
                self.icon_cache[cache_key] = unicode_char
                return unicode_char
        
        return None
    
    def _load_from_resource(self, icon_name, size):
        """从资源文件加载"""
        # 查找图标文件
        possible_paths = [
            f"icons/{icon_name}.png",
            f"icons/{icon_name}.svg",
            f"icons/{icon_name}.ico",
            os.path.join(os.path.dirname(__file__), f"../icons/{icon_name}.png"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                icon = QIcon(path)
                if not icon.isNull():
                    return icon
        return None
    
    def _load_from_system(self, icon_name, size):
        """从系统主题加载"""
        try:
            from PyQt5.QtWidgets import QApplication
            style = QApplication.style()
            
            # 标准图标映射
            standard_map = {
                'save': QStyle.SP_DialogSaveButton,
                'open': QStyle.SP_DialogOpenButton,
                'prev': QStyle.SP_ArrowBack,
                'next': QStyle.SP_ArrowForward,
                'zoom_in': QStyle.SP_DialogApplyButton,
                'zoom_out': QStyle.SP_DialogCloseButton,
                'reset': QStyle.SP_RestoreDefaultsButton,
                'prev_frame': QStyle.SP_MediaSkipBackward,
                'next_frame': QStyle.SP_MediaSeekForward,
                'arrowRight': QStyle.SP_ArrowRight,
                'arrowLeft': QStyle.SP_ArrowLeft,
                'help': QStyle.SP_DialogHelpButton
            }
            
            if icon_name in standard_map:
                icon = style.standardIcon(standard_map[icon_name])
                if not icon.isNull():
                    return icon
        except:
            pass
        return None
    
    def _get_unicode_char(self, icon_name):
        """获取 Unicode 字符"""
        unicode_map = {
            'save': '💾',
            'open': '📂',
            'prev': '◀',
            'next': '▶',
            'zoom_in': '🔍+',
            'zoom_out': '🔍-',
            'reset': '⟳',
            'delete': '🗑',
            'edit': '✏',
            'settings': '⚙',
        }
        return unicode_map.get(icon_name, '')

# 全局实例
icon_manager = IconManager()

def get_icon(icon_name, size=16):
    return icon_manager.get_icon(icon_name, size)