from PIL import Image
import io
import streamlit as st
from renderer import BookCoverRenderer


def process_images(
    cover_image,              # 上传的封面图片
    spine_image,              # 保持向后兼容性，不使用
    spine_images,             # 上传的多个书脊图片列表（默认使用多书脊模式）
    result_placeholder,       # 渲染结果占位符
    download_placeholder,     # 下载按钮占位符
    book_distance,            # 相机与书距离（mm）
    cover_width,              # 开本宽度（mm）
    perspective_angle,        # 旋转角度（度）
    bg_color,                 # 背景颜色（十六进制）
    bg_alpha,                 # 背景透明度
    spine_spread_angle,       # 书脊额外展开角度
    camera_height_ratio,      # 相机高度比例
    final_size,               # 最终图像尺寸
    border_percentage,        # 边框占最终图像的比例
    book_type,                # 书型（平装/精装）
    spine_shadow_mode         # 书脊阴影模式（无/线性）
):
    """
    处理上传的图片并生成3D封面
    """
    # 检查是否有封面图片和有效的书脊图片
    if not cover_image:
        return
    
    # 默认使用多书脊模式，检查是否有书脊图片
    if not spine_images:
        return
    
    # 初始化渲染器
    renderer = BookCoverRenderer()
    
    # 读取图片
    try:
        cover_img = Image.open(cover_image).convert('RGB')
        
        # 读取所有原始图片（用于预览显示，不应用阴影效果）
        original_spine_img_list = []
        if spine_images:
            original_spine_img_list = [Image.open(img).convert('RGB') for img in spine_images]
        
        # 显示上传的图片预览（使用原始图片，不应用阴影）
        st.subheader("上传的图片预览")
        
        # 准备所有要显示的图片列表（封面 + 所有书脊）
        display_images = []
        display_captions = []
        
        # 默认使用多书脊模式：封面 + 所有原始书脊图片
        display_images = [cover_img] + original_spine_img_list
        display_captions = ["封面图片"] + [f"书脊图片 {i+1}" for i in range(len(original_spine_img_list))]
        
        # 使用Streamlit原生布局显示图片
        if display_images:
            # 创建一个水平容器
            horizontal_container = st.container()
            
            # 在水平容器中创建一个行
            with horizontal_container:
                # 从右向左显示：先反转图片列表
                reversed_images = list(reversed(display_images))
                reversed_captions = list(reversed(display_captions))
                
                # 使用水平布局显示图片
                cols = st.columns(len(reversed_images), gap="small")
                
                # 为每个图片分配一个列
                for i, (img, caption) in enumerate(zip(reversed_images, reversed_captions)):
                    # 计算显示宽度，保持原始宽高比，高度为300px
                    width_percent = 300 / float(img.size[1])
                    new_width = int((float(img.size[0]) * float(width_percent)))
                    
                    # 在对应的列中直接显示原图，并设置显示宽度
                    with cols[i]:
                        st.image(img, caption=caption, width=new_width, clamp=True)
                        # 如果图片特别宽，可以添加横向滚动条
                        if new_width > 400:
                            st.caption(f"图片宽度: {new_width}px")
        
        # 默认使用多书脊模式：读取所有书脊图片
        spine_img_list = [Image.open(img).convert('RGB') for img in spine_images]
    except Exception as e:
        st.error(f"图片读取失败: {str(e)}")
        return
    
    # 统一多书脊和单书脊的预览形式 - 预览逻辑已移至图片读取后立即执行
    # 这样确保预览显示的是原始图片，不会受到阴影处理的影响
    
    # 生成3D封面
    with st.spinner("正在渲染3D封面..."):
        try:
            # 计算背景透明度
            alpha_value = int(bg_alpha * 255 / 100)
            
            # 使用高级方法进行完整的3D封面渲染
            result_image = renderer.render_3d_cover(
                cover_img, spine_img_list,
                perspective_angle, book_distance, cover_width,
                bg_color, alpha_value,
                spine_spread_angle=spine_spread_angle,
                camera_height_ratio=camera_height_ratio,
                final_size=final_size, 
                border_percentage=border_percentage,
                book_type=book_type,
                spine_shadow_mode=spine_shadow_mode
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
                    label="下载立体封",
                    data=byte_im,
                    file_name="3d_book_cover.png",
                    mime="image/png"
                )
                
        except Exception as e:
            st.error(f"渲染过程中出错: {str(e)}")
            st.exception(e)