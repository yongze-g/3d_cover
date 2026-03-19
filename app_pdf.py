"""
PDF到3D封面一步生成工具 - Web界面

直接从PDF文件提取封面和书脊，然后生成立体封，无需中间步骤。
支持多个PDF文件：第一个提取封面和书脊，后续只提取书脊。
"""

import streamlit as st
import sys
import os
import tempfile
import shutil
import atexit
import io
from io import BytesIO
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), 'big-bang'))

from pdf_to_images import cut_pdf, pdf_to_image
from cover_spine_generator import find_symmetry_positions
from constants import K_MAX, CENTER_SKIP_WIDTH, CENTER_SKIP_MAX
from renderer import BookCoverRenderer
from side_bar import setup_render_params_sidebar

st.set_page_config(
    page_title="立体封生成器 - PDF整合版",
    page_icon="📚",
    layout="wide"
)

def process_single_pdf(pdf_file, temp_dir, idx, is_first_pdf):
    """
    处理单个PDF文件，提取封面和书脊
    
    返回:
        dict: 包含 cover_path, spine_path, visualize_path, error 等信息
    """
    result = {
        "cover_path": None,
        "spine_path": None,
        "visualize_path": None,
        "error": None,
        "img_path": None
    }
    
    try:
        pdf_path = os.path.join(temp_dir, f"pdf_{idx}_{pdf_file.name}")
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.getbuffer())
        
        img_path = pdf_to_image(pdf_path, temp_dir)
        result["img_path"] = img_path
        
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

