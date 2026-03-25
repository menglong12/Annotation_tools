# modes/kps_mode.py
import os
import json
from PyQt5.QtWidgets import QMenu, QMessageBox
from PyQt5.QtGui import QFont, QFontMetrics, QColor, QPen
from PyQt5.QtCore import Qt, QPoint, QRectF, QPointF
from core.base_label import BaseImageLabel

class KpsImageLabel(BaseImageLabel):
    """
    21点关键点标注模式
    """
    
    KPS_NAMES = [
        "左眼", "右眼", "鼻尖", "下巴",
        "左耳尖", "右耳尖", "后颈",
        "左前腿根部", "左前腿膝盖", "左前腿爪子",
        "右前腿根部", "右前腿膝盖", "右前腿爪子",
        "左后腿根部", "左后腿膝盖", "左后腿爪子",
        "右后腿根部", "右后腿膝盖", "右后腿爪子",
        "尾巴根部", "尾巴顶端"
    ]
    
    # 关键点分组（用于辅助提示）
    KPS_GROUPS = {
        "头部": [0, 1, 2, 3, 4, 5, 6],
        "左前腿": [7, 8, 9],
        "右前腿": [10, 11, 12],
        "左后腿": [13, 14, 15],
        "右后腿": [16, 17, 18],
        "尾巴": [19, 20]
    }
    
    def __init__(self, parent=None, mode_config=None):
        super().__init__(parent, mode_config)
        self.type_names = self.mode_config.get('types', self.KPS_NAMES)
        self.colors = [QColor(255, 0, 0), QColor(0, 0, 255)]
        
        # 状态
        self.show_group = -1
        
        # 信号连接父窗口的状态栏
        if parent:
            # 发送状态信号到父窗口
            self.status_message.connect(parent.update_status)
    
    def draw_annotations(self, painter):
        """绘制关键点"""
        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)
        
        # 确定要显示的关键点索引（用于分组显示功能，可选）
        if self.show_group == -1:
            visible_indices = range(len(self.points))
        else:
            group = self.KPS_GROUPS.get(list(self.KPS_GROUPS.keys())[self.show_group], [])
            visible_indices = [i for i in range(len(self.points)) if i in group]
        
        for i in range(len(self.points)):
            if i not in visible_indices:
                continue
                
            point = self.points[i]
            screen_pos = self.original_to_screen(QPoint(point['x'], point['y']))
            if not screen_pos:
                continue
            
            x, y = screen_pos.x(), screen_pos.y()
            color = self.colors[0] if point.get('color', 'red') == 'red' else self.colors[1]
            
            # 绘制圆点
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.setBrush(color)
            painter.drawEllipse(x-7, y-7, 14, 14)
            
            # 绘制序号和名称
            painter.setPen(Qt.white)
            point_name = point.get('type', self.type_names[i] if i < len(self.type_names) else str(i+1))
            text = f"{i+1}.{point_name}"
            painter.drawText(x+10, y-5, text)
        
        # 绘制矩形框
        for rect in self.rectangles:
            x1 = self.scaled_rect.x() + rect['x'] * self.scaled_rect.width() / self.pixmap.width()
            y1 = self.scaled_rect.y() + rect['y'] * self.scaled_rect.height() / self.pixmap.height()
            x2 = x1 + rect['w'] * self.scaled_rect.width() / self.pixmap.width()
            y2 = y1 + rect['h'] * self.scaled_rect.height() / self.pixmap.height()
            
            painter.setPen(QPen(QColor(50, 205, 50), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(QPointF(x1, y1), QPointF(x2, y2)))
        
        # 在图像顶部绘制提示信息
        next_idx = len(self.points)
        if next_idx < len(self.type_names):
            next_name = self.type_names[next_idx]
            hint_text = f"下一个点: {next_name} ({next_idx+1}/{len(self.type_names)})"
            # 绘制半透明背景
            font = QFont("Microsoft YaHei", 12, QFont.Bold)
            painter.setFont(font)
            metrics = QFontMetrics(font)
            text_width = metrics.width(hint_text)
            text_height = metrics.height()
            
            # 在顶部中央绘制提示
            x = (self.width() - text_width) // 2
            y = 30
            
            # 背景
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRect(x - 10, y - text_height - 5, text_width + 20, text_height + 10)
            
            # 文字
            painter.setPen(QColor(255, 215, 0))  # 金色
            painter.drawText(x, y, hint_text)
    
    def update_next_point_hint(self):
        """更新下一个点的提示"""
        next_idx = len(self.points)
        
        if next_idx < len(self.type_names):
            # 获取当前要标注的点名称
            next_name = self.type_names[next_idx]
            
            # 计算进度百分比
            progress = int((next_idx / len(self.type_names)) * 100)
            
            # 获取当前所在的组
            current_group = None
            for group_name, indices in self.KPS_GROUPS.items():
                if next_idx in indices:
                    current_group = group_name
                    break
            
            # 构建提示消息
            hint = f"📍 下一个关键点: {next_name} ({next_idx + 1}/{len(self.type_names)})"
            
            if current_group:
                hint += f"  [部位: {current_group}]"
            
            # 添加进度条效果
            bar_length = 20
            filled = int(bar_length * next_idx / len(self.type_names))
            bar = "█" * filled + "░" * (bar_length - filled)
            hint += f"\n进度: [{bar}] {progress}%"
            
            # 发送提示到父窗口
            self.status_message.emit(hint)
        else:
            self.status_message.emit(f"✅ 所有关键点已完成！共 {len(self.type_names)} 个点")
    
    def show_type_menu(self, global_pos):
        """右键：选择颜色"""
        menu = QMenu(self)
        menu.setTitle("选择关键点颜色")
        
        # 显示当前要标注的点
        next_idx = len(self.points)
        if next_idx < len(self.type_names):
            next_name = self.type_names[next_idx]
            menu.setTitle(f"添加: {next_name} (第{next_idx+1}/{len(self.type_names)}点)")
        
        red_action = menu.addAction("🔴 红色 (左键)")
        red_action.setData('red')
        
        blue_action = menu.addAction("🔵 蓝色 (右键)")
        blue_action.setData('blue')
        
        action = menu.exec_(global_pos)
        if action and self.pending_click:
            color = action.data()
            self.add_kps_point(self.pending_click, color)
            self.pending_click = None
    
    def add_kps_point(self, screen_pos, color):
        """添加关键点"""
        orig_pos = self.screen_to_original(screen_pos)
        if not orig_pos:
            return
        
        if len(self.points) >= len(self.type_names):
            QMessageBox.warning(self, "提示", f"最多只能标注 {len(self.type_names)} 个关键点")
            return
        
        next_idx = len(self.points)
        next_name = self.type_names[next_idx]
        
        self.points.append({
            'i': self.next_id,
            'x': orig_pos.x(),
            'y': orig_pos.y(),
            'type': next_name,
            'type_index': next_idx,
            'color': color
        })
        self.next_id += 1
        
        # 更新提示
        self.update_next_point_hint()
        self.update_display()
        self.annotation_changed.emit()
        
        # 显示添加成功的消息
        self.status_message.emit(f"✓ 已添加 {next_name} ({len(self.points)}/{len(self.type_names)})")
    
    def show_rect_type_menu(self):
        """矩形框添加"""
        x1 = min(self.rect_start.x(), self.rect_end.x())
        y1 = min(self.rect_start.y(), self.rect_end.y())
        x2 = max(self.rect_start.x(), self.rect_end.x())
        y2 = max(self.rect_start.y(), self.rect_end.y())
        
        self.rectangles.append({
            'i': self.next_id,
            'x': x1,
            'y': y1,
            'w': x2 - x1,
            'h': y2 - y1,
            'type': 'body',
            'type_index': 0
        })
        self.next_id += 1
        self.drawing_rect = False
        self.update_display()
        self.annotation_changed.emit()
        self.status_message.emit("✓ 已添加身体区域矩形框")
    
    def find_point_at(self, screen_pos):
        """查找点击的点"""
        for i, point in enumerate(self.points):
            screen = self.original_to_screen(QPoint(point['x'], point['y']))
            if screen and abs(screen.x() - screen_pos.x()) < 12 and \
               abs(screen.y() - screen_pos.y()) < 12:
                return i
        return -1
    
    def find_rect_at(self, screen_pos):
        """查找矩形框"""
        for i, rect in enumerate(self.rectangles):
            x1 = self.scaled_rect.x() + rect['x'] * self.scaled_rect.width() / self.pixmap.width()
            y1 = self.scaled_rect.y() + rect['y'] * self.scaled_rect.height() / self.pixmap.height()
            x2 = x1 + rect['w'] * self.scaled_rect.width() / self.pixmap.width()
            y2 = y1 + rect['h'] * self.scaled_rect.height() / self.pixmap.height()
            
            if x1 <= screen_pos.x() <= x2 and y1 <= screen_pos.y() <= y2:
                return i
        return -1
    
    def update_point_position(self, index, orig_pos):
        """更新关键点位置"""
        if 0 <= index < len(self.points):
            self.points[index]['x'] = orig_pos.x()
            self.points[index]['y'] = orig_pos.y()
            self.update_display()
            self.annotation_changed.emit()
    
    def add_point_annotation(self, orig_pos):
        """默认添加红色点（左键点击）"""
        if len(self.points) < len(self.type_names):
            self.add_kps_point(self.original_to_screen(orig_pos), 'red')
    
    def delete_selected(self):
        """删除最后一个点"""
        if self.points:
            deleted = self.points.pop()
            self.update_next_point_hint()
            self.update_display()
            self.annotation_changed.emit()
            self.status_message.emit(f"🗑 已删除 {deleted.get('type', '点')}")
            return True
        return False
    
    def mouseDoubleClickEvent(self, event):
        """双击切换颜色"""
        idx = self.find_point_at(event.pos())
        if idx != -1:
            point = self.points[idx]
            old_color = point.get('color', 'red')
            new_color = 'blue' if old_color == 'red' else 'red'
            point['color'] = new_color
            self.update_display()
            self.annotation_changed.emit()
            color_name = "蓝色" if new_color == 'blue' else "红色"
            self.status_message.emit(f"✓ 已将点 {idx+1} 切换为{color_name}")
    
    def get_progress_text(self):
        """获取进度文本"""
        return f"{len(self.points)}/{len(self.type_names)}"