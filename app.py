import cv2
import numpy as np
from PIL import Image
import streamlit as st
import io

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
    # shadow_intensity = st.slider("阴影强度", 0.0, 1.0, 0.3)
    
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

# 转换颜色十六进制值为BGR格式
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))  # RGB格式

# 生成3D封面效果
def generate_3d_cover(cover_img, spine_img, perspective_angle, book_distance, cover_width):
    # 转换PIL图像为OpenCV格式，需要将RGB转换为BGR
    cover = cv2.cvtColor(np.array(cover_img), cv2.COLOR_RGB2BGR)
    spine = cv2.cvtColor(np.array(spine_img), cv2.COLOR_RGB2BGR)
    
    # 计算透视变换参数
    original_cover_image_height, original_cover_image_width = cover.shape[:2]
    original_spine_image_height, original_spine_image_width = spine.shape[:2]
    
    display_ppi = 70 / 25.4
    angle_rad = np.radians(perspective_angle)

    # 封面变换参数
    cover_height = display_ppi * cover_width / original_cover_image_width * original_cover_image_height # 总高度，即立体封面上最高的高度，单位是像素

    camera_height = cover_height / 2 # 相机高度，当前设为总高度的一半，后期加调整功能
    camera_height_complement = cover_height - camera_height

    display_cover_width = display_ppi * cover_width * np.cos(angle_rad) 
    transformed_offset_y_bottom = camera_height * cover_width * np.sin(angle_rad) / \
        (book_distance + cover_width * np.sin(angle_rad))
    transformed_offset_y_top = camera_height_complement * cover_width * np.sin(angle_rad) / \
        (book_distance + cover_width * np.sin(angle_rad))

    # 书脊变换参数
    spine_height = cover_height # 单位已是像素，不需要再乘以display_ppi，后面参数也不需要再乘以display_ppi
    spine_width = spine_height / original_spine_image_height * original_spine_image_width
    
    display_spine_width = spine_width * np.sin(angle_rad)
    transformed_spine_offset_y_bottom = camera_height * spine_width * np.cos(angle_rad) / \
        (book_distance + spine_width * np.cos(angle_rad))
    transformed_spine_offset_y_top = camera_height_complement * spine_width * np.cos(angle_rad) / \
        (book_distance + spine_width * np.cos(angle_rad))

    # 背景色已在外部计算
    
    # 创建封面透视变换
    cover_points = np.float32([[0, 0], [original_cover_image_width, 0], \
        [original_cover_image_width, original_cover_image_height], [0, original_cover_image_height]])
    cover_transformed = np.float32([[0, 0], [display_cover_width,  transformed_offset_y_top], \
        [display_cover_width, cover_height - transformed_offset_y_bottom], [0, cover_height]])
    cover_matrix = cv2.getPerspectiveTransform(cover_points, cover_transformed)
    # 使用指定背景色填充透视变换的空白区域
    cover_warped = cv2.warpPerspective(cover, cover_matrix, (int(display_cover_width), int(cover_height)), 
                                     borderMode=cv2.BORDER_CONSTANT, borderValue=bgr_bg)
    
    # 创建书脊透视变换
    spine_points = np.float32([[0, 0], [original_spine_image_width, 0], \
        [original_spine_image_width, original_spine_image_height], [0, original_spine_image_height]])
    spine_transformed = np.float32([[0, transformed_spine_offset_y_top], [display_spine_width, 0], \
        [display_spine_width, spine_height], [0, spine_height - transformed_spine_offset_y_bottom]])
    spine_matrix = cv2.getPerspectiveTransform(spine_points, spine_transformed)
    # 使用指定背景色填充透视变换的空白区域
    spine_warped = cv2.warpPerspective(spine, spine_matrix, (int(display_spine_width), int(spine_height)),
                                     borderMode=cv2.BORDER_CONSTANT, borderValue=bgr_bg)
    
    # 创建最终图像 (考虑书脊和封面的尺寸)
    final_width =  int(display_cover_width) + int(display_spine_width)
    final_height = max(int(cover_height), int(spine_height))
    
    # 创建带背景色的画布
    final_image = np.full((final_height, final_width, 3), bgr_bg, dtype=np.uint8)
    
    # 放置封面
    final_image[:int(cover_height), int(display_spine_width):] = cover_warped
    
    # 放置书脊
    final_image[:int(spine_height), :int(display_spine_width)] = spine_warped
    
    # 添加简单阴影效果 (注释掉阴影效果)
    # if shadow_intensity > 0:
    #     shadow_offset = int(offset_x * 0.3)
    #     # 在封面下方添加阴影
    #     shadow_region = final_image[h:h + shadow_offset, w:]
    #     shadow_filter = np.ones_like(shadow_region, dtype=np.float32) * (1 - shadow_intensity)
    #     final_image[h:h + shadow_offset, w:] = np.clip(
    #         shadow_region * shadow_filter, 0, 255).astype(np.uint8)
    
    # 将BGR格式转换回RGB格式，以便Streamlit和PIL正确显示和保存
    return cv2.cvtColor(final_image, cv2.COLOR_BGR2RGB)

