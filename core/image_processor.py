from PIL import Image
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class ImageProcessor:
    @staticmethod
    def process_frame(frame_data, sprite_sheet):
        """处理单个动画帧"""
        try:
            # 从sprite sheet中裁剪出当前帧
            if frame_data['rotated']:
                frame_image = sprite_sheet.crop((
                    frame_data['rect'][0],
                    frame_data['rect'][1],
                    frame_data['rect'][0] + frame_data['rect'][3],
                    frame_data['rect'][1] + frame_data['rect'][2]
                ))
                frame_image = frame_image.transpose(Image.ROTATE_90)
            else:
                frame_image = sprite_sheet.crop((
                    frame_data['rect'][0],
                    frame_data['rect'][1],
                    frame_data['rect'][0] + frame_data['rect'][2],
                    frame_data['rect'][1] + frame_data['rect'][3]
                ))
            
            # 创建目标图像
            source_w, source_h = frame_data['source_size']
            final_image = Image.new('RGBA', (source_w, source_h), (0, 0, 0, 0))
            
            # 计算粘贴位置
            offset_x, offset_y = frame_data['offset']
            paste_x = int((source_w - frame_image.width) / 2 + offset_x)
            paste_y = int((source_h - frame_image.height) / 2 - offset_y)
            
            # 粘贴到最终图像
            final_image.paste(frame_image, (paste_x, paste_y), frame_image)
            
            return final_image
            
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            return None
    
    @staticmethod
    def pil_to_pixmap(pil_image, target_size=None):
        """将PIL图像转换为QPixmap"""
        try:
            if pil_image is None:
                return None
                
            # 转换为numpy数组
            frame_array = np.array(pil_image)
            height, width, channel = frame_array.shape
            bytes_per_line = channel * width
            
            # 转换为QImage
            q_image = QImage(frame_array.data, width, height, bytes_per_line, 
                           QImage.Format_RGBA8888)
            
            # 创建QPixmap
            pixmap = QPixmap.fromImage(q_image)
            
            # 如果指定了目标大小，进行缩放
            if target_size:
                pixmap = pixmap.scaled(
                    target_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            
            return pixmap
            
        except Exception as e:
            print(f"Error converting image: {str(e)}")
            return None 