from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QSpinBox)
from PyQt5.QtCore import Qt, QTimer
from core.image_processor import ImageProcessor

class PreviewWindow(QMainWindow):
    def __init__(self, parent=None, animation_data=None):
        super().__init__(parent)
        self.animation_data = animation_data
        self.image_processor = ImageProcessor()
        
        # 初始化变量
        self.current_frame_index = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_frame)
        
        self.setup_ui()
        self.setup_animation()
        
    def setup_ui(self):
        """设置预览窗口UI"""
        # 设置窗口标题和大小
        self.setWindowTitle(f"预览 - {self.animation_data['name']}")
        window_size = 500
        self.setFixedSize(window_size, window_size + 100)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建预览标签
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(window_size - 40, window_size - 40)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #cccccc;")
        layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)
        
        # 创建控制区域
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(50, 10, 50, 10)
        
        # 播放按钮
        self.play_button = QPushButton("暂停")
        self.play_button.clicked.connect(self.toggle_animation)
        
        # 帧率控制
        fps_label = QLabel("帧率:")
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 60)
        self.fps_spinbox.setValue(self.animation_data['fps'])
        self.fps_spinbox.valueChanged.connect(self.update_fps)
        
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(fps_label)
        control_layout.addWidget(self.fps_spinbox)
        layout.addWidget(control_widget)
        
        # 创建信息标签
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.info_label)
        
        # 更新信息标签
        if self.animation_data['frames']:
            first_frame = self.animation_data['frames'][0]
            source_size = first_frame['source_size']
            frame_count = len(self.animation_data['frames'])
            info_text = f"尺寸: {source_size[0]}x{source_size[1]} | 帧数: {frame_count}"
            self.info_label.setText(info_text)
    
    def setup_animation(self):
        """设置动画播放"""
        # 预先缓存所有帧
        self.cached_frames = []
        for frame_data in self.animation_data['frames']:
            try:
                # 处理帧
                frame_image = self.image_processor.process_frame(
                    frame_data,
                    self.animation_data['sprite_sheet']
                )
                
                if frame_image:
                    # 转换为QPixmap
                    pixmap = self.image_processor.pil_to_pixmap(
                        frame_image,
                        self.preview_label.size()
                    )
                    if pixmap:
                        self.cached_frames.append(pixmap)
                
            except Exception as e:
                print(f"Error caching frame: {str(e)}")
                self.cached_frames.append(None)
        
        # 显示第一帧
        if self.cached_frames:
            self.preview_label.setPixmap(self.cached_frames[0])
        
        # 开始播放动画
        interval = int(1000 / self.fps_spinbox.value())
        self.animation_timer.start(interval)
    
    def update_frame(self):
        """更新当前帧"""
        if self.cached_frames and self.current_frame_index < len(self.cached_frames):
            pixmap = self.cached_frames[self.current_frame_index]
            if pixmap:
                self.preview_label.setPixmap(pixmap)
            self.current_frame_index = (self.current_frame_index + 1) % len(self.cached_frames)
    
    def toggle_animation(self):
        """切换动画播放状态"""
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            self.play_button.setText("播放")
        else:
            interval = int(1000 / self.fps_spinbox.value())
            self.animation_timer.start(interval)
            self.play_button.setText("暂停")
    
    def update_fps(self, value):
        """更新帧率"""
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            interval = int(1000 / value)
            self.animation_timer.start(interval)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.animation_timer.stop()
        super().closeEvent(event)