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
    spine_width = st.slider("书脊宽度 (像素)", 10, 200, 30)
    perspective_angle = st.slider("透视角度", 0, 45, 15)
    thickness_factor = st.slider("厚度因子", 0.1, 2.0, 0.5)
    
    # 渲染参数
    bg_color = st.color_picker("背景颜色", "#ffffff")
    shadow_intensity = st.slider("阴影强度", 0.0, 1.0, 0.3)
    
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
def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return rgb[2], rgb[1], rgb[0]  # BGR格式

# 生成3D封面效果
def generate_3d_cover(cover_img, spine_img, spine_width, perspective_angle, thickness_factor, bg_color, shadow_intensity):
    # 转换PIL图像为OpenCV格式
    cover = cv2.cvtColor(np.array(cover_img), cv2.COLOR_RGB2BGR)
    spine = cv2.cvtColor(np.array(spine_img), cv2.COLOR_RGB2BGR)
    
    # 调整书脊尺寸
    spine = cv2.resize(spine, (spine_width, cover.shape[0]))
    
    # 计算透视变换参数
    h, w = cover.shape[:2]
    angle_rad = np.radians(perspective_angle)
    offset_x = int(thickness_factor * h * np.sin(angle_rad))
    
    # 创建封面透视变换
    cover_points = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    cover_transformed = np.float32([[offset_x, 0], [w + offset_x, 0], [w, h], [0, h]])
    cover_matrix = cv2.getPerspectiveTransform(cover_points, cover_transformed)
    cover_warped = cv2.warpPerspective(cover, cover_matrix, (w + offset_x, h))
    
    # 创建书脊透视变换
    spine_points = np.float32([[0, 0], [spine_width, 0], [spine_width, h], [0, h]])
    spine_transformed = np.float32([[0, 0], [0, offset_x], [spine_width, h + offset_x], [spine_width, h]])
    spine_matrix = cv2.getPerspectiveTransform(spine_points, spine_transformed)
    spine_warped = cv2.warpPerspective(spine, spine_matrix, (spine_width, h + offset_x))
    
    # 创建最终图像 (考虑书脊和封面的尺寸)
    final_width = w + offset_x + spine_width
    final_height = max(h, h + offset_x)
    
    # 创建带背景色的画布
    bgr_bg = hex_to_bgr(bg_color)
    final_image = np.full((final_height, final_width, 3), bgr_bg, dtype=np.uint8)
    
    # 放置封面
    final_image[:h, spine_width:spine_width + w + offset_x] = cover_warped
    
    # 放置书脊
    final_image[:h + offset_x, :spine_width] = spine_warped
    
    # 添加简单阴影效果
    if shadow_intensity > 0:
        shadow_offset = int(offset_x * 0.3)
        # 在封面下方添加阴影
        shadow_region = final_image[h:h + shadow_offset, spine_width:spine_width + w + offset_x]
        shadow_filter = np.ones_like(shadow_region, dtype=np.float32) * (1 - shadow_intensity)
        final_image[h:h + shadow_offset, spine_width:spine_width + w + offset_x] = np.clip(
            shadow_region * shadow_filter, 0, 255).astype(np.uint8)
    
    # 转换回RGB格式
    final_image_rgb = cv2.cvtColor(final_image, cv2.COLOR_BGR2RGB)
    return final_image_rgb

# 当两个图片都上传后进行处理
if cover_image and spine_image:
    # 读取图片
    cover_img = Image.open(cover_image).convert('RGB')
    spine_img = Image.open(spine_image).convert('RGB')
    
    # 显示上传的图片
    st.subheader("上传的图片预览")
    img_col1, img_col2 = st.columns(2)
    with img_col1:
        st.image(cover_img, caption="封面图片", use_column_width=True)
    with img_col2:
        st.image(spine_img, caption="书脊图片", use_column_width=True)
    
    # 生成3D封面
    with st.spinner("正在渲染3D封面..."):
        try:
            result_image = generate_3d_cover(
                cover_img, spine_img, 
                spine_width, perspective_angle, 
                thickness_factor, bg_color, 
                shadow_intensity
            )
            
            # 显示结果
            with result_placeholder:
                st.image(result_image, caption="3D封面渲染结果", use_column_width=True)
            
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