# 对生成的3D封面进行后处理：重置尺寸并添加外框
def post_process_3d_cover(img_array, target_width=1200, border_width=50, bg_color=(255, 255, 255)):
    """
    对生成的3D封面进行后处理：重置尺寸并添加与背景色相同的外框
    :param img_array: 输入的3D封面图像（numpy数组），RGB格式
    :param target_width: 目标宽度（像素），高度按比例缩放
    :param border_width: 外框宽度（像素）
    :param bg_color: 背景颜色和边框颜色，BGR格式（需要转换为RGB）
    :return: 处理后的图像（numpy数组），RGB格式
    """
    # 将BGR格式的背景色转换为RGB格式，与输入图像保持一致
    rgb_bg = (bg_color[2], bg_color[1], bg_color[0])
    
    h, w = img_array.shape[:2]
    # 按比例缩放至目标宽度
    scale = target_width / w
    new_w = int(w * scale)
    new_h = int(h * scale)
    # 计算正方形尺寸（取宽高中的较大值）
    square_size = max(new_w, new_h)
    
    # 将图片按比例缩放
    resized = cv2.resize(img_array, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # 创建与背景色相同的正方形画布（使用RGB格式）
    square_canvas = np.full((square_size, square_size, 3), rgb_bg, dtype=np.uint8)
    
    # 计算居中偏移量
    y_offset = (square_size - new_h) // 2
    x_offset = (square_size - new_w) // 2
    
    # 将缩放后的图像居中粘贴到正方形画布上
    square_canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
    
    resized = square_canvas

    # 添加与背景色相同的外框（使用RGB格式）
    final_img = cv2.copyMakeBorder(
        resized,
        border_width, border_width, border_width, border_width,
        cv2.BORDER_CONSTANT,
        value=rgb_bg
    )
    return final_img


# 当两个图片都上传后进行处理
if cover_image and spine_image:
    # 读取图片
    cover_img = Image.open(cover_image).convert('RGB')
    spine_img = Image.open(spine_image).convert('RGB')
    
    # 显示上传的图片
    st.subheader("上传的图片预览")
    img_col1, img_col2 = st.columns(2)
    with img_col1:
        st.image(spine_img, caption="书脊图片", width='content')
    with img_col2:
        st.image(cover_img, caption="封面图片", width='content') 
    
    # 生成3D封面
    with st.spinner("正在渲染3D封面..."):
        try:
            # 计算背景色（RGB格式）
            rgb_bg = hex_to_rgb(bg_color)
            # 转换为BGR格式供OpenCV使用
            bgr_bg = rgb_bg[2], rgb_bg[1], rgb_bg[0]
            
            result_image = generate_3d_cover(
                cover_img, spine_img, 
                perspective_angle, book_distance, cover_width
            )

            # 后处理：重置尺寸并添加与背景色相同的外框
            result_image = post_process_3d_cover(result_image, bg_color=bgr_bg)
            
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