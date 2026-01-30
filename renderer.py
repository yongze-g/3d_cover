import cv2
import numpy as np
from PIL import Image


class BookCoverRenderer:
    """
    3D图书封面渲染器类
    封装所有渲染相关功能，提供完整的3D封面生成流程
    """
    
    def __init__(self):
        # 物理常量 - 像素密度（pixels per millimeter）
        self.display_ppmm = 96 / 25.4

    def _hex_to_rgb(self, hex_color):
        """将十六进制颜色值转换为RGB格式"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _transform_spine(self, spine_img, cover_height, spine_angle_rad, camera_height, 
                         camera_height_complement, book_distance, bg_color_bgr):
        """
        处理（平装）书脊图像的变换

        返回:
            spine_warped: 变换后的书脊图像
            spine_mask: 书脊内容掩码（True表示内容，False表示背景填充）
            display_spine_width: 变换后的书脊宽度（像素）
            spine_height: 变换后的书脊高度（像素）
        """
        # 获取书脊图像尺寸
        original_spine_h, original_spine_w = spine_img.shape[:2] # mm
        
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
        
        # 变换书脊图像
        spine_warped = cv2.warpPerspective(
            spine_img, spine_matrix, (int(display_spine_width), int(spine_height)),
            borderMode=cv2.BORDER_CONSTANT, borderValue=bg_color_bgr
        )
        
        # 创建原始内容掩码
        original_mask = np.ones((original_spine_h, original_spine_w), dtype=bool)
        
        # 对掩码进行同样的透视变换
        spine_mask = cv2.warpPerspective(
            original_mask.astype(np.uint8), spine_matrix, (int(display_spine_width), int(spine_height)),
            borderMode=cv2.BORDER_CONSTANT, borderValue=0
        ).astype(bool)
        
        return spine_warped, spine_mask, display_spine_width, spine_height
    
    def _process_spine_pixels_column(self, spine_warped, spine_mask, spine_offset_y_top, 
                                    spine_offset_y_bottom, display_spine_width, bg_color_bgr):
        """
        对书脊图像进行逐列像素处理，实现四分之一椭圆缩放效果
        - 最右侧列完全不变
        - 最左侧列上下分别偏移spine_offset_y_top和spine_offset_y_bottom
        - 中间列按四分之一椭圆规律缩放

        返回:
            processed_image: 处理后的图像
            processed_mask: 处理后的掩码
        """
        # 获取图像尺寸
        h, w = spine_warped.shape[:2]
        w = int(display_spine_width)
        
        # 创建空白输出图像和掩码
        processed_image = np.zeros_like(spine_warped)
        processed_mask = np.zeros((h, w), dtype=bool)
        
        # 向量化计算偏移量，避免双重循环
        # 创建x坐标数组 (0到w-1)
        x = np.arange(w)
        # 归一化x坐标（从右到左）
        normalized_x = (w - x - 1) / w
        
        # 计算底部和顶部偏移量
        bottom_offset = np.zeros(w)
        top_offset = np.zeros(w)
        
        if spine_offset_y_bottom > 0:
            bottom_offset = np.sqrt((1 - normalized_x**2) * (spine_offset_y_bottom**2)) - spine_offset_y_bottom
            bottom_offset = bottom_offset.astype(int)
        
        if spine_offset_y_top > 0:
            top_offset = np.sqrt((1 - normalized_x**2) * (spine_offset_y_top**2)) - spine_offset_y_top
            top_offset = top_offset.astype(int)
        
        # 创建y坐标数组 (0到h-1)
        y = np.arange(h)
        
        # 计算每个像素的偏移量
        for x_col in range(w):
            # 计算当前列的偏移因子
            current_bottom_offset = bottom_offset[x_col]
            current_top_offset = top_offset[x_col]
            
            # 计算每一行的偏移量（线性插值）
            normalized_y = y / h
            offsets = np.where(
                normalized_y < 0.5,
                current_top_offset * (1 - 2 * normalized_y),
                -current_bottom_offset * (2 * normalized_y - 1)
            ).astype(int)
            
            # 计算新的y坐标
            new_y = y + offsets
            
            # 确保新坐标在有效范围内
            valid_mask = (new_y >= 0) & (new_y < h)
            
            # 应用偏移到图像
            processed_image[y[valid_mask], x_col] = spine_warped[new_y[valid_mask], x_col]
            
            # 应用偏移到掩码
            if spine_mask is not None:
                processed_mask[y[valid_mask], x_col] = spine_mask[new_y[valid_mask], x_col]
            else:
                # 如果没有提供掩码，假设所有有效像素都是内容
                processed_mask[y[valid_mask], x_col] = True
            
            # 填充空白区域
            # 使用掩码来判断哪些像素未被填充
            empty_mask = ~processed_mask[:, x_col]
            processed_image[empty_mask, x_col] = bg_color_bgr

        return processed_image, processed_mask
    
    def _transform_spine_hardcover(self, spine_imgs, cover_height, spine_angle_rad, 
                                  camera_height, camera_height_complement, book_distance, bg_color_bgr):
        """
        处理（精装）书脊图像的变换，考虑书脊的圆弧形
        简单地采用四分之一椭圆。然而，这样的书脊透视逻辑实际上跟书封不统一。这一方面是为了简化逻辑，
        另一方面是为了避免圆弧突出书本身的轮廓（这是一个尚未良好定义的轮廓），而在多书并列时产生不必要的遮挡

        返回:
            spine_warped: 变换后拼合的书脊图像
            spine_mask: 拼合后的书脊内容掩码（True表示内容，False表示背景填充）
            total_display_spine_width: 变换后总书脊宽度（像素）
            spine_height: 变换后的书脊高度（像素）
        """

        # 处理每个书脊图像
        warped_spines = []
        warped_spine_masks = []  # 新增：存储每个书脊的掩码
        display_spine_widths = []

        last_spine_height = cover_height
        
        for spine_img in spine_imgs:
            # 获取书脊图像尺寸
            original_spine_h, original_spine_w = spine_img.shape[:2] # mm
            
            # 计算书脊变换参数
            pivot_height = cover_height
            pivot_width = pivot_height / self.display_ppmm / original_spine_h * original_spine_w # mm
            pivot_width_px = pivot_width * self.display_ppmm * np.sin(spine_angle_rad) # px，用于中转实现卷曲

            pivot_offset_y_bottom = camera_height * pivot_width * np.cos(spine_angle_rad) / (
                book_distance + pivot_width * np.cos(spine_angle_rad)) 
            pivot_offset_y_top = camera_height_complement * pivot_width * np.cos(spine_angle_rad) / (
                book_distance + pivot_width * np.cos(spine_angle_rad)) 

            spine_warped = cv2.resize(
                spine_img, (int(pivot_width_px), int(pivot_height)),
                interpolation=cv2.INTER_LANCZOS4
            )
            
            # 创建原始内容掩码
            original_mask = np.ones((int(pivot_height), int(pivot_width_px)), dtype=bool)
            
            # 应用逐列像素处理函数，传入背景颜色用于空白填充
            spine_warped, spine_mask = self._process_spine_pixels_column(
                spine_warped, original_mask, pivot_offset_y_top, pivot_offset_y_bottom, pivot_width_px, bg_color_bgr
            )

            display_height = int(last_spine_height)
            display_width = int(pivot_width_px * display_height / pivot_height)

            spine_warped = cv2.resize(
                 spine_warped, (display_width, display_height),
                 interpolation=cv2.INTER_LANCZOS4
             )
             
            # 调整掩码尺寸
            spine_mask = cv2.resize(
                spine_mask.astype(np.uint8), (display_width, display_height),
                interpolation=cv2.INTER_NEAREST  # 使用最近邻插值保持掩码的布尔值
            ).astype(bool)

            last_spine_height = display_height - pivot_offset_y_top - pivot_offset_y_bottom
            
            warped_spines.append(spine_warped)
            warped_spine_masks.append(spine_mask)
            # 使用实际spine_warped的宽度，而不是计算的宽度，避免浮点数精度问题
            display_spine_widths.append(display_width)
        
        # 计算总宽度
        total_display_spine_width = sum(display_spine_widths)
        
        # 创建合并后的图像和掩码
        merged_spine = np.zeros((int(cover_height), int(total_display_spine_width), 4), dtype=np.uint8)
        merged_mask = np.zeros((int(cover_height), int(total_display_spine_width)), dtype=bool)
        
        # 设置背景颜色（直接使用BGR格式，因为merged_spine在后续操作中会保持BGR通道顺序）
        merged_spine[:, :, 0:3] = bg_color_bgr
        # 设置透明度为完全不透明
        merged_spine[:, :, 3] = 255
        
        # 从右到左拼合所有变换后的书脊图像和掩码，确保垂直对齐
        current_x = total_display_spine_width
        for spine, spine_mask, width in zip(warped_spines, warped_spine_masks, display_spine_widths):
            # 计算垂直居中偏移
            y_offset = int((cover_height - spine.shape[0]) * camera_height_complement / cover_height)
            # 从右到左放置书脊图像
            current_x -= width
            # 获取实际图像宽度，避免浮点数精度问题
            actual_width = spine.shape[1]
            # 确保目标区域和源图像尺寸一致
            current_x_int = int(current_x)
            start_x = max(0, current_x_int)
            end_x = min(current_x_int + actual_width, merged_spine.shape[1])
            # 只有当目标区域有效时才进行赋值
            if end_x > start_x:
                # 确保所有切片索引都是整数，并且只操作RGB通道（前3个通道）
                merged_spine[y_offset:y_offset+spine.shape[0], start_x:end_x, :3] = spine[:, :end_x-start_x]
                # 更新掩码
                merged_mask[y_offset:y_offset+spine_mask.shape[0], start_x:end_x] = spine_mask[:, :end_x-start_x]
        
        return merged_spine, merged_mask, total_display_spine_width, cover_height
    
    def _overlay_shadow(self, original_image, shadow_image):
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
    
    def _merge_spines(self, spine_images):
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
        
        # 确定统一的高度
        max_height = max(spine.shape[0] for spine in spines_bgr)
        
        # 调整所有书脊到相同高度
        resized_spines = []
        for spine in spines_bgr:
            h, w = spine.shape[:2]
            scale = max_height / h
            new_width = int(w * scale)
            resized_spine = cv2.resize(spine, (new_width, max_height))
            resized_spines.append(resized_spine)
        
        # 从右到左拼合书脊
        total_width = sum(spine.shape[1] for spine in resized_spines)
        merged = np.zeros((max_height, total_width, 3), dtype=np.uint8)
        
        current_x = total_width
        for spine in resized_spines:
            h, w = spine.shape[:2]
            current_x -= w
            merged[:h, current_x:current_x + w] = spine
        
        # 将拼合后的BGR图像转换回PIL的RGB格式
        merged_rgb = cv2.cvtColor(merged, cv2.COLOR_BGR2RGB)
        return Image.fromarray(merged_rgb)
    
    def _apply_shadow_to_spines(self, spine_images, shadow_mode):
        """
        对书脊图像应用阴影效果

        参数:
            spine_images: PIL格式的多个书脊图像列表
            shadow_mode: 阴影模式（无/线性/反射）

        返回:
            processed_spine_images: 应用阴影后的书脊图像列表（PIL格式）
        """
        # 如果没有书脊图片或阴影模式为"无"，直接返回原图
        if not spine_images or shadow_mode == "无":
            return spine_images.copy()
        
        # 定义阴影模式与文件路径的映射字典
        import os
        # 获取当前文件所在目录的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        shadow_mapping = {
            "线性": os.path.join(current_dir, 'shadows', 'linear.png'),
            "反射": os.path.join(current_dir, 'shadows', 'reflect.png')
        }
        
        # 如果阴影模式无效，直接返回原图
        if shadow_mode not in shadow_mapping:
            return spine_images.copy()
        
        processed_spines = []
        
        try:
            # 加载阴影图片
            shadow_path = shadow_mapping[shadow_mode]
            shadow_img = cv2.imread(shadow_path, cv2.IMREAD_UNCHANGED)
            
            # 检查阴影图片是否成功加载
            if shadow_img is None:
                print(f"无法加载阴影图片: {shadow_path}")
                return spine_images.copy()
            
            # 对每个书脊图片应用阴影
            for spine in spine_images:
                # 将PIL图像转换为OpenCV格式进行处理
                spine_array = np.array(spine)
                spine_bgr = cv2.cvtColor(spine_array, cv2.COLOR_RGB2BGR)
                
                # 应用阴影
                spine_with_shadow = self._overlay_shadow(spine_bgr, shadow_img)
                
                # 将处理后的图像转回PIL格式
                processed_spine = Image.fromarray(cv2.cvtColor(spine_with_shadow, cv2.COLOR_BGR2RGB))
                processed_spines.append(processed_spine)
        except Exception as e:
            # 如果阴影处理失败，返回原图
            print(f"无法加载或应用阴影：{str(e)}")
            return spine_images.copy()
        
        return processed_spines
    
    def _process_spines(self, spine_images, book_type):
        """
        处理书脊图像，根据书型决定是否拼合书脊

        参数:
            spine_images: PIL格式的多个书脊图像列表
            book_type: 书型（平装/精装）

        返回:
            spine_img: 处理后的单个书脊图像（PIL格式）
            hardcover_spines: 精装书的书脊数组（如果是精装书），否则为None
        """
        hardcover_spines = spine_images.copy() if book_type == "精装" else None
        spine_img = self._merge_spines(spine_images)
        
        return spine_img, hardcover_spines
    
    def _convert_images_to_bgr(self, cover_img, spine_img, hardcover_spines, book_type):
        """
        将PIL图像转换为OpenCV BGR格式
        """
        cover = cv2.cvtColor(np.array(cover_img), cv2.COLOR_RGB2BGR)
        spine = cv2.cvtColor(np.array(spine_img), cv2.COLOR_RGB2BGR)
        
        spine_imgs_bgr = None
        if book_type == "精装" and hardcover_spines is not None:
            spine_imgs_bgr = [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in hardcover_spines]
        
        return cover, spine, spine_imgs_bgr
    
    def _calculate_transform_params(self, cover, cover_width, perspective_angle, spine_spread_angle, 
                                  camera_height_ratio, book_distance):
        """
        计算封面和书脊的变换参数
        """
        # 获取图像尺寸
        original_cover_h, original_cover_w = cover.shape[:2]

        # 计算封面变换参数
        cover_height = self.display_ppmm * cover_width / original_cover_w * original_cover_h
        camera_height = cover_height * camera_height_ratio
        camera_height_complement = cover_height - camera_height
        
        # 角度转换为弧度
        angle_rad = np.radians(perspective_angle)
        spine_angle_rad = np.radians(perspective_angle + spine_spread_angle)

        # 计算透视变换后的尺寸和偏移量
        display_cover_width = self.display_ppmm * cover_width * np.cos(angle_rad)
        offset_y_bottom = camera_height * cover_width * np.sin(angle_rad) / (
            book_distance + cover_width * np.sin(angle_rad))
        offset_y_top = camera_height_complement * cover_width * np.sin(angle_rad) / (
            book_distance + cover_width * np.sin(angle_rad))
        
        return {
            "cover_height": cover_height,
            "camera_height": camera_height,
            "camera_height_complement": camera_height_complement,
            "angle_rad": angle_rad,
            "spine_angle_rad": spine_angle_rad,
            "display_cover_width": display_cover_width,
            "offset_y_bottom": offset_y_bottom,
            "offset_y_top": offset_y_top
        }
    
    def _transform_cover(self, cover, original_cover_w, original_cover_h, display_cover_width, 
                        cover_height, offset_y_top, offset_y_bottom, bg_color_bgr):
        """
        对封面图像进行透视变换
        
        返回:
            cover_warped: 变换后的封面图像
            cover_mask: 封面内容掩码（True表示内容，False表示背景填充）
        """
        # 创建封面透视变换
        cover_points = np.float32([[0, 0], [original_cover_w, 0], 
                        [original_cover_w, original_cover_h], [0, original_cover_h]])
        cover_transformed = np.float32([[0, 0], [display_cover_width, offset_y_top], 
                        [display_cover_width, cover_height - offset_y_bottom], [0, cover_height]])
        cover_matrix = cv2.getPerspectiveTransform(cover_points, cover_transformed)
        
        # 变换封面图像
        cover_warped = cv2.warpPerspective(
            cover, cover_matrix, (int(display_cover_width), int(cover_height)),
            borderMode=cv2.BORDER_CONSTANT, borderValue=bg_color_bgr
        )
        
        # 创建原始内容掩码
        original_mask = np.ones((original_cover_h, original_cover_w), dtype=bool)
        
        # 对掩码进行同样的透视变换
        cover_mask = cv2.warpPerspective(
            original_mask.astype(np.uint8), cover_matrix, (int(display_cover_width), int(cover_height)),
            borderMode=cv2.BORDER_CONSTANT, borderValue=0
        ).astype(bool)
        
        return cover_warped, cover_mask
    
    def _generate_3d_cover(self, cover_img, spine_img, hardcover_spines, perspective_angle, 
                          book_distance, cover_width, bg_color, bg_alpha, spine_spread_angle, 
                          camera_height_ratio, book_type, stroke_enabled=False):
        """
        生成3D封面效果

        返回:
            渲染后的图像（RGB或RGBA格式的numpy数组）
        """
        # 转换图像格式
        cover, spine, spine_imgs_bgr = self._convert_images_to_bgr(cover_img, spine_img, hardcover_spines, book_type)
        
        # 计算背景颜色
        if isinstance(bg_color, str):
            rgb_bg = self._hex_to_rgb(bg_color)
            bg_color_bgr = (rgb_bg[2], rgb_bg[1], rgb_bg[0])
        else:
            bg_color_bgr = bg_color
        
        # 计算变换参数
        transform_params = self._calculate_transform_params(
            cover, cover_width, perspective_angle, spine_spread_angle, 
            camera_height_ratio, book_distance
        )
        
        # 变换封面
        cover_warped, cover_mask = self._transform_cover(
            cover, cover.shape[1], cover.shape[0], transform_params["display_cover_width"], 
            transform_params["cover_height"], transform_params["offset_y_top"], 
            transform_params["offset_y_bottom"], bg_color_bgr
        )
        
        # 根据书型选择不同的书脊变换方法
        if book_type == "精装" and spine_imgs_bgr is not None:
            # 精装书使用书脊数组
            spine_warped, spine_mask, display_spine_width, spine_height = self._transform_spine_hardcover(
                spine_imgs_bgr, transform_params["cover_height"], transform_params["spine_angle_rad"], 
                transform_params["camera_height"], transform_params["camera_height_complement"], 
                book_distance, bg_color_bgr
            )
        elif book_type == "精装":
            # 精装书但未提供书脊数组，使用单个书脊图像
            spine_warped, spine_mask, display_spine_width, spine_height = self._transform_spine_hardcover(
                [spine], transform_params["cover_height"], transform_params["spine_angle_rad"], 
                transform_params["camera_height"], transform_params["camera_height_complement"], 
                book_distance, bg_color_bgr
            )
        else:  # 平装
            spine_warped, spine_mask, display_spine_width, spine_height = self._transform_spine(
                spine, transform_params["cover_height"], transform_params["spine_angle_rad"], 
                transform_params["camera_height"], transform_params["camera_height_complement"], 
                book_distance, bg_color_bgr
            )
        
        # 创建最终图像尺寸
        final_width = int(transform_params["display_cover_width"]) + int(display_spine_width)
        final_height = max(int(transform_params["cover_height"]), int(spine_height))
        
        # 创建带背景色的RGB画布
        rgb_image = np.full((final_height, final_width, 3), 
                          (bg_color_bgr[2], bg_color_bgr[1], bg_color_bgr[0]), 
                          dtype=np.uint8)
        
        # 放置封面和书脊
        rgb_image[:int(transform_params["cover_height"]), int(display_spine_width):] = cv2.cvtColor(cover_warped, cv2.COLOR_BGR2RGB)
        rgb_image[:int(spine_height), :int(display_spine_width)] = cv2.cvtColor(spine_warped, cv2.COLOR_BGR2RGB)
        
        # 如果启用描边功能，则添加细灰色描边
        if stroke_enabled:
            # 创建联合掩码（封面+书脊）
            full_mask = np.zeros((final_height, final_width), dtype=np.uint8)
            
            # 设置封面掩码区域
            cover_region = full_mask[:int(transform_params["cover_height"]), int(display_spine_width):]
            cover_region[cover_mask] = 255
            
            # 设置书脊掩码区域
            spine_region = full_mask[:int(spine_height), :int(display_spine_width)]
            spine_region[spine_mask] = 255
            
            # 提取边界
            contours, _ = cv2.findContours(full_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 绘制灰色描边
            gray_color = (128, 128, 128)  # 灰色
            for contour in contours:
                cv2.drawContours(rgb_image, [contour], -1, gray_color, 1)
        
        # 处理透明度
        if bg_alpha < 255:
            alpha_channel = np.full((final_height, final_width), bg_alpha, dtype=np.uint8)
              
            # 标记封面区域为不透明
            cover_region = alpha_channel[:int(transform_params["cover_height"]), int(display_spine_width):]
            cover_region[cover_mask] = 255
            
            # 标记书脊区域为不透明
            spine_region = alpha_channel[:int(spine_height), :int(display_spine_width)]
            spine_region[spine_mask] = 255
            
            # 合并RGB和Alpha通道
            return cv2.merge([rgb_image, alpha_channel])
        
        return rgb_image
    
    def _post_process_image(self, img_array, final_size, border_percentage, bg_color, bg_alpha):
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
        
        # 处理背景颜色 - 支持RGB格式和十六进制字符串
        if isinstance(bg_color, str):
            # 如果是十六进制字符串，转换为RGB
            bg_color_rgb = self._hex_to_rgb(bg_color)
        else:
            bg_color_rgb = bg_color
        
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
    
    def render_3d_cover(self, cover_img,               # PIL封面图像
                       spine_images,                   # PIL格式的多个书脊图像列表
                       perspective_angle,              # 旋转角度（度）
                       book_distance,                  # 相机与书距离（mm）
                       cover_width,                    # 开本宽度（mm）
                       bg_color,                       # 背景颜色（十六进制）
                       bg_alpha,                       # 背景透明度（0-255）
                       spine_spread_angle,             # 书脊额外展开角度（度）
                       camera_height_ratio,            # 相机高度比例
                       final_size,                     # 最终图像尺寸
                       border_percentage,              # 边框占最终图像的比例
                       book_type,                      # 书型（平装/精装）
                       spine_shadow_mode,              # 书脊阴影模式
                       stroke_enabled=False):          # 是否为封面描边
        """
        完整的3D封面渲染流程

        参数:
            cover_img: PIL封面图像
            spine_images: PIL格式的多个书脊图像列表
            perspective_angle: 旋转角度（度）
            book_distance: 相机与书距离（mm）
            cover_width: 开本宽度（mm）
            bg_color: 背景颜色（十六进制）
            bg_alpha: 背景透明度（0-255）
            spine_spread_angle: 书脊额外展开角度（度）
            camera_height_ratio: 相机高度比例
            final_size: 最终图像尺寸
            border_percentage: 边框占最终图像的比例
            book_type: 书型（平装/精装）
            spine_shadow_mode: 书脊阴影模式
            stroke_enabled: 是否为封面描边

        返回:
            result_image: 渲染后的3D封面图像
        """
        # 应用阴影效果
        processed_spine_images = self._apply_shadow_to_spines(spine_images, spine_shadow_mode)
        
        # 处理书脊图像，根据书型决定是否拼合书脊
        spine_img, hardcover_spines = self._process_spines(processed_spine_images, book_type)
        
        # 生成3D封面
        result_image = self._generate_3d_cover(
            cover_img, spine_img, hardcover_spines,
            perspective_angle, book_distance, cover_width,
            bg_color, bg_alpha, spine_spread_angle,
            camera_height_ratio, book_type, stroke_enabled
        )
        
        # 进行后处理
        result_image = self._post_process_image(
            result_image, final_size, border_percentage, bg_color, bg_alpha
        )
        
        return result_image