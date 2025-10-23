import cv2
import numpy as np
from PIL import Image
import streamlit as st
import io


class BookCoverRenderer:
    """
    3D图书封面渲染器类
    封装所有渲染相关功能，提供完整的3D封面生成流程
    """
    
    def __init__(self):
        self.display_ppi = 70 / 25.4  # 显示分辨率
    
    def hex_to_rgb(self, hex_color):
        """将十六进制颜色值转换为RGB格式"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def generate_3d_cover(self, cover_img, spine_img, perspective_angle, 
                          book_distance, cover_width, bg_color_bgr, bg_alpha=255):
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
            
        返回:
            渲染后的图像（RGB或RGBA格式的numpy数组）
        """
        # 转换PIL图像为OpenCV格式，需要将RGB转换为BGR
        cover = cv2.cvtColor(np.array(cover_img), cv2.COLOR_RGB2BGR)
        spine = cv2.cvtColor(np.array(spine_img), cv2.COLOR_RGB2BGR)
        
        # 获取图像尺寸
        original_cover_h, original_cover_w = cover.shape[:2]
        original_spine_h, original_spine_w = spine.shape[:2]
        
        # 角度转换为弧度
        angle_rad = np.radians(perspective_angle)

        # 计算封面变换参数
        cover_height = self.display_ppi * cover_width / original_cover_w * original_cover_h
        camera_height = cover_height / 2  # 相机高度设为总高度的一半
        camera_height_complement = cover_height - camera_height

        # 计算透视变换后的尺寸和偏移量
        display_cover_width = self.display_ppi * cover_width * np.cos(angle_rad)
        offset_y_bottom = camera_height * cover_width * np.sin(angle_rad) / (
            book_distance + cover_width * np.sin(angle_rad))
        offset_y_top = camera_height_complement * cover_width * np.sin(angle_rad) / (
            book_distance + cover_width * np.sin(angle_rad))

        # 计算书脊变换参数
        spine_height = cover_height
        spine_width = spine_height / original_spine_h * original_spine_w
        
        display_spine_width = spine_width * np.sin(angle_rad)
        spine_offset_y_bottom = camera_height * spine_width * np.cos(angle_rad) / (
            book_distance + spine_width * np.cos(angle_rad))
        spine_offset_y_top = camera_height_complement * spine_width * np.cos(angle_rad) / (
            book_distance + spine_width * np.cos(angle_rad))

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
    
    def post_process_image(self, img_array, target_width=1200, border_width=50, 
                          bg_color_rgb=(255, 255, 255), bg_alpha=255):
        """
        对生成的3D封面进行后处理：重置尺寸并添加外框
        
        参数:
            img_array: 输入图像（RGB或RGBA格式）
            target_width: 目标宽度
            border_width: 外框宽度
            bg_color_rgb: 背景颜色（RGB格式）
            bg_alpha: 背景透明度
            
        返回:
            处理后的图像
        """
        # 检查是否有Alpha通道
        has_alpha = len(img_array.shape) == 3 and img_array.shape[2] == 4
        
        # 计算缩放参数
        h, w = img_array.shape[:2]
        scale = target_width / w
        new_w = int(w * scale)
        new_h = int(h * scale)
        square_size = max(new_w, new_h)
        
        # 计算居中偏移量
        y_offset = (square_size - new_h) // 2
        x_offset = (square_size - new_w) // 2
        
        # 缩放图像
        resized = cv2.resize(img_array, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # 创建正方形画布
        if has_alpha:
            # RGBA格式画布
            square_canvas = np.full((square_size, square_size, 4), (*bg_color_rgb, bg_alpha), dtype=np.uint8)
        else:
            # RGB格式画布
            square_canvas = np.full((square_size, square_size, 3), bg_color_rgb, dtype=np.uint8)
        
        # 将缩放后的图像居中放置
        square_canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
        
        # 添加边框
        if has_alpha:
            return cv2.copyMakeBorder(
                square_canvas,
                border_width, border_width, border_width, border_width,
                cv2.BORDER_CONSTANT,
                value=(*bg_color_rgb, bg_alpha)
            )
        else:
            return cv2.copyMakeBorder(
                square_canvas,
                border_width, border_width, border_width, border_width,
                cv2.BORDER_CONSTANT,
                value=bg_color_rgb
            )


def setup_ui():
    """设置Streamlit用户界面"""
    # 设置页面配置
    st.set_page_config(
        page_title="3D图书封面渲染器",
        page_icon="📚",
        layout="wide"
    )

    # 页面标题和说明
    st.title("📚 3D图书封面渲染器")
    st.write("上传图书封面和书脊图片，调整参数生成专业的立体图书效果")

    # 侧边栏 - 参数调整
    with st.sidebar:
        st.header("参数设置")
        
        # 图书尺寸参数
        book_distance = st.slider("相机与书距离（mm）", 300, 500, 500)
        cover_width = st.slider("开本宽度（mm）", 120, 200, 187)
        perspective_angle = st.slider("旋转角度（°）", 1, 89, 30)
        
        # 渲染参数
        bg_color = st.color_picker("背景颜色", "#ffffff")
        bg_alpha = st.slider("背景不透明度", 0, 100, 100, help="0表示完全透明，100表示完全不透明")
        
        st.markdown("---")
        st.write("📝 使用说明：")
        st.write("1. 上传封面和书脊图片")
        st.write("2. 调整左侧参数")
        st.write("3. 查看预览效果")
        st.write("4. 下载渲染结果")

    # 主内容区域 - 文件上传和渲染
    col1, col2 = st.columns(2)

    with col1:
        st.header("上传图片")
        cover_image = st.file_uploader("上传封面图片", type=["png", "jpg", "jpeg"])
        spine_image = st.file_uploader("上传书脊图片", type=["png", "jpg", "jpeg"])

    with col2:
        st.header("渲染结果")
        result_placeholder = st.empty()
        download_placeholder = st.empty()
    
    return cover_image, spine_image, result_placeholder, download_placeholder, \
           book_distance, cover_width, perspective_angle, bg_color, bg_alpha


def process_images(cover_image, spine_image, result_placeholder, download_placeholder,
                   book_distance, cover_width, perspective_angle, bg_color, bg_alpha):
    """处理上传的图片并生成3D封面"""
    if not (cover_image and spine_image):
        return
    
    # 读取图片
    try:
        cover_img = Image.open(cover_image).convert('RGB')
        spine_img = Image.open(spine_image).convert('RGB')
    except Exception as e:
        st.error(f"图片读取失败: {str(e)}")
        return
    
    # 显示上传的图片预览
    st.subheader("上传的图片预览")
    img_col1, img_col2 = st.columns(2)
    with img_col1:
        st.image(spine_img, caption="书脊图片", width='content')
    with img_col2:
        st.image(cover_img, caption="封面图片", width='content')
    
    # 生成3D封面
    with st.spinner("正在渲染3D封面..."):
        try:
            # 初始化渲染器
            renderer = BookCoverRenderer()
            
            # 计算背景色和透明度
            alpha_value = int(bg_alpha * 255 / 100)
            rgb_bg = renderer.hex_to_rgb(bg_color)
            bgr_bg = rgb_bg[2], rgb_bg[1], rgb_bg[0]  # 转换为BGR格式
            
            # 生成3D封面
            result_image = renderer.generate_3d_cover(
                cover_img, spine_img,
                perspective_angle, book_distance, cover_width,
                bg_color_bgr=bgr_bg, bg_alpha=alpha_value
            )

            # 后处理
            result_image = renderer.post_process_image(
                result_image,
                bg_color_rgb=rgb_bg,
                bg_alpha=alpha_value
            )
            
            # 显示结果
            with result_placeholder:
                st.image(result_image, caption="3D封面渲染结果", width='stretch')
        
            # 准备下载
            buf = io.BytesIO()
            result_pil = Image.fromarray(result_image)
            result_pil.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            with download_placeholder:
                st.download_button(
                    label="下载3D封面图片",
                    data=byte_im,
                    file_name="3d_book_cover.png",
                    mime="image/png"
                )
                
        except Exception as e:
            st.error(f"渲染过程中出错: {str(e)}")
            st.exception(e)


def main():
    """主函数"""
    ui_elements = setup_ui()
    process_images(*ui_elements)


if __name__ == "__main__":
    main()