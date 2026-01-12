import streamlit as st
from params import UIParams


def setup_ui():
    """
    设置Streamlit用户界面
    
    返回:
        UIParams: 封装所有UI参数的数据类实例
    """
    # 初始化session_state以保存状态值
    if 'spine_spread_angle' not in st.session_state:
        st.session_state.spine_spread_angle = 0
    
    # 设置页面配置
    st.set_page_config(
        page_title="立体封渲染器",
        page_icon="📚",
        layout="wide"
    )

    # 页面标题和说明
    st.title("立体封渲染器")
    st.write("上传图书封面和书脊图片，调整参数生成专业的立体图书效果")

    # 侧边栏 - 参数调整
    with st.sidebar:
        
        st.header("参数设置")
        
        # 书型选择
        book_type = st.radio(
            "选择书型",
            options=["平装", "精装"],
            index=0,
        )

        cover_width = st.slider("开本宽度（mm）", 120, 200, 187, 
                                help="成品图基于真实空间尺寸计算，开本宽度不同会导致透视关系不同，请选择该书真实的开本宽度") 
    
        # 书脊阴影模式选择
        spine_shadow_mode = st.radio(
            "书脊阴影模式",
            options=["无", "线性", "反射"],
            index=1
        )
        
        perspective_angle = st.slider("旋转角度（°）", 1, 89, 35)
        
        # 计算最大允许的书脊额外展开角度
        max_spine_spread_angle = 90 - perspective_angle
        
        # 如果当前保存的值超过新的上限，则截断
        if st.session_state.spine_spread_angle > max_spine_spread_angle:
            st.session_state.spine_spread_angle = max_spine_spread_angle
        
        # 使用key参数绑定组件与session_state
        spine_spread_angle = st.slider(
            "书脊额外展开角度（°）", 
            0, 
            max_spine_spread_angle, 
            st.session_state.spine_spread_angle, 
            help="如果书脊太窄，可以额外展开，最大可以展至完全面向正面.推荐为0。该滑条允许值会自动计算。注意：额外展开书脊会使得书脊的角度不符合真实透视关系",
            key="spine_spread_angle"
        )
        
        # 书脊加宽比例
        spine_width_ratio = st.slider(
            "书脊拉伸", 
            1.0, 
            2.0, 
            1.0, 
            step=0.05,
            help="如果书脊的视觉展示效果过薄，可在此按比例拉宽书脊，默认为1（即不拉伸）。注意：拉伸会使得书脊的宽度不符合真实透视关系"
        )
        
        # 使用expander实现折叠设置
        with st.expander("高级设置", expanded=False):
            # 透视参数
            st.subheader("透视参数")
            book_distance = st.slider("相机与书距离（mm）", 300, 1000, 800)
            camera_height_ratio = st.slider("相机相对高度比例", 0.0, 1.0, 0.5, help="控制3D视角的垂直位置，0表示底部，1表示顶部")
            
            # 输出图像参数
            st.subheader("输出图像参数")
            final_size = st.slider("最终图像尺寸（像素）", 800, 2000, 1200, step=100)
            border_percentage = st.slider("边框占比", 0.0, 0.2, 0.05, step=0.01)
            
            # 渲染参数
            st.subheader("渲染参数")
            bg_color = st.color_picker("背景颜色", "#ffffff")
            bg_alpha = st.slider("背景不透明度", 0, 100, 100)

    # 主内容区域 - 文件上传和渲染
    col1, col2 = st.columns(2)

    with col1:
        st.header("上传图片")
        
        # 初始化状态
        if 'example_mode' not in st.session_state:
            st.session_state.example_mode = False
        if 'saved_cover_image' not in st.session_state:
            st.session_state.saved_cover_image = None
        if 'saved_spine_images' not in st.session_state:
            st.session_state.saved_spine_images = []
        
        # 正常上传功能（始终显示，用于保存用户选择）
        # 但仅在非示例模式下可用
        user_cover_image = st.file_uploader(
            "上传封面图片", 
            type=["png", "jpg", "jpeg"],
            disabled=st.session_state.example_mode
        )
        
        user_spine_images = st.file_uploader(
            "上传书脊图片（可上传多个）", 
            type=["png", "jpg", "jpeg"], 
            help="对于套书，可以从前到后依次上传书脊。书脊会缩放至统一高度处理", 
            accept_multiple_files=True,
            disabled=st.session_state.example_mode
        )
        
        # 示例按钮功能
        if st.session_state.example_mode:
            if st.button("关闭示例图片以继续"):
                st.session_state.example_mode = False
                st.rerun()
            
            # 下载示例图片按钮
            import os
            import zipfile
            from io import BytesIO
            
            # 准备示例图片路径
            example_dir = "example"
            example_files = ["cover.png", "spine1.png", "spine2.png"]
            
            # 创建内存中的zip文件
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for file_name in example_files:
                    file_path = os.path.join(example_dir, file_name)
                    zip_file.write(file_path, file_name)
            zip_buffer.seek(0)
            
            # 提供下载按钮
            st.download_button(
                label="下载示例图片",
                data=zip_buffer,
                file_name="example_images.zip",
                mime="application/zip",
                help="一键下载所有示例图片（封面和书脊）"
            )
        else:
            if st.button("使用示例图片"):
                # 保存用户当前上传的文件
                st.session_state.saved_cover_image = user_cover_image
                st.session_state.saved_spine_images = user_spine_images
                st.session_state.example_mode = True
                st.rerun()
        
        # 根据示例模式决定使用的图片
        if st.session_state.example_mode:
            # 使用示例图片
            import os
            from io import BytesIO
            from PIL import Image
            
            # 获取示例图片路径
            example_dir = "example"
            cover_path = os.path.join(example_dir, "cover.png")
            spine1_path = os.path.join(example_dir, "spine1.png")
            spine2_path = os.path.join(example_dir, "spine2.png")
            
            # 读取示例图片并转换为BytesIO对象，模拟上传文件
            def image_to_bytesio(image_path):
                img = Image.open(image_path)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                # 手动提取文件名，避免使用os.basename
                buffer.name = image_path.split(os.path.sep)[-1] if os.path.sep in image_path else image_path
                return buffer
            
            cover_image = image_to_bytesio(cover_path)
            spine_images = [image_to_bytesio(spine1_path), image_to_bytesio(spine2_path)]
        else:
            # 恢复用户之前上传的文件，如果没有则使用当前上传的
            cover_image = st.session_state.saved_cover_image or user_cover_image
            spine_images = st.session_state.saved_spine_images or user_spine_images

        # 使用查询参数切换到big-bang功能
        if st.button("从PDF提取封面和书脊→", type="secondary"):
            st.query_params["page"] = "big-bang"
            st.rerun()

    with col2:
        st.header("渲染结果")
        result_placeholder = st.empty()
        download_placeholder = st.empty()
    
    # 使用UIParams数据类封装并返回所有参数
    return UIParams(
        cover_image=cover_image,
        spine_images=spine_images,
        result_placeholder=result_placeholder,
        download_placeholder=download_placeholder,
        book_distance=book_distance,
        cover_width=cover_width,
        perspective_angle=perspective_angle,
        bg_color=bg_color,
        bg_alpha=bg_alpha,
        spine_spread_angle=st.session_state.spine_spread_angle,
        camera_height_ratio=camera_height_ratio,
        final_size=final_size,
        border_percentage=border_percentage,
        book_type=book_type,
        spine_shadow_mode=spine_shadow_mode,
        spine_width_ratio=spine_width_ratio
    )
