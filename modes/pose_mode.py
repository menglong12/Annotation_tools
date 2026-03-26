# modes/pose_mode.py
from PyQt5.QtWidgets import QMenu, QMessageBox
from PyQt5.QtGui import QFont, QFontMetrics, QColor, QPen, QIcon, QPixmap
from PyQt5.QtCore import Qt, QPoint, QRectF
from core.base_label import BaseImageLabel

class PoseImageLabel(BaseImageLabel):
    """
    姿势标注模式
    """
    
    def __init__(self, parent=None, mode_config=None):
        super().__init__(parent, mode_config)
        self.type_names = self.mode_config.get('types', [
            "站立", "坐下", "趴下", "侧躺", "蹲下", "后腿站立", "半侧卧", "蜷缩", "弓背", "其他"
        ])
        self.max_points = 3
    
    def draw_annotations(self, painter):
        if not self.points:
            return
        
        font = QFont("Microsoft YaHei", 12, QFont.Bold)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        
        for point in self.points:
            screen_pos = self.original_to_screen(QPoint(point['x'], point['y']))
            if not screen_pos:
                continue
            
            x, y = screen_pos.x(), screen_pos.y()
            type_idx = point.get('type_index', 0)
            color = self.colors[type_idx % len(self.colors)]
            
            painter.setPen(QPen(QColor(80, 80, 80), 2))
            painter.setBrush(color)
            painter.drawEllipse(x-10, y-10, 20, 20)
            
            painter.setPen(QPen(Qt.white, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(x-10, y-10, 20, 20)
            
            text = point.get('type', self.type_names[0])
            text_w = metrics.width(text)
            text_h = metrics.height()
            
            bg_rect = QRectF(x - text_w/2 - 4, y + 15, text_w + 8, text_h + 4)
            painter.setBrush(QColor(0, 0, 0, 200))
            painter.setPen(Qt.NoPen)
            painter.drawRect(bg_rect)
            
            painter.setPen(Qt.white)
            painter.drawText(int(x - text_w/2), int(y + 15 + text_h), text)
    
    def show_type_menu(self, global_pos):
        menu = QMenu(self)
        menu.setTitle("选择姿势")
        
        for i, pose in enumerate(self.type_names):
            action = menu.addAction(pose)
            action.setData(i)
        
        action = menu.exec_(global_pos)
        if action and self.pending_click:
            self.add_pose_point(self.pending_click, action.data())
            self.pending_click = None
    
    def add_pose_point(self, screen_pos, type_idx):
        orig_pos = self.screen_to_original(screen_pos)
        if not orig_pos:
            return
        
        if len(self.points) >= self.max_points:
            QMessageBox.information(self, "提示", f"最多标注 {self.max_points} 个姿势点（多猫场景）")
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
        for i, point in enumerate(self.points):
            screen = self.original_to_screen(QPoint(point['x'], point['y']))
            if screen and abs(screen.x() - screen_pos.x()) < 15 and \
               abs(screen.y() - screen_pos.y()) < 15:
                return i
        return -1
    
    def update_point_position(self, index, orig_pos):
        if 0 <= index < len(self.points):
            self.points[index]['x'] = orig_pos.x()
            self.points[index]['y'] = orig_pos.y()
            self.update_display()
            self.annotation_changed.emit()
    
    def add_point_annotation(self, orig_pos):
        if len(self.points) < self.max_points:
            self.add_pose_point(self.original_to_screen(orig_pos), 0)
    
    def delete_selected(self):
        if self.points:
            self.points.pop()
            self.update_display()
            self.annotation_changed.emit()
            return True
        return False
    
    def mouseDoubleClickEvent(self, event):
        idx = self.find_point_at(event.pos())
        if idx != -1:
            menu = QMenu(self)
            for i, pose in enumerate(self.type_names):
                action = menu.addAction(pose)
                action.setData((idx, i))
            
            def update_type(action):
                anno_idx, type_idx = action.data()
                self.points[anno_idx]['type'] = self.type_names[type_idx]
                self.points[anno_idx]['type_index'] = type_idx
                self.update_display()
                self.annotation_changed.emit()
                self.status_message.emit(f"已修改为 {self.type_names[type_idx]}")
            
            menu.triggered.connect(update_type)
            menu.exec_(event.globalPos())
