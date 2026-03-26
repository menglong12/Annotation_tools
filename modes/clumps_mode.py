# modes/clumps_mode.py
import os
import json
from PyQt5.QtWidgets import QMenu, QMessageBox
from PyQt5.QtGui import QFont, QFontMetrics, QColor, QPen, QIcon, QPixmap
from PyQt5.QtCore import Qt, QPoint, QRectF
from core.base_label import BaseImageLabel

class ClumpsImageLabel(BaseImageLabel):
    """
    便团标注模式
    特点：小点标注、密集场景、需要计数统计
    """
    
    def __init__(self, parent=None, mode_config=None):
        super().__init__(parent, mode_config)
        self.type_names = self.mode_config.get('types', ["尿团", "软便", "硬便", "粘壁", "其他"])
        self.show_stats = True
        self.type_colors = {
            "尿团": QColor(255, 215, 0),
            "软便": QColor(139, 69, 19),
            "硬便": QColor(160, 82, 45),
            "粘壁": QColor(255, 0, 0),
            "其他": QColor(128, 128, 128)
        }
    
    def draw_annotations(self, painter):
        """绘制便团点"""
        if not self.points:
            return
        
        font = QFont("Microsoft YaHei", 9)
        painter.setFont(font)
        
        stats = {t: 0 for t in self.type_names}
        
        for point in self.points:
            screen_pos = self.original_to_screen(QPoint(point['x'], point['y']))
            if not screen_pos:
                continue
            
            x, y = screen_pos.x(), screen_pos.y()
            type_name = point.get('type', self.type_names[0])
            stats[type_name] = stats.get(type_name, 0) + 1
            
            color = self.type_colors.get(type_name, QColor(128, 128, 128))
            
            # 绘制圆点
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(color)
            painter.drawEllipse(x-5, y-5, 10, 10)
            
            # 高光
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 100))
            painter.drawEllipse(x-3, y-3, 4, 4)
            
            # 显示类型缩写
            short_name = type_name[0:2] if type_name else "?"
            painter.setPen(Qt.white)
            painter.drawText(x-3, y+4, short_name)
        
        if self.show_stats:
            self.draw_stats(painter, stats)
    
    def draw_stats(self, painter, stats):
        """绘制统计面板"""
        panel_w = 150
        panel_h = 30 + len(self.type_names) * 20
        x = self.width() - panel_w - 10
        y = 10
        
        painter.fillRect(x, y, panel_w, panel_h, QColor(0, 0, 0, 180))
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRect(x, y, panel_w, panel_h)
        
        painter.setPen(Qt.white)
        painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        painter.drawText(x + 5, y + 20, "便团统计")
        
        painter.setFont(QFont("Microsoft YaHei", 9))
        y_offset = 40
        total = 0
        
        for type_name in self.type_names:
            count = stats.get(type_name, 0)
            color = self.type_colors.get(type_name, QColor(128, 128, 128))
            
            painter.fillRect(x + 5, y + y_offset - 10, 12, 12, color)
            painter.setPen(Qt.black)
            painter.drawRect(x + 5, y + y_offset - 10, 12, 12)
            
            painter.setPen(Qt.white)
            painter.drawText(x + 22, y + y_offset, f"{type_name}: {count}")
            
            y_offset += 20
            total += count
        
        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        painter.drawText(x + 5, y + y_offset + 5, f"总计: {total}")
    
    def show_type_menu(self, global_pos):
        """显示类型菜单"""
        menu = QMenu(self)
        menu.setTitle("选择便团类型")
        
        for i, clump_type in enumerate(self.type_names):
            action = menu.addAction(clump_type)
            action.setData(i)
            pixmap = QPixmap(16, 16)
            pixmap.fill(self.type_colors.get(clump_type, QColor(128, 128, 128)))
            action.setIcon(QIcon(pixmap))
        
        action = menu.exec_(global_pos)
        if action and self.pending_click:
            self.add_clump_point(self.pending_click, action.data())
            self.pending_click = None
    
    def add_clump_point(self, screen_pos, type_idx):
        """添加便团点"""
        orig_pos = self.screen_to_original(screen_pos)
        if not orig_pos:
            return
        
        self.points.append({
            'i': self.next_id,
            'x': orig_pos.x(),
            'y': orig_pos.y(),
            'type': self.type_names[type_idx],
            'type_index': type_idx
        })
        self.next_id += 1
        self.update_display()
        self.annotation_changed.emit()
        self.status_message.emit(f"已添加 {self.type_names[type_idx]}")
    
    def show_rect_type_menu(self):
        pass
    
    def find_point_at(self, screen_pos):
        """查找点击的点"""
        for i, point in enumerate(self.points):
            screen = self.original_to_screen(QPoint(point['x'], point['y']))
            if screen and abs(screen.x() - screen_pos.x()) < 10 and \
               abs(screen.y() - screen_pos.y()) < 10:
                return i
        return -1
    
    def find_rect_at(self, screen_pos):
        return -1
    
    def update_point_position(self, index, orig_pos):
        if 0 <= index < len(self.points):
            self.points[index]['x'] = orig_pos.x()
            self.points[index]['y'] = orig_pos.y()
            self.update_display()
            self.annotation_changed.emit()
    
    def add_point_annotation(self, orig_pos):
        """默认添加尿团"""
        self.points.append({
            'i': self.next_id,
            'x': orig_pos.x(),
            'y': orig_pos.y(),
            'type': self.type_names[0],
            'type_index': 0
        })
        self.next_id += 1
        self.update_display()
        self.annotation_changed.emit()
        self.status_message.emit(f"已添加 {self.type_names[0]}")
    
    def delete_selected(self):
        """删除最后一个点"""
        if self.points:
            deleted = self.points.pop()
            self.update_display()
            self.annotation_changed.emit()
            self.status_message.emit(f"已删除 {deleted.get('type', '点')}")
            return True
        return False
    
    def mouseDoubleClickEvent(self, event):
        """双击修改类型"""
        idx = self.find_point_at(event.pos())
        if idx != -1:
            menu = QMenu(self)
            for i, clump_type in enumerate(self.type_names):
                action = menu.addAction(clump_type)
                action.setData((idx, i))
                pixmap = QPixmap(16, 16)
                pixmap.fill(self.type_colors.get(clump_type, QColor(128, 128, 128)))
                action.setIcon(QIcon(pixmap))
            
            def update_type(action):
                anno_idx, type_idx = action.data()
                self.points[anno_idx]['type'] = self.type_names[type_idx]
                self.points[anno_idx]['type_index'] = type_idx
                self.update_display()
                self.annotation_changed.emit()
                self.status_message.emit(f"已修改为 {self.type_names[type_idx]}")
            
            menu.triggered.connect(update_type)
            menu.exec_(event.globalPos())
