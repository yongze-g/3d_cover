from PIL import Image
import io
import streamlit as st
from renderer import BookCoverRenderer


def process_images(cover_image, spine_image, result_placeholder, download_placeholder,
                   book_distance, cover_width, perspective_angle, bg_color, bg_alpha, spine_spread_angle=0, camera_height_ratio=0.5):
    """
    处理上传的图片并生成3D封面
    
    参数:
        cover_image: 上传的封面图片
        spine_image: 上传的书脊图片
        result_placeholder: 渲染结果占位符
        download_placeholder: 下载按钮占位符
        book_distance: 相机与书距离（mm）
        cover_width: 开本宽度（mm）
        perspective_angle: 旋转角度（度）
        bg_color: 背景颜色（十六进制）
        bg_alpha: 背景不透明度（0-100）
        spine_spread_angle: 书脊额外展开角度（度）
        camera_height_ratio: 相机相对高度比例（0-1）
    """
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
                bg_color_bgr=bgr_bg, bg_alpha=alpha_value,
                spine_spread_angle=spine_spread_angle,
                camera_height_ratio=camera_height_ratio
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