def main():
    st.title("立体封生成器 - PDF整合版")
    st.write("上传带出血线的PDF印刷文件，自动提取封面和书脊，生成立体封效果。第一个PDF提取封面和书脊，后续PDF只提取书脊。")
    
    if 'imported_config' not in st.session_state:
        st.session_state['imported_config'] = None
    if 'config_processed' not in st.session_state:
        st.session_state['config_processed'] = False
    
    render_params = setup_render_params_sidebar()
    
    if 'temp_dir' not in st.session_state:
        st.session_state.temp_dir = None
    if 'pdf_results' not in st.session_state:
        st.session_state.pdf_results = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'split_params' not in st.session_state:
        st.session_state.split_params = {}
    
    st.subheader("上传PDF文件")
    uploaded_files = st.file_uploader(
        "仅接受带出血线的PDF文件，不带血线则无法正确识别（可上传多个）", 
        type="pdf", 
        accept_multiple_files=True
    )
    
    st.write("血线识别算法持续优化中，若出现识别错误，可以在WPS中临时删除错误识别的血线，或用纯白色色块临时遮盖。")
    
    if uploaded_files:
        old_files = st.session_state.uploaded_files if st.session_state.uploaded_files else []
        old_names = [f.name for f in old_files] if old_files else []
        new_names = [f.name for f in uploaded_files]
        
        files_changed = (
            len(uploaded_files) != len(st.session_state.uploaded_files) or
            any(f1.name != f2.name for f1, f2 in zip(uploaded_files, st.session_state.uploaded_files))
        )
        
        if files_changed:
            if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
                try:
                    shutil.rmtree(st.session_state.temp_dir)
                except:
                    pass
            
            st.session_state.temp_dir = tempfile.mkdtemp()
            
            old_split_params_by_name = {}
            if st.session_state.split_params:
                for old_idx, old_file in enumerate(old_files):
                    old_key = f"pdf_{old_idx}"
                    if old_key in st.session_state.split_params:
                        old_split_params_by_name[old_file.name] = st.session_state.split_params[old_key]
            
            st.session_state.uploaded_files = uploaded_files
            st.session_state.pdf_results = []
            st.session_state.split_params = {}
            
            for idx, pdf_file in enumerate(uploaded_files):
                result = process_single_pdf(pdf_file, st.session_state.temp_dir, idx, idx == 0)
                st.session_state.pdf_results.append(result)
                
                param_key = f"pdf_{idx}"
                if pdf_file.name in old_split_params_by_name:
                    st.session_state.split_params[param_key] = old_split_params_by_name[pdf_file.name]
                else:
                    st.session_state.split_params[param_key] = {
                        "center_skip_width": CENTER_SKIP_WIDTH,
                        "manual_split_k": 0
                    }
    
    if st.session_state.pdf_results:
        col_left, col_right = st.columns(2)
        
        with col_left:
            all_cover_paths = []
            all_spine_paths = []
            all_valid = True
            
            for idx, (pdf_file, result) in enumerate(zip(st.session_state.uploaded_files, st.session_state.pdf_results)):
                is_first = (idx == 0)
                
                with st.container():
                    st.markdown(f"### {'主文件' if is_first else f'书脊文件 {idx}'}: {pdf_file.name}")
                    
                    param_key = f"pdf_{idx}"
                    if param_key not in st.session_state.split_params:
                        st.session_state.split_params[param_key] = {
                            "center_skip_width": CENTER_SKIP_WIDTH,
                            "manual_split_k": 0
                        }
                    
                    param_col1, param_col2 = st.columns(2)
                    with param_col1:
                        center_skip_width = st.slider(
                            "中间跳过区域宽度（像素）",
                            min_value=0,
                            max_value=CENTER_SKIP_MAX,
                            value=st.session_state.split_params[param_key]["center_skip_width"],
                            help="横向扫描时跳过图片中间区域的宽度，用于避开中间的血线干扰",
                            key=f"center_skip_width_{idx}"
                        )
                        st.session_state.split_params[param_key]["center_skip_width"] = center_skip_width
                    
                    with param_col2:
                        manual_split_k = st.slider(
                            "手动分割位置k",
                            min_value=0,
                            max_value=K_MAX,
                            value=st.session_state.split_params[param_key]["manual_split_k"],
                            help=f"取值范围为0到{K_MAX}，如果为0则按默认逻辑处理",
                            key=f"manual_split_k_{idx}"
                        )
                        st.session_state.split_params[param_key]["manual_split_k"] = manual_split_k
                    
                    if result.get("img_path"):
                        try:
                            with st.spinner(f"处理 {pdf_file.name}..."):
                                symmetry_positions, visualize_path, _ = find_symmetry_positions(
                                    result["img_path"], st.session_state.temp_dir, 
                                    directions=["horizontal", "vertical"], 
                                    center_skip_width=center_skip_width,
                                    manual_split_k=manual_split_k
                                )
                                
                                pdf_path = os.path.join(st.session_state.temp_dir, f"pdf_{idx}_{pdf_file.name}")
                                cover_path, spine_path = cut_pdf(
                                    pdf_path, 
                                    st.session_state.temp_dir, 
                                    center_skip_width, 
                                    manual_split_k
                                )
                                
                                unique_cover_path = os.path.join(st.session_state.temp_dir, f"cover_{idx}.jpg")
                                unique_spine_path = os.path.join(st.session_state.temp_dir, f"spine_{idx}.jpg")
                                unique_visualize_path = os.path.join(st.session_state.temp_dir, f"visualize_{idx}.png")
                                
                                if cover_path and os.path.exists(cover_path):
                                    shutil.copy(cover_path, unique_cover_path)
                                    cover_path = unique_cover_path
                                if spine_path and os.path.exists(spine_path):
                                    shutil.copy(spine_path, unique_spine_path)
                                    spine_path = unique_spine_path
                                if visualize_path and os.path.exists(visualize_path):
                                    shutil.copy(visualize_path, unique_visualize_path)
                                    visualize_path = unique_visualize_path
                                
                                st.session_state.pdf_results[idx]["cover_path"] = cover_path
                                st.session_state.pdf_results[idx]["spine_path"] = spine_path
                                st.session_state.pdf_results[idx]["visualize_path"] = visualize_path
                            
                            if cover_path and spine_path:
                                st.subheader("界限预览")
                                st.image(visualize_path, width='stretch')
                                
                                if is_first:
                                    all_cover_paths.append(cover_path)
                                all_spine_paths.append(spine_path)
                            else:
                                st.error("处理失败，请检查PDF文件是否符合要求")
                                all_valid = False
                        except Exception as e:
                            st.error(f"处理错误: {str(e)}")
                            all_valid = False
                    else:
                        st.error("PDF转换失败")
                        all_valid = False
                    
                    if idx < len(st.session_state.uploaded_files) - 1:
                        st.divider()
        
        with col_right:
            if all_valid and all_cover_paths and all_spine_paths:
                st.subheader("立体封渲染")
                
                with st.spinner("正在渲染立体封……"):
                    cover_img = Image.open(all_cover_paths[0]).convert('RGB')
                    spine_imgs = [Image.open(sp).convert('RGB') for sp in all_spine_paths]
                    
                    if render_params["spine_width_ratio"] != 1.0:
                        resized_spine_imgs = []
                        for spine_img in spine_imgs:
                            new_width = int(spine_img.width * render_params["spine_width_ratio"])
                            new_height = spine_img.height
                            resized_spine_imgs.append(spine_img.resize((new_width, new_height), Image.LANCZOS))
                        spine_imgs = resized_spine_imgs
                    
                    renderer = BookCoverRenderer()
                    
                    alpha_value = int(render_params["bg_alpha"] * 255 / 100)
                    
                    result_image = renderer.render_3d_cover(
                        cover_img, spine_imgs,
                        render_params["perspective_angle"],
                        render_params["book_distance"],
                        render_params["cover_width"],
                        render_params["bg_color"],
                        alpha_value,
                        spine_spread_angle=render_params["spine_spread_angle"],
                        camera_height_ratio=render_params["camera_height_ratio"],
                        final_size=render_params["final_size"],
                        border_percentage=render_params["border_percentage"],
                        book_type=render_params["book_type"],
                        shadow_mode=render_params["shadow_mode"],
                        stroke_enabled=render_params["stroke_enabled"],
                        is_2d=render_params["is_2d"]
                    )
                    
                    st.image(result_image, width='stretch')
                    
                    buf = io.BytesIO()
                    result_pil = Image.fromarray(result_image)
                    result_pil.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    base_file_name = "3d"
                    try:
                        if st.session_state.uploaded_files:
                            first_pdf_name = st.session_state.uploaded_files[0].name
                            pdf_name_without_ext = first_pdf_name.rsplit('.', 1)[0]
                            base_file_name += f"_{pdf_name_without_ext}"
                    except Exception:
                        pass
                    
                    st.download_button(
                        label="下载立体封",
                        data=byte_im,
                        file_name=f"{base_file_name}.png",
                        mime="image/png",
                        type="primary"
                    )
            else:
                st.info("请在左侧调整各PDF的分割参数以提取封面和书脊")
    
    def cleanup_temp_dir():
        if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
            try:
                shutil.rmtree(st.session_state.temp_dir)
            except:
                pass
    
    if 'cleanup_registered' not in st.session_state:
        atexit.register(cleanup_temp_dir)
        st.session_state.cleanup_registered = True

if __name__ == "__main__":
    main()
