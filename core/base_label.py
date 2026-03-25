# core/base_label.py
import os
import json
import cv2
import numpy as np
from PyQt5.QtWidgets import QLabel, QMenu
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QImage, QFontMetrics, QCursor
from PyQt5.QtCore import Qt, QPoint, QRect, QRectF, QSize, pyqtSignal, QPointF

class BaseImageLabel(QLabel):
    '''
    图像标注组件基类
    支持：图片/视频、缩放、平移、十字线、关键点/矩形标注
    '''
    
    annotation_changed = pyqtSignal()
    status_message = pyqtSignal(str)
    
    def __init__(self, parent=None, mode_config=None):
        super().__init__(parent)
        self.mode_config = mode_config or {}
        
        # 显示状态
        self.setAlignment(Qt.AlignCenter)
        self.setMouseTracking(True)
        self.setMinimumSize(400, 300)
        
        # 媒体数据
        self.media_path = None
        self.pixmap = None
        self.is_video = False
        self.video_capture = None
        self.current_frame_idx = 0
        self.total_frames = 0
        self.fps = 0
        self.sample_rate = self.mode_config.get('sample_rate', 5)
        
        # 标注数据 - 统一使用 points 和 rectangles
        self.points = []           # 当前帧的点标注
        self.rectangles = []       # 当前帧的矩形标注
        self.video_annotations = {}  # 视频：帧索引 -> {points, rectangles}
        self.next_id = 0
        
        # 交互状态
        self.zoom_factor = 1.0
        self.min_zoom, self.max_zoom = 0.2, 4.0
        self.pan_offset = QPoint(0, 0)
        self.panning = False
        self.pan_start = QPoint()
        self.drag_point_index = -1
        self.drag_rect_index = -1
        self.drawing_rect = False
        self.rect_start = QPoint()
        self.rect_end = QPoint()
        self.pending_click = None
        
        # 视觉样式
        self.setup_visual_style()
    
    def setup_visual_style(self):
        self.crosshair_color = QColor(255, 165, 0, 180)
        self.crosshair_pen = QPen(self.crosshair_color, 1, Qt.DashLine)
        self.bg_color = QColor(45, 45, 48)
        self.colors = self.mode_config.get('colors', [
            QColor(255, 0, 0), QColor(0, 0, 255), QColor(0, 255, 0),
            QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255)
        ])
    
    # ============== 媒体加载 ==============
    def load_media(self, path):
        self.media_path = path
        ext = path.lower().split('.')[-1]
        
        if ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
            return self.load_video(path)
        else:
            return self.load_image(path)
    
    def load_video(self, path):
        self.is_video = True
        self.video_capture = cv2.VideoCapture(path)
        
        if not self.video_capture.isOpened():
            return False
        
        self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.current_frame_idx = 0
        
        self.load_video_annotations()
        return self.seek_frame(0)
    
    def load_image(self, path):
        self.is_video = False
        self.pixmap = QPixmap(path)
        if self.pixmap.isNull():
            return False
        
        self.load_image_annotations()
        self.reset_view()
        return True
    
    def seek_frame(self, frame_idx):
        """跳转到指定帧"""
        if not self.is_video or not self.video_capture:
            return False
        
        frame_idx = max(0, min(frame_idx, self.total_frames - 1))
        self.current_frame_idx = frame_idx
        
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.video_capture.read()
        
        if not ret:
            return False
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.pixmap = QPixmap.fromImage(q_image)
        
        # 加载该帧的标注
        frame_data = self.video_annotations.get(frame_idx, {})
        self.points = frame_data.get('points', [])
        self.rectangles = frame_data.get('rectangles', [])
        
        self.update_next_point_hint()
        self.update_display()
        self.annotation_changed.emit()
        return True
    
    # ============== 标注文件加载/保存 ==============
    def get_annotation_path(self):
        """获取标注文件路径"""
        if not self.media_path:
            return None
        
        base_name = os.path.splitext(self.media_path)[0]
        suffix = self.mode_config.get('file_suffix', 'anno')
        
        if self.is_video:
            return f"{base_name}_frame_{self.current_frame_idx}.{suffix}.json"
        else:
            return f"{base_name}.{suffix}.json"
    
    def load_image_annotations(self):
        """加载图片标注"""
        self.points = []
        self.rectangles = []
        
        path = self.get_annotation_path()
        if not path or not os.path.exists(path):
            self.update_next_point_hint()
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.points = data.get('points', [])
                self.rectangles = data.get('rectangles', [])
                self.next_id = max([p.get('i', -1) for p in self.points] + 
                                  [r.get('i', -1) for r in self.rectangles] + [-1]) + 1
        except Exception as e:
            print(f"加载标注失败：{e}")
        
        self.update_next_point_hint()
    
    def load_video_annotations(self):
        """加载视频所有帧的标注"""
        self.video_annotations = {}
        base_name = os.path.splitext(self.media_path)[0]
        suffix = self.mode_config.get('file_suffix', 'anno')
        
        import glob
        pattern = f"{base_name}_frame_*.{suffix}.json"
        for file_path in glob.glob(pattern):
            try:
                filename = os.path.basename(file_path)
                frame_str = filename.split('_frame_')[1].split('.')[0]
                frame_idx = int(frame_str)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.video_annotations[frame_idx] = {
                        'points': data.get('points', []),
                        'rectangles': data.get('rectangles', [])
                    }
            except Exception as e:
                print(f"加载视频标注失败 {file_path}: {e}")
    
    def save_current_annotations(self):
        """保存当前帧的标注"""
        if not self.media_path:
            return False
        
        # 过滤空数据
        if not self.points and not self.rectangles:
            path = self.get_annotation_path()
            if path and os.path.exists(path):
                os.remove(path)
            return True

        path = self.get_annotation_path()
        
        if self.is_video:
            self.video_annotations[self.current_frame_idx] = {
                'points': self.points.copy(),
                'rectangles': self.rectangles.copy()
            }
            # path = self.get_annotation_path()
        
        data = {
            'points': self.points,
            'rectangles': self.rectangles,
            'image_path': os.path.basename(self.media_path)
        }
        
        if self.is_video:
            data['frame_index'] = self.current_frame_idx
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存标注失败: {e}")
            return False
    
    def save_all_annotations(self):
        """保存所有标注（视频模式）"""
        if not self.is_video:
            return self.save_current_annotations()
        
        success = True
        for frame_idx, data in self.video_annotations.items():
            base_name = os.path.splitext(self.media_path)[0]
            suffix = self.mode_config.get('file_suffix', 'anno')
            path = f"{base_name}_frame_{frame_idx}.{suffix}.json"
            
            save_data = {
                'points': data.get('points', []),
                'rectangles': data.get('rectangles', []),
                'image_path': os.path.basename(self.media_path),
                'frame_index': frame_idx
            }
            
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"保存失败 {path}: {e}")
                success = False
        
        return success
    
    # ============== 视图控制 ==============
    def reset_view(self):
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.update_display()
    
    def zoom_in(self):
        if self.pixmap:
            self.zoom_factor = min(self.zoom_factor * 1.2, self.max_zoom)
            self.update_display()
    
    def zoom_out(self):
        if self.pixmap:
            self.zoom_factor = max(self.zoom_factor * 0.8, self.min_zoom)
            self.update_display()
    
    def update_display(self):
        if not self.pixmap or self.pixmap.isNull():
            self.clear()
            return
        
        scaled_width = int(self.width() * self.zoom_factor)
        scaled_height = int(self.height() * self.zoom_factor)
        
        pixmapTmp = self.pixmap.scaled(
            scaled_width, scaled_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.scaled_pixmap = pixmapTmp
        
        x = (self.width() - pixmapTmp.width()) // 2 + self.pan_offset.x()
        y = (self.height() - pixmapTmp.height()) // 2 + self.pan_offset.y()
        self.scaled_rect = QRect(x, y, pixmapTmp.width(), pixmapTmp.height())
        
        img = QImage(self.size(), QImage.Format_ARGB32)
        img.fill(self.bg_color)
        
        painter = QPainter(img)
        painter.drawPixmap(x, y, pixmapTmp)
        
        # 绘制标注
        self.draw_annotations(painter)
        
        # 绘制正在绘制的矩形
        if self.drawing_rect:
            x1 = self.scaled_rect.x() + self.rect_start.x() * self.scaled_rect.width() / self.pixmap.width()
            y1 = self.scaled_rect.y() + self.rect_start.y() * self.scaled_rect.height() / self.pixmap.height()
            x2 = self.scaled_rect.x() + self.rect_end.x() * self.scaled_rect.width() / self.pixmap.width()
            y2 = self.scaled_rect.y() + self.rect_end.y() * self.scaled_rect.height() / self.pixmap.height()
            
            painter.setPen(QPen(QColor(255, 165, 0), 2, Qt.DashLine))
            painter.setBrush(QColor(255, 165, 0, 50))
            painter.drawRect(QRectF(QPointF(x1, y1), QPointF(x2, y2)))
        
        # 绘制十字线
        if hasattr(self, 'current_point') and self.current_point:
            painter.setPen(self.crosshair_pen)
            painter.drawLine(0, self.current_point.y(), self.width(), self.current_point.y())
            painter.drawLine(self.current_point.x(), 0, self.current_point.x(), self.height())
        
        # 绘制视频进度条
        if self.is_video:
            self.draw_video_progress(painter)
        
        painter.end()
        self.setPixmap(QPixmap.fromImage(img))
    
    def draw_video_progress(self, painter):
        bar_height = 4
        y = self.height() - bar_height - 20
        
        painter.fillRect(20, y, self.width() - 40, bar_height, QColor(80, 80, 80))
        
        if self.total_frames > 0:
            progress = (self.current_frame_idx + 1) / self.total_frames
            fill_w = int((self.width() - 40) * progress)
            painter.fillRect(20, y, fill_w, bar_height, QColor(0, 122, 204))
        
        painter.setPen(Qt.white)
        painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        text = f"{self.current_frame_idx + 1} / {self.total_frames}"
        painter.drawText(20, y - 5, text)
    
    # ============== 坐标转换 ==============
    def screen_to_original(self, screen_pos):
        if not self.pixmap or self.scaled_rect.isEmpty():
            return None
        
        x = (screen_pos.x() - self.scaled_rect.x()) * self.pixmap.width() / self.scaled_rect.width()
        y = (screen_pos.y() - self.scaled_rect.y()) * self.pixmap.height() / self.scaled_rect.height()
        
        x, y = int(x), int(y)
        if 0 <= x < self.pixmap.width() and 0 <= y < self.pixmap.height():
            return QPoint(x, y)
        return None
    
    def original_to_screen(self, orig_pos):
        if not self.pixmap or self.scaled_rect.isEmpty():
            return None
        
        x = self.scaled_rect.x() + orig_pos.x() * self.scaled_rect.width() / self.pixmap.width()
        y = self.scaled_rect.y() + orig_pos.y() * self.scaled_rect.height() / self.pixmap.height()
        return QPoint(int(x), int(y))
    
    # ============== 事件处理 ==============
    def mousePressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.button() == Qt.LeftButton:
            self.panning = True
            self.pan_start = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            return
        
        if event.button() == Qt.LeftButton:
            # 检查是否点击在点上
            idx = self.find_point_at(event.pos())
            if idx != -1:
                self.drag_point_index = idx
                return
            
            # 检查是否点击在矩形上
            idx = self.find_rect_at(event.pos())
            if idx != -1:
                self.drag_rect_index = idx
                self.drag_start = event.pos()
                return
            
            # 开始绘制矩形
            if self.mode_config.get('support_rectangle', False):
                orig_pos = self.screen_to_original(event.pos())
                if orig_pos:
                    self.drawing_rect = True
                    self.rect_start = orig_pos
                    self.rect_end = orig_pos
        
        if event.button() == Qt.RightButton:
            self.pending_click = event.pos()
            self.show_type_menu(event.globalPos())
    
    def mouseMoveEvent(self, event):
        self.current_point = event.pos()
        
        if self.panning:
            delta = event.pos() - self.pan_start
            self.pan_offset += delta
            self.pan_start = event.pos()
            self.update_display()
            return
        
        if self.drag_point_index != -1:
            orig_pos = self.screen_to_original(event.pos())
            if orig_pos:
                self.update_point_position(self.drag_point_index, orig_pos)
            return
        
        if self.drag_rect_index != -1:
            orig_pos = self.screen_to_original(event.pos())
            if orig_pos:
                rect = self.rectangles[self.drag_rect_index]
                delta_x = orig_pos.x() - self.drag_start.x()
                delta_y = orig_pos.y() - self.drag_start.y()
                rect['x'] += delta_x
                rect['y'] += delta_y
                self.drag_start = orig_pos
                self.update_display()
            return
        
        if self.drawing_rect:
            orig_pos = self.screen_to_original(event.pos())
            if orig_pos:
                self.rect_end = orig_pos
                self.update_display()
            return
        
        self.update_display()
    
    def mouseReleaseEvent(self, event):
        if self.panning:
            self.panning = False
            self.setCursor(QCursor(Qt.ArrowCursor))
            return
        
        if self.drag_point_index != -1:
            self.drag_point_index = -1
        
        if self.drag_rect_index != -1:
            self.drag_rect_index = -1
        
        if self.drawing_rect:
            self.drawing_rect = False
            w = abs(self.rect_end.x() - self.rect_start.x())
            h = abs(self.rect_end.y() - self.rect_start.y())
            
            if w > 5 and h > 5:
                self.show_rect_type_menu()
            else:
                self.add_point_annotation(self.rect_start)
        
        self.update_display()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.undo_last()
        elif event.key() == Qt.Key_Delete:
            self.delete_selected()
        else:
            super().keyPressEvent(event)
    
    # ============== 子类需要实现的接口 ==============
    def draw_annotations(self, painter):
        raise NotImplementedError
    
    def update_next_point_hint(self):
        pass
    
    def show_type_menu(self, global_pos):
        raise NotImplementedError
    
    def show_rect_type_menu(self):
        raise NotImplementedError
    
    def find_point_at(self, screen_pos):
        return -1
    
    def find_rect_at(self, screen_pos):
        return -1
    
    def update_point_position(self, index, orig_pos):
        pass
    
    def add_point_annotation(self, orig_pos):
        pass
    
    def undo_last(self):
        if self.points:
            self.points.pop()
            self.update_display()
            self.annotation_changed.emit()
            return True
        elif self.rectangles:
            self.rectangles.pop()
            self.update_display()
            self.annotation_changed.emit()
            return True
        return False
    
    def delete_selected(self):
        pass