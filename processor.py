from PIL import Image
import io
import streamlit as st
from renderer import BookCoverRenderer
from params import UIParams, RenderParams


def process_images(ui_params: UIParams):
    """
    处理上传的图片并生成3D封面
    
    参数:
        ui_params: 封装所有UI参数的数据类实例
    """
    # 检查是否有封面图片和有效的书脊图片
    if not ui_params.cover_image or not ui_params.spine_images:
        return
    
    # 初始化渲染器
    renderer = BookCoverRenderer()
    
    # 读取图片
    try:
        cover_img = Image.open(ui_params.cover_image).convert('RGB')
        
        # 读取所有原始图片（用于预览显示，不应用阴影效果）
        original_spine_img_list = [Image.open(img).convert('RGB') for img in ui_params.spine_images]
        
        # 显示上传的图片预览
        st.subheader("已上传的图片")
        
        # 准备所有要显示的图片列表（封面 + 所有书脊）
        display_images = [cover_img] + original_spine_img_list
        display_captions = ["封面图片"] + [f"书脊图片 {i+1}" for i in range(len(original_spine_img_list))]
        
        # 使用Streamlit原生布局显示图片（从右向左）
        if display_images:
            with st.container():
                reversed_images = list(reversed(display_images))
                reversed_captions = list(reversed(display_captions))
                
                cols = st.columns(len(reversed_images), gap="small")
                
                for i, (img, caption) in enumerate(zip(reversed_images, reversed_captions)):
                    # 计算显示宽度，保持原始宽高比，高度为300px
                    new_width = int(img.size[0] * (300 / img.size[1]))
                    
                    with cols[i]:
                        st.image(img, caption=caption, width=new_width, clamp=True)
                        if new_width > 400:
                            st.caption(f"图片宽度: {new_width}px")
        
        # 读取所有书脊图片用于渲染
        spine_img_list = original_spine_img_list.copy()
        
        # 应用书脊加宽比例（在所有其他处理之前执行）
        if ui_params.spine_width_ratio != 1.0:
            for i, spine_img in enumerate(spine_img_list):
                # 计算新的宽度，保持高度不变
                new_width = int(spine_img.width * ui_params.spine_width_ratio)
                new_height = spine_img.height
                
                # 使用Pillow的resize方法调整图片大小，使用高质量的重采样滤镜
                spine_img_list[i] = spine_img.resize((new_width, new_height), Image.LANCZOS)
    except Exception as e:
        st.error(f"图片读取失败: {str(e)}")
        return
    
    # 生成3D封面
    with st.spinner("正在渲染3D封面..."):
        try:
            # 计算背景透明度
            alpha_value = int(ui_params.bg_alpha * 255 / 100)
            
            # 准备渲染参数
            render_params = RenderParams(
                perspective_angle=ui_params.perspective_angle,
                book_distance=ui_params.book_distance,
                cover_width=ui_params.cover_width,
                bg_color=ui_params.bg_color,
                bg_alpha=alpha_value,
                spine_spread_angle=ui_params.spine_spread_angle,
                camera_height_ratio=ui_params.camera_height_ratio,
                final_size=ui_params.final_size,
                border_percentage=ui_params.border_percentage,
                book_type=ui_params.book_type,
                spine_shadow_mode=ui_params.spine_shadow_mode,
                spine_width_ratio=ui_params.spine_width_ratio,
                stroke_enabled=ui_params.stroke_enabled
            )
            
            # 使用高级方法进行完整的3D封面渲染
            result_image = renderer.render_3d_cover(
                cover_img, spine_img_list,
                render_params.perspective_angle, render_params.book_distance, render_params.cover_width,
                render_params.bg_color, render_params.bg_alpha,
                spine_spread_angle=render_params.spine_spread_angle,
                camera_height_ratio=render_params.camera_height_ratio,
                final_size=render_params.final_size, 
                border_percentage=render_params.border_percentage,
                book_type=render_params.book_type,
                spine_shadow_mode=render_params.spine_shadow_mode,
                stroke_enabled=render_params.stroke_enabled
            )
            
            # 显示结果
            with ui_params.result_placeholder:
                st.image(result_image, width='stretch')
        
            # 准备下载
            buf = io.BytesIO()
            result_pil = Image.fromarray(result_image)
            result_pil.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            # 生成包含上传文件名的下载文件名
            base_file_name = "3d"
            try:
                # 获取上传的封面文件名（不带扩展名）
                if ui_params.cover_image and hasattr(ui_params.cover_image, 'name'):
                    cover_file_name = ui_params.cover_image.name
                    # 移除扩展名
                    cover_name_without_ext = cover_file_name.rsplit('.', 1)[0]
                    # 添加到下载文件名中
                    base_file_name += f"_{cover_name_without_ext}"
            except Exception:
                # 如果获取文件名失败，使用默认名称
                pass
            
            with ui_params.download_placeholder:
                st.download_button(
                    label="下载立体封",
                    data=byte_im,
                    file_name=f"{base_file_name}.png",
                    mime="image/png",
                    type="primary"
                )
                
        except Exception as e:
            st.error(f"渲染过程中出错: {str(e)}")
            st.exception(e)