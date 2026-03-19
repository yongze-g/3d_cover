"""
3D图书封面渲染器 - 主入口文件

该应用程序允许用户上传图书封面和书脊图片，通过调整各种参数生成3D立体效果的图书封面。

结构说明：
- side_bar.py: 共享的渲染参数设置
- renderer.py: 封装所有渲染相关功能
- processor.py: 处理图像处理逻辑
- app.py: 主入口文件，协调各模块
- params.py: 定义数据类，封装参数
- big-bang/: 附属功能，PDF封面和书脊提取
"""

import streamlit as st
import sys
import os
import zipfile
from io import BytesIO
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), 'big-bang'))

from side_bar import setup_render_params_sidebar
from processor import process_images
from params import UIParams


def setup_file_upload_section():
    """
    设置文件上传区域
    
    返回:
        tuple: (cover_image, spine_images, result_placeholder, download_placeholder)
    """
    col1, col2 = st.columns(2)

    with col1:
        st.header("上传图片")
        
        if 'example_mode' not in st.session_state:
            st.session_state.example_mode = False
        if 'saved_cover_image' not in st.session_state:
            st.session_state.saved_cover_image = None
        if 'saved_spine_images' not in st.session_state:
            st.session_state.saved_spine_images = []

        if st.button("从印刷文件提取封面和书脊　→", type="secondary", help="使用带血线的PDF印刷文件，提取封面和书脊图片"):
            st.query_params["page"] = "big-bang"
            st.rerun()
        
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
        
        with st.expander("功能演示", expanded=False):
            if st.session_state.example_mode:
                if st.button("关闭示例图片以继续"):
                    st.session_state.example_mode = False
                    st.rerun()
                
                example_dir = "example"
                example_files = ["cover.png", "spine1.png", "spine2.png"]
                
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    for file_name in example_files:
                        file_path = os.path.join(example_dir, file_name)
                        zip_file.write(file_path, file_name)
                zip_buffer.seek(0)
                
                st.download_button(
                    label="下载示例图片",
                    data=zip_buffer,
                    file_name="example_images.zip",
                    mime="application/zip",
                    help="一键下载所有示例图片（封面和书脊）"
                )
            else:
                if st.button("使用示例图片"):
                    st.session_state.saved_cover_image = user_cover_image
                    st.session_state.saved_spine_images = user_spine_images
                    st.session_state.example_mode = True
                    st.rerun()
        
        if st.session_state.example_mode:
            example_dir = "example"
            cover_path = os.path.join(example_dir, "cover.png")
            spine1_path = os.path.join(example_dir, "spine1.png")
            spine2_path = os.path.join(example_dir, "spine2.png")
            
            def image_to_bytesio(image_path):
                img = Image.open(image_path)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                buffer.name = image_path.split(os.path.sep)[-1] if os.path.sep in image_path else image_path
                return buffer
            
            cover_image = image_to_bytesio(cover_path)
            spine_images = [image_to_bytesio(spine1_path), image_to_bytesio(spine2_path)]
        else:
            cover_image = st.session_state.saved_cover_image or user_cover_image
            spine_images = st.session_state.saved_spine_images or user_spine_images

    with col2:
        st.header("渲染结果")
        result_placeholder = st.empty()
        download_placeholder = st.empty()
    
    return cover_image, spine_images, result_placeholder, download_placeholder


def setup_ui():
    """
    设置Streamlit用户界面
    
    返回:
        UIParams: 封装所有UI参数的数据类实例
    """
    if 'spine_spread_angle' not in st.session_state:
        st.session_state.spine_spread_angle = 0
    if 'imported_config' not in st.session_state:
        st.session_state.imported_config = None
    if 'config_processed' not in st.session_state:
        st.session_state.config_processed = False
    
    st.set_page_config(
        page_title="立体封渲染器",
        page_icon="📚",
        layout="wide"
    )

    st.title("立体封渲染器")
    st.write("上传图书封面和书脊图片，调整参数生成专业的立体图书效果")

    render_params = setup_render_params_sidebar()
    
    cover_image, spine_images, result_placeholder, download_placeholder = setup_file_upload_section()
    
    return UIParams(
        cover_image=cover_image,
        spine_images=spine_images,
        result_placeholder=result_placeholder,
        download_placeholder=download_placeholder,
        book_distance=render_params["book_distance"],
        cover_width=render_params["cover_width"],
        perspective_angle=render_params["perspective_angle"],
        bg_color=render_params["bg_color"],
        bg_alpha=render_params["bg_alpha"],
        spine_spread_angle=render_params["spine_spread_angle"],
        camera_height_ratio=render_params["camera_height_ratio"],
        final_size=render_params["final_size"],
        border_percentage=render_params["border_percentage"],
        book_type=render_params["book_type"],
        shadow_mode=render_params["shadow_mode"],
        spine_width_ratio=render_params["spine_width_ratio"],
        stroke_enabled=render_params["stroke_enabled"],
        is_2d=render_params["is_2d"]
    )


def main_app():
    ui_params = setup_ui()
    process_images(ui_params)


def big_bang_app():
    if st.button("← 返回立体封渲染器", type="secondary"):
        st.query_params["page"] = "main"
        st.rerun()
    
    big_bang_app_path = os.path.join(os.path.dirname(__file__), 'big-bang', 'app.py')
    
    big_bang_module = {}
    
    exec(open(big_bang_app_path, 'r', encoding='utf-8').read(), big_bang_module)
    
    big_bang_module['run_big_bang_app']()


def main():
    page = st.query_params.get("page", "main")
    
    if page == "big-bang":
        big_bang_app()
    else:
        main_app()


if __name__ == "__main__":
    main()
