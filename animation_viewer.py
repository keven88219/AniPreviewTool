import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTreeView, QListWidget, QLabel, 
                            QPushButton, QFileSystemModel, QSpinBox, QComboBox, QGridLayout, QScrollArea)
from PyQt5.QtCore import Qt, QDir, QTimer
from PyQt5.QtGui import QPixmap, QImage
import plistlib
from PIL import Image
import numpy as np

class AnimationViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("序列帧动画预览工具")
        self.setGeometry(100, 100, 1400, 800)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建水平布局
        layout = QHBoxLayout(main_widget)
        layout.setSpacing(10)
        
        # 创建左侧文件夹面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建文件夹浏览器
        folder_label = QLabel("文件夹:")
        self.folder_tree = QTreeView()
        self.folder_model = QFileSystemModel()
        
        # 设置根目录
        root_dir = QDir.rootPath()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.folder_model.setRootPath(root_dir)
        self.folder_tree.setModel(self.folder_model)
        self.folder_tree.setRootIndex(self.folder_model.index(current_dir))
        
        # 设置列宽和显示
        self.folder_tree.setColumnWidth(0, 300)  # 设置第一列（文件名）的宽度为300像素
        self.folder_tree.setMinimumWidth(350)    # 设置整个树视图的最小宽度
        
        # 只显示文件夹名称列
        self.folder_tree.setColumnHidden(1, True)
        self.folder_tree.setColumnHidden(2, True)
        self.folder_tree.setColumnHidden(3, True)
        
        # 添加一个"返回根目录"按钮
        root_button = QPushButton("返回根目录")
        root_button.clicked.connect(self.goto_root_directory)
        
        # 添加到布局
        left_layout.addWidget(folder_label)
        left_layout.addWidget(root_button)
        left_layout.addWidget(self.folder_tree)
        
        # 创建中间动画列表面板
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建动画列表
        anim_label = QLabel("动画文件:")
        self.animation_list = QListWidget()
        self.animation_list.setStyleSheet("border: 1px solid #cccccc;")
        self.animation_list.setFixedWidth(200)  # 固定宽度
        
        middle_layout.addWidget(anim_label)
        middle_layout.addWidget(self.animation_list)
        
        # 创建右侧预览面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建预览区域
        preview_label = QLabel("预览:")
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建预览容器
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建预览窗��的容器
        self.preview_container = QWidget()
        self.preview_grid = QGridLayout(self.preview_container)
        self.preview_grid.setSpacing(20)
        self.preview_layout.addWidget(self.preview_container)
        
        # 将预览容器添加到滚动区域
        scroll_area.setWidget(self.preview_widget)
        
        # 添加到右侧面板
        right_layout.addWidget(preview_label)
        right_layout.addWidget(scroll_area)
        
        # 创建控制按钮区域
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        self.play_button = QPushButton("播放")
        fps_label = QLabel("帧率:")
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 60)
        self.fps_spinbox.setValue(12)
        self.fps_spinbox.valueChanged.connect(self.update_fps)
        
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(fps_label)
        control_layout.addWidget(self.fps_spinbox)
        
        right_layout.addWidget(control_widget)
        
        # 添加到主布局，调整比例
        layout.addWidget(left_panel)
        layout.addWidget(middle_panel)
        layout.addWidget(right_panel, stretch=3)  # 预览区域占更多空间
        
        # 设置动画播放相关变量
        self.current_frames = []
        self.current_frame_index = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation_frame)
        
        # 连接信号
        self.folder_tree.clicked.connect(self.on_folder_selected)
        self.animation_list.itemClicked.connect(self.on_animation_selected)
        self.play_button.clicked.connect(self.toggle_animation)
        
        # 添加新的成员变量
        self.sprite_sheet = None
        self.frame_rects = []
        self.current_png = None
        
        # 添加预览窗口列表
        self.preview_windows = []
        
    def on_folder_selected(self, index):
        path = self.folder_model.filePath(index)
        self.animation_list.clear()
        
        try:
            # 检查是否是文件夹
            if not os.path.isdir(path):
                return
            
            # 获取文件夹中的所有plist文件
            files = os.listdir(path)
            plist_files = []
            
            # 检查每个plist文件是否有对应的png文件
            for f in files:
                if f.endswith('.plist'):
                    png_file = f.replace('.plist', '.png')
                    if png_file in files:
                        plist_files.append(f)
            
            if not plist_files:
                self.animation_list.addItem("没有找到有效的动画文件")
                return
            
            # 按名称排序
            plist_files.sort()
            self.animation_list.addItems(plist_files)
            
            # 选中并播放第一个动画
            self.animation_list.setCurrentRow(0)
            first_item = self.animation_list.item(0)
            if first_item:
                self.on_animation_selected(first_item)
                
        except Exception as e:
            print(f"Error loading folder: {str(e)}")
            self.animation_list.addItem(f"加载文件夹出错: {str(e)}")
    
    def on_animation_selected(self, item):
        # 检查是否是错误消息
        if item.text().startswith("没有找到") or item.text().startswith("加载文件夹出错"):
            return
            
        folder_index = self.folder_tree.currentIndex()
        folder_path = self.folder_model.filePath(folder_index)
        plist_path = os.path.join(folder_path, item.text())
        png_path = plist_path.replace('.plist', '.png')
        
        # 检查文件是否存在
        if not os.path.exists(plist_path) or not os.path.exists(png_path):
            print(f"Missing files: {plist_path} or {png_path}")
            return
        
        self.current_plist_path = plist_path
        
        try:
            # 加载plist文件
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
            
            # 加载对应的PNG文件
            self.current_png = Image.open(png_path).convert('RGBA')
            
            # 解析plist数据
            frames_dict = plist_data.get('frames', {})
            
            # 按动画序列分组
            animation_groups = {}
            for frame_name in frames_dict.keys():
                # 获取基础名称（去掉序号部分）
                base_name = '_'.join(frame_name.split('_')[:-1])  # 去掉最后的序号部分
                if base_name not in animation_groups:
                    animation_groups[base_name] = []
                animation_groups[base_name].append(frame_name)
            
            if not animation_groups:
                print(f"No valid animations found in {plist_path}")
                return
            
            # 对每个动画组内的帧按序号排序
            for group in animation_groups.values():
                group.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
            
            # 创建画选择下框（如果不存）
            if not hasattr(self, 'animation_combo'):
                self.animation_combo = QComboBox()
                self.animation_combo.currentIndexChanged.connect(self.on_animation_type_changed)
                # 在帧率控制之前添加到布局
                self.preview_widget.layout().insertWidget(1, self.animation_combo)
            
            # 更新动画类型列表
            self.animation_combo.clear()
            self.animation_combo.addItems(sorted(animation_groups.keys()))
            
            # 创建预览窗口
            self.create_preview_windows(animation_groups)
            
            # 为每个动画序列解析帧
            for i, (anim_name, frame_names) in enumerate(sorted(animation_groups.items())):
                frames = self.parse_animation_frames(frames_dict, frame_names)
                self.preview_windows[i]['frames'] = frames
                # 更新预览信息
                self.update_preview_info(i)
            
            # 保存数据
            self.animation_groups = animation_groups
            self.current_frames_dict = frames_dict
            
            # 开始播放
            interval = int(1000 / self.fps_spinbox.value())
            self.animation_timer.start(interval)
            self.play_button.setText("暂停")
            
        except Exception as e:
            print(f"Error loading animation: {str(e)}")
            for window in self.preview_windows:
                if window['label']:
                    window['label'].setText(f"Error: {str(e)}")
    
    def parse_animation_frames(self, frames_dict, frame_names):
        """解析指定动画序列的帧，返回帧列表"""
        frames = []
        for frame_name in frame_names:
            try:
                frame_data = frames_dict[frame_name]
                frame_dict = {}
                
                # 解析frame字符串
                frame_str = frame_data.get('frame', '')
                if isinstance(frame_str, str):
                    # 处理字符串格式
                    frame_str = frame_str.replace('{', '').replace('}', '')
                    if frame_str:  # 确保字符串不为空
                        coords = [float(x) for x in frame_str.split(',')]
                    else:
                        continue  # 跳过空字符串
                elif isinstance(frame_str, (list, tuple)):
                    # 处理列表或元组格式
                    coords = list(map(float, frame_str))
                else:
                    print(f"Unsupported frame format for {frame_name}: {frame_str}")
                    continue
                
                if len(coords) != 4:
                    print(f"Invalid coordinates count for {frame_name}: {coords}")
                    continue
                
                frame_dict['rect'] = [int(coords[0]), int(coords[1]), 
                                    int(coords[2]), int(coords[3])]
                
                # 解析旋转信息
                frame_dict['rotated'] = frame_data.get('rotated', False)
                
                # 解析源尺寸
                source_size = frame_data.get('sourceSize', '')
                if isinstance(source_size, str):
                    source_size = source_size.replace('{', '').replace('}', '')
                    if source_size:
                        source_size = [int(float(x)) for x in source_size.split(',')]
                    else:
                        source_size = [100, 100]  # 默认尺寸
                elif isinstance(source_size, (list, tuple)):
                    source_size = list(map(int, source_size))
                else:
                    source_size = [100, 100]  # 默认尺寸
                frame_dict['source_size'] = source_size
                
                # 解析偏移
                offset = frame_data.get('offset', '')
                if isinstance(offset, str):
                    offset = offset.replace('{', '').replace('}', '')
                    if offset:
                        offset = [float(x) for x in offset.split(',')]
                    else:
                        offset = [0, 0]  # 默认无偏移
                elif isinstance(offset, (list, tuple)):
                    offset = list(map(float, offset))
                else:
                    offset = [0, 0]  # 默认无偏移
                frame_dict['offset'] = [int(offset[0]), int(offset[1])]
                
                frames.append(frame_dict)
                
            except Exception as e:
                print(f"Error parsing frame {frame_name}: {str(e)}")
                continue
        
        return frames
    
    def on_animation_type_changed(self, index):
        """当选择不同的动画序列时调"""
        if hasattr(self, 'animation_groups'):
            anim_type = self.animation_combo.currentText()
            if anim_type in self.animation_groups:
                # 停止当前动画
                self.animation_timer.stop()
                # 使用已保存的frames_dict
                self.parse_animation_frames(self.current_frames_dict, 
                                         self.animation_groups[anim_type])
    
    def update_animation_frame(self):
        """更新所有预览口的帧"""
        if not self.current_png:
            return
            
        for window in self.preview_windows:
            if not window['frames']:
                continue
                
            try:
                frame_data = window['frames'][window['frame_index']]
                
                # 从sprite sheet中裁剪出当前帧
                if frame_data['rotated']:
                    frame_image = self.current_png.crop((frame_data['rect'][0], frame_data['rect'][1], 
                                                        frame_data['rect'][0] + frame_data['rect'][3], 
                                                        frame_data['rect'][1] + frame_data['rect'][2]))
                    frame_image = frame_image.transpose(Image.ROTATE_90)
                else:
                    frame_image = self.current_png.crop((frame_data['rect'][0], frame_data['rect'][1], 
                                                        frame_data['rect'][0] + frame_data['rect'][2], 
                                                        frame_data['rect'][1] + frame_data['rect'][3]))
                
                # 创建目标图像
                source_w, source_h = frame_data['source_size']
                final_image = Image.new('RGBA', (source_w, source_h), (0, 0, 0, 0))
                
                # 计算粘贴位置
                offset_x, offset_y = frame_data['offset']
                paste_x = int((source_w - frame_image.width) / 2 + offset_x)
                paste_y = int((source_h - frame_image.height) / 2 - offset_y)
                
                # 粘贴到最终图像
                final_image.paste(frame_image, (paste_x, paste_y), frame_image)
                
                # 转换为QPixmap并显示
                frame_array = np.array(final_image)
                height, width, channel = frame_array.shape
                bytes_per_line = channel * width
                
                q_image = QImage(frame_array.data, width, height, bytes_per_line, 
                               QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(q_image)
                
                # 根据预览区域大小缩放
                scaled_pixmap = pixmap.scaled(window['label'].size(), 
                                            Qt.KeepAspectRatio, 
                                            Qt.SmoothTransformation)
                
                # 更新预览窗口
                window['label'].setPixmap(scaled_pixmap)
                
                # 更新帧索引
                window['frame_index'] = (window['frame_index'] + 1) % len(window['frames'])
                
            except Exception as e:
                print(f"Error displaying frame: {str(e)}")
    
    def toggle_animation(self):
        """切换所有动画的播放状态"""
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            self.play_button.setText("播放")
        else:
            interval = int(1000 / self.fps_spinbox.value())
            self.animation_timer.start(interval)
            self.play_button.setText("暂停")

    def update_fps(self):
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            interval = int(1000 / self.fps_spinbox.value())  # 将帧率换为毫秒间隔
            self.animation_timer.start(interval)
            
    def create_preview_windows(self, animation_groups):
        """创建览窗口"""
        # 清除现有的预览窗口
        for window in self.preview_windows:
            window['container'].setParent(None)
        self.preview_windows.clear()
        
        # 计算网格布局
        num_animations = len(animation_groups)
        cols = 2  # 固定为2列
        rows = (num_animations + cols - 1) // cols
        
        # 设置预览容器的固定宽度
        container_width = 900  # 适两列画
        self.preview_container.setFixedWidth(container_width)
        
        # 计算每个预览窗口的固定大小
        preview_size = (container_width - 60) // 2  # 减去间距后平分宽度
        
        # 创建新的预览窗口
        for i, anim_name in enumerate(sorted(animation_groups.keys())):
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
            
            # 添加双击事件
            preview_label.mouseDoubleClickEvent = lambda event, name=anim_name, index=i: self.show_single_preview(name, index)
            
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
                'frames': []
            })

    def update_preview_info(self, window_index):
        """更预览窗口的信息"""
        if window_index < len(self.preview_windows):
            window = self.preview_windows[window_index]
            frames = window['frames']
            if frames:
                # 获取第一帧的尺寸信息
                first_frame = frames[0]
                source_size = first_frame['source_size']
                frame_count = len(frames)
                
                # 更新信息标签
                info_text = f"尺寸: {source_size[0]}x{source_size[1]} | 帧数: {frame_count}"
                window['info_label'].setText(info_text)

    def show_single_preview(self, anim_name, index):
        """显示单动画的预览窗口"""
        preview_window = QMainWindow(self)
        preview_window.setWindowTitle(f"预览 - {anim_name}")
        
        # 固定大小的正方形窗口
        window_size = 500
        preview_window.setFixedSize(window_size, window_size + 100)  # 100是控制区域的高度
        
        # 创建中央部件
        central_widget = QWidget()
        preview_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建预览标签
        preview_label = QLabel()
        preview_label.setFixedSize(window_size - 40, window_size - 40)  # 减去边距
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet("border: 1px solid #cccccc;")
        layout.addWidget(preview_label, alignment=Qt.AlignCenter)
        
        # 创建控制按钮
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(50, 10, 50, 10)
        
        play_button = QPushButton("播放")
        fps_label = QLabel("帧率:")
        fps_spinbox = QSpinBox()
        fps_spinbox.setRange(1, 60)
        fps_spinbox.setValue(self.fps_spinbox.value())
        
        control_layout.addWidget(play_button)
        control_layout.addWidget(fps_label)
        control_layout.addWidget(fps_spinbox)
        layout.addWidget(control_widget)
        
        # 创建信息标签
        info_label = QLabel()
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #666666;")
        
        # 获取并显示信息
        frames = self.preview_windows[index]['frames']
        if frames:
            first_frame = frames[0]
            source_size = first_frame['source_size']
            frame_count = len(frames)
            info_text = f"尺寸: {source_size[0]}x{source_size[1]} | 帧数: {frame_count}"
            info_label.setText(info_text)
        
        layout.addWidget(info_label)
        
        # 创建动画计时器
        timer = QTimer()
        frame_index = 0
        frames = self.preview_windows[index]['frames']
        
        # 预先生成所有帧的图像
        cached_frames = []
        for frame_data in frames:
            try:
                if frame_data['rotated']:
                    frame_image = self.current_png.crop((
                        frame_data['rect'][0],
                        frame_data['rect'][1],
                        frame_data['rect'][0] + frame_data['rect'][3],
                        frame_data['rect'][1] + frame_data['rect'][2]
                    ))
                    frame_image = frame_image.transpose(Image.ROTATE_90)
                else:
                    frame_image = self.current_png.crop((
                        frame_data['rect'][0],
                        frame_data['rect'][1],
                        frame_data['rect'][0] + frame_data['rect'][2],
                        frame_data['rect'][1] + frame_data['rect'][3]
                    ))
                
                source_w, source_h = frame_data['source_size']
                final_image = Image.new('RGBA', (source_w, source_h), (0, 0, 0, 0))
                
                offset_x, offset_y = frame_data['offset']
                paste_x = int((source_w - frame_image.width) / 2 + offset_x)
                paste_y = int((source_h - frame_image.height) / 2 - offset_y)
                
                final_image.paste(frame_image, (paste_x, paste_y), frame_image)
                
                # 转换为固定大小的QPixmap
                frame_array = np.array(final_image)
                height, width, channel = frame_array.shape
                bytes_per_line = channel * width
                
                q_image = QImage(frame_array.data, width, height, bytes_per_line, 
                               QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(q_image)
                
                # 缩放到固定大小
                scaled_pixmap = pixmap.scaled(
                    preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                cached_frames.append(scaled_pixmap)
                
            except Exception as e:
                print(f"Error preparing frame: {str(e)}")
                cached_frames.append(None)
        
        def update_frame():
            nonlocal frame_index
            if cached_frames and frame_index < len(cached_frames):
                pixmap = cached_frames[frame_index]
                if pixmap:
                    preview_label.setPixmap(pixmap)
                frame_index = (frame_index + 1) % len(cached_frames)
        
        def toggle_animation():
            if timer.isActive():
                timer.stop()
                play_button.setText("播放")
            else:
                interval = int(1000 / fps_spinbox.value())
                timer.start(interval)
                play_button.setText("暂停")
        
        def update_fps(value):
            if timer.isActive():
                timer.stop()
                interval = int(1000 / value)
                timer.start(interval)
        
        # 连接信号
        timer.timeout.connect(update_frame)
        play_button.clicked.connect(toggle_animation)
        fps_spinbox.valueChanged.connect(update_fps)
        
        # 显示第一帧
        if cached_frames:
            preview_label.setPixmap(cached_frames[0])
        
        # 显示窗口并开始播放
        preview_window.show()
        toggle_animation()

    def goto_root_directory(self):
        """返回到根目录"""
        root_index = self.folder_model.index(QDir.rootPath())
        self.folder_tree.setRootIndex(root_index)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = AnimationViewer()
    viewer.show()
    sys.exit(app.exec_()) 