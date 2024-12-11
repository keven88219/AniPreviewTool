from PyQt5.QtWidgets import QTreeView, QFileSystemModel
from PyQt5.QtCore import QDir, QModelIndex
import os
import json
import plistlib
from PIL import Image

class FileManager:
    def __init__(self):
        self.folder_model = QFileSystemModel()
        self.setup_model()
        self.tree = None
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        
    def setup_model(self):
        """设置文件系统模型"""
        root_dir = QDir.rootPath()
        self.folder_model.setRootPath(root_dir)
        
    def create_folder_tree(self):
        """创建文件夹树视图"""
        self.tree = QTreeView()
        self.tree.setModel(self.folder_model)
        
        # 设置根目录
        root_dir = QDir.rootPath()
        self.tree.setRootIndex(self.folder_model.index(root_dir))
        
        # 设置列宽和显示
        self.tree.setColumnWidth(0, 300)
        self.tree.setMinimumWidth(350)
        
        # 只显示文件夹名称列
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        
        # 恢复上次的位置
        last_path = self.load_last_position()
        if last_path and os.path.exists(last_path):
            index = self.folder_model.index(last_path)
            self.tree.setCurrentIndex(index)
            self.tree.scrollTo(index)
            # 展开到当前位置的路径
            parent = index.parent()
            while parent.isValid():
                self.tree.expand(parent)
                parent = parent.parent()
        
        return self.tree
    
    def load_last_position(self):
        """加载上次的位置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('last_position')
        except Exception as e:
            print(f"Error loading last position: {str(e)}")
        return None
    
    def save_last_position(self, path):
        """保存当前位置"""
        try:
            config = {'last_position': path}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving last position: {str(e)}")
    
    def get_animation_files(self, folder_path):
        """获取文件夹中的动画文件"""
        try:
            files = os.listdir(folder_path)
            plist_files = []
            
            # 检查每个plist文件是否有对应的png文件
            for f in files:
                if f.endswith('.plist'):
                    png_file = f.replace('.plist', '.png')
                    if png_file in files:
                        plist_files.append(f)
            
            return sorted(plist_files)
        except Exception as e:
            print(f"Error getting animation files: {str(e)}")
            return []
    
    def load_animation_file(self, plist_path):
        """加载动画文件，支持新旧两种格式"""
        try:
            png_path = plist_path.replace('.plist', '.png')
            
            # 检查文件是否存在
            if not os.path.exists(plist_path) or not os.path.exists(png_path):
                return None, None, None
            
            # 加载plist文件
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
            
            # 加载PNG文件
            sprite_sheet = Image.open(png_path).convert('RGBA')
            
            # 解析plist数据
            frames_dict = plist_data.get('frames', {})
            
            # 按动画序列分组
            animation_groups = {}
            converted_frames = {}
            
            for frame_name, frame_data in frames_dict.items():
                try:
                    # 基本帧数据
                    frame_dict = {
                        'source_size': [500, 500],  # 默认值
                        'offset': [0, 0],           # 默认值
                        'rotated': False,           # 默认值
                        'rect': [0, 0, 1, 1]        # 默认值
                    }
                    
                    # 检测是否是新版格式
                    is_new_format = 'textureRect' in frame_data or 'spriteSize' in frame_data
                    
                    if is_new_format:
                        # 新版格式解析
                        # 解析源尺寸 (spriteSourceSize 或 spriteSize)
                        size_str = None
                        if 'spriteSourceSize' in frame_data:
                            size_str = frame_data['spriteSourceSize']
                        elif 'spriteSize' in frame_data:
                            size_str = frame_data['spriteSize']
                            
                        if size_str and isinstance(size_str, str):
                            size_str = size_str.replace('{', '').replace('}', '')
                            parts = [x.strip() for x in size_str.split(',')]
                            if len(parts) == 2 and all(parts):
                                try:
                                    frame_dict['source_size'] = [int(float(x)) for x in parts]
                                except ValueError:
                                    pass
                        
                        # 解析偏移 (spriteOffset)
                        if 'spriteOffset' in frame_data:
                            offset_str = frame_data['spriteOffset']
                            if offset_str and isinstance(offset_str, str):
                                offset_str = offset_str.replace('{', '').replace('}', '')
                                parts = [x.strip() for x in offset_str.split(',')]
                                if len(parts) == 2 and all(parts):
                                    try:
                                        frame_dict['offset'] = [int(float(x)) for x in parts]
                                    except ValueError:
                                        pass
                        
                        # 解析矩形区域 (textureRect)
                        if 'textureRect' in frame_data:
                            rect_str = frame_data['textureRect']
                            if rect_str and isinstance(rect_str, str):
                                rect_str = rect_str.replace('{{', '').replace('}}', '').replace('},{', ',')
                                parts = [x.strip() for x in rect_str.split(',')]
                                if len(parts) == 4 and all(parts):
                                    try:
                                        frame_dict['rect'] = [int(float(x)) for x in parts]
                                    except ValueError:
                                        pass
                        
                        # 解析旋转 (textureRotated)
                        if 'textureRotated' in frame_data:
                            frame_dict['rotated'] = bool(frame_data['textureRotated'])
                    
                    else:
                        # 旧版格式解析
                        # 解析frame
                        frame_str = frame_data.get('frame', '')
                        if isinstance(frame_str, str):
                            frame_str = frame_str.replace('{', '').replace('}', '')
                            parts = [x.strip() for x in frame_str.split(',')]
                            if len(parts) == 4 and all(parts):
                                try:
                                    frame_dict['rect'] = [int(float(x)) for x in parts]
                                except ValueError:
                                    pass
                        
                        # 解析源尺寸
                        source_size = frame_data.get('sourceSize', '')
                        if isinstance(source_size, str):
                            source_size = source_size.replace('{', '').replace('}', '')
                            parts = [x.strip() for x in source_size.split(',')]
                            if len(parts) == 2 and all(parts):
                                try:
                                    frame_dict['source_size'] = [int(float(x)) for x in parts]
                                except ValueError:
                                    pass
                        
                        # 解析偏移
                        offset = frame_data.get('offset', '')
                        if isinstance(offset, str):
                            offset = offset.replace('{', '').replace('}', '')
                            parts = [x.strip() for x in offset.split(',')]
                            if len(parts) == 2 and all(parts):
                                try:
                                    frame_dict['offset'] = [int(float(x)) for x in parts]
                                except ValueError:
                                    pass
                        
                        # 解析旋转
                        frame_dict['rotated'] = frame_data.get('rotated', False)
                    
                    converted_frames[frame_name] = frame_dict
                    
                    # 添加到动画组
                    base_name = frame_name.rsplit('.', 1)[0]
                    base_name = '_'.join(base_name.split('_')[:-1])
                    if base_name not in animation_groups:
                        animation_groups[base_name] = []
                    animation_groups[base_name].append(frame_name)
                    
                except Exception as e:
                    print(f"Warning: Using default values for frame {frame_name}")
                    converted_frames[frame_name] = {
                        'source_size': [500, 500],
                        'offset': [0, 0],
                        'rotated': False,
                        'rect': [0, 0, 1, 1]
                    }
            
            # 对每个动画组内的帧按序号排序
            for group in animation_groups.values():
                group.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
            
            return converted_frames, sprite_sheet, animation_groups
            
        except Exception as e:
            print(f"Error loading animation file: {str(e)}")
            print(f"File path: {plist_path}")
            import traceback
            traceback.print_exc()
            return None, None, None