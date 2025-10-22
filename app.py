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
    
    # 渲染参数 (注释掉颜色和阴影相关参数)
    # bg_color = st.color_picker("背景颜色", "#ffffff")
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

# 转换颜色十六进制值为BGR格式 (注释掉颜色转换函数)
# def hex_to_bgr(hex_color):
#     hex_color = hex_color.lstrip('#')
#     rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
#     return rgb[2], rgb[1], rgb[0]  # BGR格式

# 生成3D封面效果
def generate_3d_cover(cover_img, spine_img, perspective_angle, book_distance, cover_width):
    # 转换PIL图像为OpenCV格式 (仅保留图像数据，暂不进行颜色空间转换)
    cover = np.array(cover_img)
    spine = np.array(spine_img)
    
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

    # 创建封面透视变换
    cover_points = np.float32([[0, 0], [original_cover_image_width, 0], \
        [original_cover_image_width, original_cover_image_height], [0, original_cover_image_height]])
    cover_transformed = np.float32([[0, 0], [display_cover_width,  transformed_offset_y_top], \
        [display_cover_width, cover_height - transformed_offset_y_bottom], [0, cover_height]])
    cover_matrix = cv2.getPerspectiveTransform(cover_points, cover_transformed)
    cover_warped = cv2.warpPerspective(cover, cover_matrix, (int(display_cover_width), int(cover_height)))
    
    # 创建书脊透视变换
    spine_points = np.float32([[0, 0], [original_spine_image_width, 0], \
        [original_spine_image_width, original_spine_image_height], [0, original_spine_image_height]])
    spine_transformed = np.float32([[0, transformed_spine_offset_y_top], [display_spine_width, 0], \
        [display_spine_width, spine_height], [0, spine_height - transformed_spine_offset_y_bottom]])
    spine_matrix = cv2.getPerspectiveTransform(spine_points, spine_transformed)
    spine_warped = cv2.warpPerspective(spine, spine_matrix, (int(display_spine_width), int(spine_height)))
    
    # 创建最终图像 (考虑书脊和封面的尺寸)
    final_width =  int(display_cover_width) + int(display_spine_width)
    final_height = max(int(cover_height), int(spine_height))
    
    # 创建带背景色的画布 (使用白色背景)
    # bgr_bg = hex_to_bgr(bg_color)
    final_image = np.full((final_height, final_width, 3), 255, dtype=np.uint8)
    
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
    
    # 直接返回图像，不需要颜色空间转换
    return final_image

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
            result_image = generate_3d_cover(
                cover_img, spine_img, 
                perspective_angle, book_distance, cover_width
            )
            
            # 显示结果
            with result_placeholder:
                st.image(result_image, caption="3D封面渲染结果", width='content')
        
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