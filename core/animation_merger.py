from PIL import Image
import numpy as np
from core.image_processor import ImageProcessor

class AnimationMerger:
    def __init__(self):
        self.current_frames = []
        self.current_frame_index = 0
        self.image_processor = ImageProcessor()
        
    def parse_animation_frames(self, frames_dict, frame_names):
        """解析指定动画序列的帧"""
        frames = []
        for frame_name in frame_names:
            try:
                frame_data = frames_dict[frame_name]
                frame_dict = {}
                
                # 直接使用已经转换好的数据
                frame_dict['rect'] = frame_data.get('rect', [0, 0, 1, 1])
                frame_dict['rotated'] = frame_data.get('rotated', False)
                frame_dict['source_size'] = frame_data.get('source_size', [500, 500])
                frame_dict['offset'] = frame_data.get('offset', [0, 0])
                
                frames.append(frame_dict)
                
            except Exception as e:
                print(f"Warning: Using default values for frame {frame_name}")
                frames.append({
                    'source_size': [500, 500],
                    'offset': [0, 0],
                    'rotated': False,
                    'rect': [0, 0, 1, 1]
                })
        
        return frames
    
    def merge_animation_frames(self, frame_data, sprite_sheet):
        """合并动画帧"""
        try:
            # ... [动画合并逻辑]
            pass
        except Exception as e:
            print(f"Error merging frames: {str(e)}")
            return None 