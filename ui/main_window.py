from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTreeView, QListWidget, QLabel, QPushButton, 
                            QSpinBox, QComboBox, QGridLayout, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from core.file_manager import FileManager
from core.animation_merger import AnimationMerger
from ui.preview_window import PreviewWindow
from core.image_processor import ImageProcessor
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("序列帧动画预览工具")
        self.setGeometry(100, 100, 1400, 800)
        
        # 初始化核心组件
        self.file_manager = FileManager()
        self.animation_merger = AnimationMerger()
        self.image_processor = ImageProcessor()
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI组件"""
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建水平布局
        layout = QHBoxLayout(main_widget)
        layout.setSpacing(10)
        
        # 添加左侧面板
        self.setup_left_panel(layout)
        # 添加中间面板
        self.setup_middle_panel(layout)
        # 添加右侧面板
        self.setup_right_panel(layout)
        
        # 初始化动画相关变量
        self.setup_animation_variables()
        
    def setup_left_panel(self, parent_layout):
        """设置左侧文件浏览面板"""
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 文件夹浏览器
        self.folder_tree = self.file_manager.create_folder_tree()
        
        layout.addWidget(QLabel("文件夹:"))
        layout.addWidget(self.folder_tree)
        
        parent_layout.addWidget(left_panel)
        
    def setup_middle_panel(self, parent_layout):
        """设置中间动画列表面板"""
        middle_panel = QWidget()
        layout = QVBoxLayout(middle_panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建动画列表
        anim_label = QLabel("动画文件:")
        self.animation_list = QListWidget()
        self.animation_list.setStyleSheet("border: 1px solid #cccccc;")
        self.animation_list.setFixedWidth(200)  # 固定宽度
        
        layout.addWidget(anim_label)
        layout.addWidget(self.animation_list)
        
        parent_layout.addWidget(middle_panel)
        
    def setup_right_panel(self, parent_layout):
        """设置右侧预览面板"""
        right_panel = QWidget()
        layout = QVBoxLayout(right_panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建预览区域
        preview_label = QLabel("预览:")
        
        # 创滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建预览容器
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建预览窗口的容器
        self.preview_container = QWidget()
        self.preview_grid = QGridLayout(self.preview_container)
        self.preview_grid.setSpacing(20)
        self.preview_layout.addWidget(self.preview_container)
        
        # 将预览容器添加到滚动区域
        scroll_area.setWidget(self.preview_widget)
        
        # 添加到右侧面板
        layout.addWidget(preview_label)
        layout.addWidget(scroll_area)
        
        # 创建控制按钮区域
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        self.play_button = QPushButton("播放")
        fps_label = QLabel("帧率:")
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 60)
        self.fps_spinbox.setValue(12)
        
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(fps_label)
        control_layout.addWidget(self.fps_spinbox)
        
        layout.addWidget(control_widget)
        
        parent_layout.addWidget(right_panel, stretch=3)  # 预览区域占更多空间
        
    def setup_animation_variables(self):
        """初始化动画相关变量"""
        self.current_frames = []
        self.current_frame_index = 0
        self.animation_timer = QTimer()
        self.preview_windows = []
        
    def setup_connections(self):
        """设置信号连接"""
        self.folder_tree.clicked.connect(self.on_folder_selected)
        self.animation_list.itemClicked.connect(self.on_animation_selected)
        self.play_button.clicked.connect(self.toggle_animation)
        self.fps_spinbox.valueChanged.connect(self.update_fps)
        self.animation_timer.timeout.connect(self.update_animation_frame)
        
    def on_folder_selected(self, index):
        """处理文件夹选择事件"""
        path = self.file_manager.folder_model.filePath(index)
        
        # 保存当前位置
        self.file_manager.save_last_position(path)
        
        self.animation_list.clear()
        
        # 获取动画文件列表
        plist_files = self.file_manager.get_animation_files(path)
        
        if not plist_files:
            self.animation_list.addItem("没有找到有效的动画文件")
            return
        
        # 添加到列表并选中第一个
        self.animation_list.addItems(plist_files)
        self.animation_list.setCurrentRow(0)
        first_item = self.animation_list.item(0)
        if first_item:
            self.on_animation_selected(first_item)

    def on_animation_selected(self, item):
        """处理动画选择事件"""
        # 检查是否是错误消息
        if item.text().startswith("没有找到") or item.text().startswith("加载文件夹出错"):
            return
            
        # 获取文件路径
        folder_index = self.folder_tree.currentIndex()
        folder_path = self.file_manager.folder_model.filePath(folder_index)
        plist_path = os.path.join(folder_path, item.text())
        
        # 加载动画文件
        frames_dict, sprite_sheet, animation_groups = self.file_manager.load_animation_file(plist_path)
        if not all([frames_dict, sprite_sheet, animation_groups]):
            return
            
        # 清除现有的预览窗口
        for window in self.preview_windows:
            window['container'].setParent(None)
        self.preview_windows.clear()
        
        # 创建新的预览窗口
        self.create_preview_windows(animation_groups, frames_dict, sprite_sheet)
        
        # 开始播放动画
        interval = int(1000 / self.fps_spinbox.value())
        self.animation_timer.start(interval)
        self.play_button.setText("暂停")

    def create_preview_windows(self, animation_groups, frames_dict, sprite_sheet):
        """创建预览窗口"""
        # 计算网格布局
        num_animations = len(animation_groups)
        cols = 2  # 固定为2列
        rows = (num_animations + cols - 1) // cols
        
        # 设置预览容器的固定宽度
        container_width = 900  # 适合两列布局
        self.preview_container.setFixedWidth(container_width)
        
        # 计算每个预览窗口的固定大小
        preview_size = (container_width - 60) // 2  # 减去间距后平分宽度
        
        # 为每个动画序列创建预览窗口
        for i, (anim_name, frame_names) in enumerate(sorted(animation_groups.items())):
            # 创建预览窗口容器
            container = QWidget()
            container.setFixedSize(preview_size, preview_size + 40)
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(5)
            container_layout.setContentsMargins(5, 5, 5, 5)
            
            # 创建预览标签
            preview_label = QLabel()
            preview_label.setFixedSize(preview_size - 10, preview_size - 45)
            preview_label.setAlignment(Qt.AlignCenter)
            preview_label.setStyleSheet("border: 1px solid #cccccc;")
            
            # 创建名称标签
            name_label = QLabel(anim_name)
            name_label.setAlignment(Qt.AlignCenter)
            
            # 创建信息标签
            info_label = QLabel()
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("color: #666666; font-size: 10px;")
            
            # 解析动画帧
            frames = self.animation_merger.parse_animation_frames(frames_dict, frame_names)
            
            # 添加双击事件
            preview_label.mouseDoubleClickEvent = lambda event, name=anim_name, frames=frames, sheet=sprite_sheet: \
                self.show_single_preview(name, frames, sheet)
            
            container_layout.addWidget(preview_label)
            container_layout.addWidget(name_label)
            container_layout.addWidget(info_label)
            
            # 添加到网格布局
            row = i // cols
            col = i % cols
            self.preview_grid.addWidget(container, row, col, Qt.AlignCenter)
            
            # 保存预览窗口信息
            self.preview_windows.append({
                'container': container,
                'label': preview_label,
                'name_label': name_label,
                'info_label': info_label,
                'frame_index': 0,
                'frames': frames,
                'sprite_sheet': sprite_sheet
            })
            
            # 更新信息标签
            if frames:
                source_size = frames[0]['source_size']
                info_text = f"尺寸: {source_size[0]}x{source_size[1]} | 帧数: {len(frames)}"
                info_label.setText(info_text)

    def show_single_preview(self, anim_name, frames, sprite_sheet):
        """显示单个动画的预览窗口"""
        preview_window = PreviewWindow(
            parent=self,
            animation_data={
                'name': anim_name,
                'frames': frames,
                'sprite_sheet': sprite_sheet,
                'fps': self.fps_spinbox.value()
            }
        )
        preview_window.show()

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

    def update_animation_frame(self):
        """更新动画帧"""
        for window in self.preview_windows:
            if not window['frames'] or not window['sprite_sheet']:
                continue
                
            try:
                frame_data = window['frames'][window['frame_index']]
                
                # 处理当前帧
                frame_image = self.image_processor.process_frame(frame_data, window['sprite_sheet'])
                if frame_image:
                    # 转换为QPixmap并显示
                    pixmap = self.image_processor.pil_to_pixmap(
                        frame_image,
                        window['label'].size()
                    )
                    if pixmap:
                        window['label'].setPixmap(pixmap)
                
                # 更新帧引
                window['frame_index'] = (window['frame_index'] + 1) % len(window['frames'])
                
            except Exception as e:
                print(f"Error updating frame: {str(e)}")