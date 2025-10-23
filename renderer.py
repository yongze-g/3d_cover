import cv2
import numpy as np


class BookCoverRenderer:
    """
    3D图书封面渲染器类
    封装所有渲染相关功能，提供完整的3D封面生成流程
    """
    
    def __init__(self):
        """
        ppmm = pixels per millimeter
        1 inch = 25.4 mm
        图片在最终缩放前会依此做线性变换，如果需要全尺寸立体封面，可以依此设定全尺寸
        并且取消后面的缩放、加框环节
        """
        self.display_ppmm = 96 / 25.4

    def hex_to_rgb(self, hex_color):
        """将十六进制颜色值转换为RGB格式"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def generate_3d_cover(self, cover_img, spine_img, perspective_angle, 
                          book_distance, cover_width, bg_color_bgr, bg_alpha=255, 
                          spine_spread_angle=0, camera_height_ratio=0.5):
        """
        生成3D封面效果
        
        参数:
            cover_img: PIL封面图像
            spine_img: PIL书脊图像
            perspective_angle: 旋转角度（度）
            book_distance: 相机与书距离（mm）
            cover_width: 开本宽度（mm）
            bg_color_bgr: 背景颜色（BGR格式）
            bg_alpha: 背景透明度（0-255）
            spine_spread_angle: 书脊额外展开角度（度）
            camera_height_ratio: 相机相对高度比例（0-1），用于控制3D视角的垂直位置
            
        返回:
            渲染后的图像（RGB或RGBA格式的numpy数组）
        """
        # 转换PIL图像为OpenCV格式，需要将RGB转换为BGR
        cover = cv2.cvtColor(np.array(cover_img), cv2.COLOR_RGB2BGR)
        spine = cv2.cvtColor(np.array(spine_img), cv2.COLOR_RGB2BGR)
        
        # 获取图像尺寸
        original_cover_h, original_cover_w = cover.shape[:2] # mm
        original_spine_h, original_spine_w = spine.shape[:2] # mm
        
        # 角度转换为弧度
        angle_rad = np.radians(perspective_angle)
        spine_angle_rad = np.radians(perspective_angle + spine_spread_angle)

        # 计算封面变换参数
        cover_height = self.display_ppmm * cover_width / original_cover_w * original_cover_h
        #      pixel =          pixel/mm *          mm /            pixel *            pixel

        camera_height = cover_height * camera_height_ratio  # in pixel
        camera_height_complement = cover_height - camera_height

        # 计算透视变换后的尺寸和偏移量
        display_cover_width = self.display_ppmm * cover_width * np.cos(angle_rad) # in pixel
        offset_y_bottom = camera_height * cover_width * np.sin(angle_rad) / (
            book_distance + cover_width * np.sin(angle_rad)) # in pixel
        offset_y_top = camera_height_complement * cover_width * np.sin(angle_rad) / (
            book_distance + cover_width * np.sin(angle_rad))

        # 计算书脊变换参数
        spine_height = cover_height
        spine_width = spine_height / self.display_ppmm / original_spine_h * original_spine_w # in mm
        
        display_spine_width = spine_width * self.display_ppmm * np.sin(spine_angle_rad) # in pixel
        spine_offset_y_bottom = camera_height * spine_width * np.cos(spine_angle_rad) / (
            book_distance + spine_width * np.cos(spine_angle_rad)) 
        spine_offset_y_top = camera_height_complement * spine_width * np.cos(spine_angle_rad) / (
            book_distance + spine_width * np.cos(spine_angle_rad)) 

        # 创建封面透视变换
        cover_points = np.float32([[0, 0], [original_cover_w, 0], 
                        [original_cover_w, original_cover_h], [0, original_cover_h]])
        cover_transformed = np.float32([[0, 0], [display_cover_width, offset_y_top], 
                        [display_cover_width, cover_height - offset_y_bottom], [0, cover_height]])
        cover_matrix = cv2.getPerspectiveTransform(cover_points, cover_transformed)
        cover_warped = cv2.warpPerspective(
            cover, cover_matrix, (int(display_cover_width), int(cover_height)),
            borderMode=cv2.BORDER_CONSTANT, borderValue=bg_color_bgr
        )
        
        # 创建书脊透视变换
        spine_points = np.float32([[0, 0], [original_spine_w, 0], 
                        [original_spine_w, original_spine_h], [0, original_spine_h]])
        spine_transformed = np.float32([[0, spine_offset_y_top], [display_spine_width, 0], 
                        [display_spine_width, spine_height], [0, spine_height - spine_offset_y_bottom]])
        spine_matrix = cv2.getPerspectiveTransform(spine_points, spine_transformed)
        spine_warped = cv2.warpPerspective(
            spine, spine_matrix, (int(display_spine_width), int(spine_height)),
            borderMode=cv2.BORDER_CONSTANT, borderValue=bg_color_bgr
        )
        
        # 创建最终图像
        final_width = int(display_cover_width) + int(display_spine_width)
        final_height = max(int(cover_height), int(spine_height))
        
        # 创建带背景色的画布
        final_image = np.full((final_height, final_width, 3), bg_color_bgr, dtype=np.uint8)
        
        # 放置封面和书脊
        final_image[:int(cover_height), int(display_spine_width):] = cover_warped
        final_image[:int(spine_height), :int(display_spine_width)] = spine_warped
        
        # 将BGR格式转换回RGB格式
        rgb_image = cv2.cvtColor(final_image, cv2.COLOR_BGR2RGB)
        
        # 处理透明度
        if bg_alpha < 255:
            return self._add_transparency(rgb_image, cover_warped, spine_warped, 
                                         display_spine_width, cover_height, spine_height, 
                                         bg_color_bgr, bg_alpha)
        
        return rgb_image
    
    def _add_transparency(self, rgb_image, cover_warped, spine_warped, 
                         display_spine_width, cover_height, spine_height, 
                         bg_color_bgr, bg_alpha):
        """为图像添加透明度，仅背景透明，内容保持不透明"""
        final_height, final_width = rgb_image.shape[:2]
        
        # 创建初始透明度通道
        alpha_channel = np.full((final_height, final_width), bg_alpha, dtype=np.uint8)
        
        # 标记封面区域为不透明
        cover_mask = np.any(cover_warped != bg_color_bgr, axis=2)
        alpha_channel[:int(cover_height), int(display_spine_width):][cover_mask] = 255
        
        # 标记书脊区域为不透明
        spine_mask = np.any(spine_warped != bg_color_bgr, axis=2)
        alpha_channel[:int(spine_height), :int(display_spine_width)][spine_mask] = 255
        
        # 合并RGB和Alpha通道
        return cv2.merge([rgb_image, alpha_channel])
    
    def post_process_image(self, img_array, final_size=1200, border_percentage=0.08, 
                          bg_color_rgb=(255, 255, 255), bg_alpha=255):
        """
        对生成的3D封面进行后处理：添加外框并调整尺寸到最终大小
        
        参数:
            img_array: 输入图像（RGB或RGBA格式）
            final_size: 最终成图的目标尺寸（正方形）
            border_percentage: 边框宽度占最终成图尺寸的比例（0-1之间）
            bg_color_rgb: 背景颜色（RGB格式）
            bg_alpha: 背景透明度
        """
        # 获取原图尺寸
        height, width = img_array.shape[:2]
        
        # 计算边框实际宽度
        actual_border_width = int(final_size * border_percentage)
        
        # 计算内部图像可用区域（减去边框）
        inner_size = final_size - 2 * actual_border_width
        
        # 计算缩放比例，保持纵横比，确保图像适应内部区域
        scale_ratio = inner_size / max(width, height)
        new_height = int(height * scale_ratio)
        new_width = int(width * scale_ratio)
        
        # 调整图像尺寸到内部区域大小
        resized = cv2.resize(img_array, (new_width, new_height))
        
        # 判断是否有alpha通道
        has_alpha = len(resized.shape) == 3 and resized.shape[2] == 4
        
        # 创建带背景色的画布（正方形，最终尺寸）
        if has_alpha:
            # 创建带alpha通道的画布
            final_image = np.full((final_size, final_size, 4), (*bg_color_rgb, bg_alpha), dtype=np.uint8)
            # 计算居中位置
            y_offset = (final_size - new_height) // 2
            x_offset = (final_size - new_width) // 2
            # 复制调整后的图像到画布中心
            final_image[y_offset:y_offset + new_height, 
                       x_offset:x_offset + new_width] = resized
        else:
            # 创建RGB画布
            final_image = np.full((final_size, final_size, 3), bg_color_rgb, dtype=np.uint8)
            # 计算居中位置
            y_offset = (final_size - new_height) // 2
            x_offset = (final_size - new_width) // 2
            # 复制调整后的图像到画布中心
            final_image[y_offset:y_offset + new_height, 
                       x_offset:x_offset + new_width] = resized
        
        return final_image