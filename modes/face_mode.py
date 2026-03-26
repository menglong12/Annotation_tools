# modes/face_mode.py
from PyQt5.QtWidgets import QMenu, QMessageBox
from PyQt5.QtGui import QFont, QFontMetrics, QColor, QPen, QCursor
from PyQt5.QtCore import Qt, QPoint, QRectF, QPointF
from core.base_label import BaseImageLabel

class FaceImageLabel(BaseImageLabel):
    """
    面部和身体朝向标注模式
    """
    
    KEYPOINT_TYPES = ["正面", "左侧", "右侧", "头顶", "后脑勺", "其他"]
    RECT_TYPES = [
        "正面", "左侧", "右侧", "头顶", "后脑勺",
        "身体左侧", "身体右侧", "身体正面", "身体背面", "其他"
    ]
    
    def __init__(self, parent=None, mode_config=None):
        super().__init__(parent, mode_config)
        self.rect_colors = [
            QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255),
            QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255)
        ]
        self.drag_rect_index = -1
        self.drag_start = QPoint()
    
    def draw_annotations(self, painter):
        font = QFont("Microsoft YaHei", 10, QFont.Bold)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        
        # 绘制关键点
        for point in self.points:
            screen_pos = self.original_to_screen(QPoint(point['x'], point['y']))
            if not screen_pos:
                continue
            
            x, y = screen_pos.x(), screen_pos.y()
            type_idx = point.get('type_index', 0)
            color = self.colors[type_idx % len(self.colors)]
            
            painter.setPen(QPen(Qt.white, 2))
            painter.setBrush(color)
            painter.drawEllipse(x-6, y-6, 12, 12)
            
            text = point.get('type', '')
            text_w = metrics.width(text)
            bg_rect = QRectF(x - text_w/2 - 2, y + 10, text_w + 4, metrics.height() + 2)
            painter.fillRect(bg_rect, QColor(0, 0, 0, 180))
            painter.setPen(Qt.white)
            painter.drawText(int(x - text_w/2), int(y + 10 + metrics.height()), text)
        
        # 绘制矩形框
        for idx, rect in enumerate(self.rectangles):
            x1 = self.scaled_rect.x() + rect['x'] * self.scaled_rect.width() / self.pixmap.width()
            y1 = self.scaled_rect.y() + rect['y'] * self.scaled_rect.height() / self.pixmap.height()
            x2 = x1 + rect['w'] * self.scaled_rect.width() / self.pixmap.width()
            y2 = y1 + rect['h'] * self.scaled_rect.height() / self.pixmap.height()
            
            type_idx = rect.get('type_index', 0)
            color = self.rect_colors[type_idx % len(self.rect_colors)]
            
            painter.setPen(QPen(color, 3, Qt.SolidLine))
            painter.setBrush(QColor(color.red(), color.green(), color.blue(), 30))
            painter.drawRect(QRectF(QPointF(x1, y1), QPointF(x2, y2)))
            
            text = rect.get('type', '')
            text_w = metrics.width(text)
            text_h = metrics.height()
            
            label_rect = QRectF(min(x1, x2), min(y1, y2) - text_h - 4, text_w + 8, text_h + 4)
            painter.fillRect(label_rect, color)
            painter.setPen(Qt.white)
            painter.drawText(int(min(x1, x2) + 4), int(min(y1, y2) - 6), text)
    
    def show_type_menu(self, global_pos):
        menu = QMenu(self)
        menu.setTitle("添加朝向关键点")
        
        for i, t in enumerate(self.KEYPOINT_TYPES):
            action = menu.addAction(t)
            action.setData(('point', i))
        
        action = menu.exec_(global_pos)
        if action and self.pending_click:
            _, type_idx = action.data()
            self.add_face_point(self.pending_click, type_idx)
            self.pending_click = None
    
    def add_face_point(self, screen_pos, type_idx):
        orig_pos = self.screen_to_original(screen_pos)
        if not orig_pos:
            return
        
        self.points.append({
            'i': self.next_id,
            'x': orig_pos.x(),
            'y': orig_pos.y(),
            'type': self.KEYPOINT_TYPES[type_idx],
            'type_index': type_idx
        })
        self.next_id += 1
        self.update_display()
        self.annotation_changed.emit()
        self.status_message.emit(f"已添加 {self.KEYPOINT_TYPES[type_idx]}")
    
    def show_rect_type_menu(self):
        x1 = min(self.rect_start.x(), self.rect_end.x())
        y1 = min(self.rect_start.y(), self.rect_end.y())
        x2 = max(self.rect_start.x(), self.rect_end.x())
        y2 = max(self.rect_start.y(), self.rect_end.y())
        
        menu = QMenu(self)
        menu.setTitle("选择矩形类型")
        
        for i, t in enumerate(self.RECT_TYPES):
            action = menu.addAction(t)
            action.setData(i)
        
        action = menu.exec_(QCursor.pos())
        if action:
            type_idx = action.data()
            self.rectangles.append({
                'i': self.next_id,
                'x': x1,
                'y': y1,
                'w': x2 - x1,
                'h': y2 - y1,
                'type': self.RECT_TYPES[type_idx],
                'type_index': type_idx
            })
            self.next_id += 1
            self.drawing_rect = False
            self.update_display()
            self.annotation_changed.emit()
    
    def find_point_at(self, screen_pos):
        for i, point in enumerate(self.points):
            screen = self.original_to_screen(QPoint(point['x'], point['y']))
            if screen and abs(screen.x() - screen_pos.x()) < 12 and \
               abs(screen.y() - screen_pos.y()) < 12:
                return i
        return -1
    
    def find_rect_at(self, screen_pos):
        for i, rect in enumerate(self.rectangles):
            x1 = self.scaled_rect.x() + rect['x'] * self.scaled_rect.width() / self.pixmap.width()
            y1 = self.scaled_rect.y() + rect['y'] * self.scaled_rect.height() / self.pixmap.height()
            x2 = x1 + rect['w'] * self.scaled_rect.width() / self.pixmap.width()
            y2 = y1 + rect['h'] * self.scaled_rect.height() / self.pixmap.height()
            
            if x1 <= screen_pos.x() <= x2 and y1 <= screen_pos.y() <= y2:
                return i
        return -1
    
    def update_point_position(self, index, orig_pos):
        if 0 <= index < len(self.points):
            self.points[index]['x'] = orig_pos.x()
            self.points[index]['y'] = orig_pos.y()
            self.update_display()
            self.annotation_changed.emit()
    
    def add_point_annotation(self, orig_pos):
        self.add_face_point(self.original_to_screen(orig_pos), 0)
    
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
            for i, t in enumerate(self.KEYPOINT_TYPES):
                action = menu.addAction(t)
                action.setData(('kp', idx, i))
            
            def update_kp(action):
                _, idx, type_idx = action.data()
                self.points[idx]['type'] = self.KEYPOINT_TYPES[type_idx]
                self.points[idx]['type_index'] = type_idx
                self.update_display()
                self.annotation_changed.emit()
                self.status_message.emit(f"已修改为 {self.KEYPOINT_TYPES[type_idx]}")
            
            menu.triggered.connect(update_kp)
            menu.exec_(event.globalPos())
            return
        
        rect_idx = self.find_rect_at(event.pos())
        if rect_idx != -1:
            menu = QMenu(self)
            for i, t in enumerate(self.RECT_TYPES):
                action = menu.addAction(t)
                action.setData(('rect', rect_idx, i))
            
            def update_rect(action):
                _, idx, type_idx = action.data()
                self.rectangles[idx]['type'] = self.RECT_TYPES[type_idx]
                self.rectangles[idx]['type_index'] = type_idx
                self.update_display()
                self.annotation_changed.emit()
                self.status_message.emit(f"已修改为 {self.RECT_TYPES[type_idx]}")
            
            menu.triggered.connect(update_rect)
            menu.exec_(event.globalPos())
