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
    
    def _transform_spine(self, spine_img,                  # BGR格式的书脊图像
                        perspective_angle,                # 旋转角度（度）
                        spine_spread_angle,               # 书脊额外展开角度（度）
                        book_distance,                    # 相机与书距离（mm）
                        cover_height,                     # 封面高度（像素）
                        camera_height,                    # 相机高度（像素）
                        camera_height_complement,         # 封面高度减去相机高度（像素）
                        bg_color_bgr):                    # 背景颜色（BGR格式）
        """
        处理（平装）书脊图像的变换
        
        返回:
            spine_warped: 变换后的书脊图像
            display_spine_width: 变换后的书脊宽度（像素）
            spine_height: 变换后的书脊高度（像素）
        """
        # 获取书脊图像尺寸
        original_spine_h, original_spine_w = spine_img.shape[:2] # mm
        
        # 角度转换为弧度
        spine_angle_rad = np.radians(perspective_angle + spine_spread_angle)
        
        # 计算书脊变换参数
        spine_height = cover_height
        spine_width = spine_height / self.display_ppmm / original_spine_h * original_spine_w # in mm
        
        display_spine_width = spine_width * self.display_ppmm * np.sin(spine_angle_rad) # in pixel
        spine_offset_y_bottom = camera_height * spine_width * np.cos(spine_angle_rad) / (
            book_distance + spine_width * np.cos(spine_angle_rad)) 
        spine_offset_y_top = camera_height_complement * spine_width * np.cos(spine_angle_rad) / (
            book_distance + spine_width * np.cos(spine_angle_rad)) 
        
        # 创建书脊透视变换
        spine_points = np.float32([[0, 0], [original_spine_w, 0], 
                        [original_spine_w, original_spine_h], [0, original_spine_h]])
        spine_transformed = np.float32([[0, spine_offset_y_top], [display_spine_width, 0], 
                        [display_spine_width, spine_height], [0, spine_height - spine_offset_y_bottom]])
        spine_matrix = cv2.getPerspectiveTransform(spine_points, spine_transformed)
        spine_warped = cv2.warpPerspective(
            spine_img, spine_matrix, (int(display_spine_width), int(spine_height)),
            borderMode=cv2.BORDER_CONSTANT, borderValue=bg_color_bgr
        )
        
        return spine_warped, display_spine_width, spine_height
    
    def _transform_spine_hardcover(self, spine_imgs,               # BGR格式的书脊图像数组
                                  perspective_angle,              # 旋转角度（度）
                                  spine_spread_angle,             # 书脊额外展开角度（度）
                                  book_distance,                  # 相机与书距离（mm）
                                  cover_height,                   # 封面高度（像素）
                                  camera_height,                  # 相机高度（像素）
                                  camera_height_complement,       # 封面高度减去相机高度（像素）
                                  bg_color_bgr):                  # 背景颜色（BGR格式）
        """
        处理（精装）书脊图像的变换，考虑书脊的圆弧形
        简单地采用四分之一椭圆。然而，这样的书脊透视逻辑实际上跟书封不统一。这一方面是为了简化逻辑，
        另一方面是为了避免圆弧突出书本身的轮廓（这是一个尚未良好定义的轮廓），而在多书并列时产生不必要的遮挡
        
        返回:
            spine_warped: 变换后拼合的书脊图像
            total_display_spine_width: 变换后总书脊宽度（像素）
            spine_height: 变换后的书脊高度（像素）
        """

        # 角度转换为弧度
        spine_angle_rad = np.radians(perspective_angle + spine_spread_angle)
        
        # 处理每个书脊图像
        warped_spines = []
        display_spine_widths = []
        
        for i, spine_img in enumerate(spine_imgs):
            # 获取书脊图像尺寸
            original_spine_h, original_spine_w = spine_img.shape[:2] # mm
            
            # 计算书脊变换参数
            spine_height = cover_height
            spine_width = spine_height / self.display_ppmm / original_spine_h * original_spine_w # in mm
            display_spine_width = spine_width * self.display_ppmm * np.sin(spine_angle_rad) 

            spine_offset_y_bottom = camera_height * spine_width * np.cos(spine_angle_rad) / (
                book_distance + spine_width * np.cos(spine_angle_rad)) 
            spine_offset_y_top = camera_height_complement * spine_width * np.cos(spine_angle_rad) / (
                book_distance + spine_width * np.cos(spine_angle_rad)) 
            
            # 创建书脊透视变换
            spine_points = np.float32([[0, 0], [original_spine_w, 0], 
                            [original_spine_w, original_spine_h], [0, original_spine_h]])
            spine_transformed = np.float32([[0, 0], [display_spine_width, 0], 
                            [display_spine_width, spine_height], [0, spine_height]])
            spine_matrix = cv2.getPerspectiveTransform(spine_points, spine_transformed)
            spine_warped = cv2.warpPerspective(
                spine_img, spine_matrix, (int(display_spine_width), int(spine_height)),
                borderMode=cv2.BORDER_CONSTANT, borderValue=bg_color_bgr
            )
            
            # 应用逐列像素处理函数，传入背景颜色用于空白填充
            spine_warped = self._process_spine_pixels_column(spine_warped, spine_angle_rad, spine_offset_y_top, spine_offset_y_bottom, display_spine_width, bg_color_bgr)
            
            # 从第二个书脊开始，根据前一个书脊（右侧书脊）的最左侧高度进行等比例缩放
            if i > 0:
                # 获取前一个书脊（右侧书脊）的最左侧一列
                prev_spine = warped_spines[-1]
                leftmost_col = prev_spine[:, 0]  # 最左侧一列
                
                # 查找这一列中非背景色的像素范围（有效高度）
                non_bg_pixels = np.any(leftmost_col != bg_color_bgr, axis=1)
                if np.any(non_bg_pixels):
                    # 找到第一个和最后一个非背景色像素的位置
                    first_pixel = np.argmax(non_bg_pixels)
                    last_pixel = len(non_bg_pixels) - 1 - np.argmax(non_bg_pixels[::-1])
                    
                    # 计算有效高度（减去上下偏移后的高度）
                    target_height = last_pixel - first_pixel + 1
                    
                    # 计算等比例缩放的宽度
                    aspect_ratio = spine_warped.shape[1] / spine_warped.shape[0]
                    new_width = int(target_height * aspect_ratio)
                    
                    # 进行等比例缩放
                    spine_warped = cv2.resize(spine_warped, (new_width, target_height), interpolation=cv2.INTER_LANCZOS4)
                    display_spine_width = new_width
            
            warped_spines.append(spine_warped)
            display_spine_widths.append(display_spine_width)
        
        # 计算总宽度
        total_display_spine_width = sum(display_spine_widths)
        spine_height = cover_height
        
        # 计算最大书脊高度，用于创建拼合画布
        max_spine_height = max(spine.shape[0] for spine in warped_spines) if warped_spines else int(spine_height)
        
        # 创建拼合画布
        merged_spine = np.zeros((max_spine_height, int(total_display_spine_width), 3), dtype=np.uint8)
        
        # 从右到左拼合所有变换后的书脊图像，确保垂直对齐
        current_x = total_display_spine_width
        for spine, width in zip(warped_spines, display_spine_widths):
            # 计算垂直居中偏移
            y_offset = (max_spine_height - spine.shape[0]) // 2
            # 从右到左放置书脊图像
            current_x -= width
            merged_spine[y_offset:y_offset+spine.shape[0], int(current_x):int(current_x + width)] = spine
            
        # 更新返回的书脊高度为最大高度
        spine_height = max_spine_height
        
        return merged_spine, total_display_spine_width, spine_height
    
    def _process_spine_pixels_column(self, 
                                    spine_warped,          # 变换后的书脊图像
                                    spine_angle_rad,       # 书脊角度（弧度）
                                    spine_offset_y_top,
                                    spine_offset_y_bottom,
                                    display_spine_width,   # 显示的书脊宽度
                                    bg_color_bgr):         # 背景颜色（BGR格式）用于填充
        """
        对书脊图像进行逐列像素处理，实现四分之一椭圆缩放效果
        - 最右侧列完全不变
        - 最左侧列上下分别偏移spine_offset_y_top和spine_offset_y_bottom
        - 中间列按四分之一椭圆规律缩放
        
        返回:
            processed_image: 处理后的图像
        """
        # 重命名参数以简化使用
        theta = spine_angle_rad  # 书脊角度
        w = int(display_spine_width)  # 显示的书脊宽度
        h = spine_warped.shape[0]  # 书脊高度
        
        # 创建空白输出图像，尺寸与 spine_warped 一致
        processed_image = np.zeros_like(spine_warped)
        
        # 从左到右逐列处理
        for x in range(w):
            # 计算当前列的偏移因子
            # 归一化的x坐标（相对于书脊宽度的比例）
            normalized_x = (w - x - 1) / w
            
            # 使用四分之一椭圆公式计算上部分和下部分的偏移量
            # 最下方：y=sqrt((1-(x**2/display_spine_width**2)) * spine_off_y_bottom ** 2) - spine_off_y_bottom
            # 最上方相应改成top
            
            # 底部区域偏移量（向下偏移为正）
            if spine_offset_y_bottom > 0:
                bottom_offset = int(np.sqrt((1 - (normalized_x**2)) * (spine_offset_y_bottom**2)) - spine_offset_y_bottom)
            else:
                bottom_offset = 0
            
            # 顶部区域偏移量（向上偏移为负）
            if spine_offset_y_top > 0:
                top_offset = int(np.sqrt((1 - (normalized_x**2)) * (spine_offset_y_top**2)) - spine_offset_y_top)
            else:
                top_offset = 0
            
            # 应用偏移到每一行像素
            for y in range(h):
                # 确定当前行的偏移量（线性插值）
                normalized_y = y / h
                if normalized_y < 0.5:
                    # 上半部分，使用顶部偏移量的线性插值
                    current_offset = int(top_offset * (1 - 2 * normalized_y))
                else:
                    # 下半部分，使用底部偏移量的线性插值（取负值使图像向上偏转）
                    current_offset = -int(bottom_offset * (2 * normalized_y - 1))
                
                # 计算新的y坐标
                new_y = y + current_offset
                
                # 确保新坐标在有效范围内
                if 0 <= new_y < h:
                    processed_image[y, x] = spine_warped[new_y, x]
            
            # 使用背景颜色填充空白区域
            for y in range(h):
                if not np.any(processed_image[y, x]):
                    # 直接使用传入的背景颜色填充
                    processed_image[y, x] = bg_color_bgr

        '''
        TODO
         - 多书脊模式下需要单独处理每个书脊
         - 图像先缩放后扭曲会有毛刺，改变处理顺序
         - 上下偏移跟平装完全一致，可以合并计算
         - 变量尽量往外移动，避免重复计算引用
        '''
        
        return processed_image

    def generate_3d_cover(self, cover_img,               # PIL封面图像
                          spine_img,                     # PIL书脊图像（用于平装书或作为精装书的向后兼容）
                          perspective_angle,             # 旋转角度（度）
                          book_distance,                 # 相机与书距离（mm）
                          cover_width,                   # 开本宽度（mm）
                          bg_color_bgr=(255, 255, 255),  # 背景颜色（BGR格式）
                          bg_alpha=255,                  # 背景透明度（0-255）
                          spine_spread_angle=0,          # 书脊额外展开角度（度）
                          camera_height_ratio=0.5,       # 相机相对高度比例（0-1），用于控制3D视角的垂直位置
                          book_type="平装",               # 书籍类型：精装或平装
                          spine_imgs=None):               # PIL书脊图像数组（用于精装书）
        """
        生成3D封面效果
        
        返回:
            渲染后的图像（RGB或RGBA格式的numpy数组）
        """
        # 转换PIL图像为OpenCV格式，需要将RGB转换为BGR
        cover = cv2.cvtColor(np.array(cover_img), cv2.COLOR_RGB2BGR)
        spine = cv2.cvtColor(np.array(spine_img), cv2.COLOR_RGB2BGR)
        
        # 如果是精装书且提供了spine_imgs，则将其转换为BGR格式
        if book_type == "精装" and spine_imgs is not None:
            spine_imgs_bgr = [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in spine_imgs]
        
        # 获取图像尺寸
        original_cover_h, original_cover_w = cover.shape[:2] # mm
        
        # 角度转换为弧度
        angle_rad = np.radians(perspective_angle)

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
        
        # 根据书型选择不同的书脊变换方法
        if book_type == "精装" and spine_imgs is not None:
            # 精装书使用书脊数组
            spine_warped, display_spine_width, spine_height = self._transform_spine_hardcover(
                spine_imgs_bgr, perspective_angle, spine_spread_angle, book_distance, 
                cover_height, camera_height, camera_height_complement, bg_color_bgr
            )
        elif book_type == "精装":
            # 精装书但未提供书脊数组，使用单个书脊图像作为向后兼容
            spine_warped, display_spine_width, spine_height = self._transform_spine_hardcover(
                [spine], perspective_angle, spine_spread_angle, book_distance, 
                cover_height, camera_height, camera_height_complement, bg_color_bgr
            )
        else:  # 平装
            spine_warped, display_spine_width, spine_height = self._transform_spine(
                spine, perspective_angle, spine_spread_angle, book_distance, 
                cover_height, camera_height, camera_height_complement, bg_color_bgr
            )
        
        # 创建最终图像尺寸
        final_width = int(display_cover_width) + int(display_spine_width)
        final_height = max(int(cover_height), int(spine_height))
        
        # 将BGR格式转换回RGB格式
        # 创建带背景色的RGB画布
        rgb_image = np.full((final_height, final_width, 3), 
                          (bg_color_bgr[2], bg_color_bgr[1], bg_color_bgr[0]), 
                          dtype=np.uint8)
        
        # 放置封面和书脊
        rgb_image[:int(cover_height), int(display_spine_width):] = cv2.cvtColor(cover_warped, cv2.COLOR_BGR2RGB)
        rgb_image[:int(spine_height), :int(display_spine_width)] = cv2.cvtColor(spine_warped, cv2.COLOR_BGR2RGB)
        
        # 处理透明度 - 直接在主函数中实现，避免单独调用_add_transparency
        if bg_alpha < 255:
            # 创建初始透明度通道，值为背景透明度
            alpha_channel = np.full((final_height, final_width), bg_alpha, dtype=np.uint8)
             
            # 标记封面区域为不透明
            cover_mask = np.any(cover_warped != bg_color_bgr, axis=2)
            alpha_channel[:int(cover_height), int(display_spine_width):][cover_mask] = 255
            
            # 标记书脊区域为不透明
            spine_mask = np.any(spine_warped != bg_color_bgr, axis=2)
            alpha_channel[:int(spine_height), :int(display_spine_width)][spine_mask] = 255
            
            # 合并RGB和Alpha通道
            return cv2.merge([rgb_image, alpha_channel])
        
        return rgb_image
    
    def overlay_shadow(self, original_image, shadow_image = "shadows/linear.png"):
        """
        叠加阴影
        
        参数:
            original_image: 原图片A（BGR格式）
            shadow_image: 阴影图片B（BGR格式，带有Alpha通道）
            
        返回:
            叠加阴影后的新图像（BGR格式）
        """
        # 获取原图片尺寸
        original_height, original_width = original_image.shape[:2]
        
        # 将阴影图片调整到与原图片相同的尺寸
        resized_shadow = cv2.resize(shadow_image, (original_width, original_height))
        
        # 检查阴影图片是否有Alpha通道
        if resized_shadow.shape[2] == 4:
            # 分离阴影图像的BGR和Alpha通道
            shadow_bgr = resized_shadow[:, :, :3]
            shadow_alpha = resized_shadow[:, :, 3] / 255.0  # 转换为0-1范围
            
            # 创建结果图像
            result = original_image.copy()
            
            # 叠加阴影（使用Alpha通道作为权重）
            for c in range(3):  # 遍历BGR通道
                result[:, :, c] = (1 - shadow_alpha) * original_image[:, :, c] + shadow_alpha * shadow_bgr[:, :, c]
        else:
            # 如果没有Alpha通道，直接叠加（假设阴影已经处理好透明度）
            result = cv2.addWeighted(original_image, 1.0, resized_shadow, 0.5, 0)
        
        return result
    
    def merge_spines(self, spine_images):
        """
        将多个书脊图像拼合为一个图像
        
        参数:
            spine_images: PIL格式的多个书脊图像列表
            
        返回:
            merged_spine: 拼合后的单个书脊图像（PIL格式）
        """
        if not spine_images:
            raise ValueError("至少需要提供一个书脊图像")
        
        # 将PIL图像转换为OpenCV格式（BGR）
        spines_bgr = [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in spine_images]
        
        # 确定统一的高度（使用最大的高度）
        max_height = max(spine.shape[0] for spine in spines_bgr)
        
        # 调整所有书脊到相同高度
        resized_spines = []
        for spine in spines_bgr:
            # 计算缩放比例以保持宽高比
            h, w = spine.shape[:2]
            scale = max_height / h
            new_width = int(w * scale)
            # 调整大小
            resized_spine = cv2.resize(spine, (new_width, max_height))
            resized_spines.append(resized_spine)
        
        # 从右到左拼合书脊
        # 注意：我们需要反转书脊列表，因为最右边的书脊应该是列表中的第一个
        total_width = sum(spine.shape[1] for spine in resized_spines)
        
        # 创建空白画布
        merged = np.zeros((max_height, total_width, 3), dtype=np.uint8)
        
        # 从右到左放置书脊
        current_x = total_width
        for spine in resized_spines:
            h, w = spine.shape[:2]
            current_x -= w
            merged[:h, current_x:current_x + w] = spine
        
        # 将拼合后的BGR图像转换回PIL的RGB格式
        merged_rgb = cv2.cvtColor(merged, cv2.COLOR_BGR2RGB)
        from PIL import Image
        return Image.fromarray(merged_rgb)
        
    def post_process_image(self, img_array,               # 输入图像（RGB或RGBA格式）
                           final_size=1200,               # 最终成图的目标尺寸（正方形）
                           border_percentage=0.08,        # 边框宽度占最终成图尺寸的比例（0-1之间）
                           bg_color_rgb=(255, 255, 255),  # 背景颜色（RGB格式）
                           bg_alpha=255):                 # 背景透明度
        """
        对生成的3D封面进行后处理：添加外框并调整尺寸到最终大小
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