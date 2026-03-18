"""
PDF到3D封面一步生成工具 - Web界面

直接从PDF文件提取封面和书脊，然后生成立体封，无需中间步骤。
"""

import streamlit as st
import sys
import os
import tempfile
import shutil
import atexit
import io
import json
from io import BytesIO
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), 'big-bang'))

from pdf_to_images import cut_pdf, pdf_to_image
from cover_spine_generator import find_symmetry_positions
from constants import K_MAX, CENTER_SKIP_WIDTH, CENTER_SKIP_MAX
from renderer import BookCoverRenderer

st.set_page_config(
    page_title="PDF到3D封面",
    page_icon="📚",
    layout="wide"
)

def get_config_value(imported_config, key, default):
    if imported_config and key in imported_config:
        return imported_config[key]
    return default

def setup_sidebar(imported_config):
    with st.sidebar:
        st.header("3D渲染参数设置")
        
        book_type = st.radio(
            "选择书型",
            options=["平装", "精装"],
            index=["平装", "精装"].index(get_config_value(imported_config, "book_type", "平装")),
        )

        cover_width = st.slider("开本宽度（mm）", 120, 200, get_config_value(imported_config, "cover_width", 187), 
                                help="成品图基于真实空间尺寸计算，开本宽度不同会导致透视关系不同，请选择该书真实的开本宽度") 
        
        shadow_mode = st.radio(
            "阴影模式",
            options=["无", "线性", "反射", "阴影"],
            index=["无", "线性", "反射", "阴影"].index(get_config_value(imported_config, "shadow_mode", "线性"))
        )
        
        perspective_angle = st.slider("旋转角度（°）", 1, 89, get_config_value(imported_config, "perspective_angle", 35))
        
        max_spine_spread_angle = 90 - perspective_angle
        
        if 'spine_spread_angle' not in st.session_state:
            st.session_state.spine_spread_angle = get_config_value(imported_config, "spine_spread_angle", 0)
        
        current_spine_spread_angle = st.session_state.spine_spread_angle
        
        if current_spine_spread_angle > max_spine_spread_angle:
            current_spine_spread_angle = max_spine_spread_angle
            st.session_state.spine_spread_angle = current_spine_spread_angle
        
        spine_spread_angle = st.slider(
            "书脊额外展开角度（°）", 
            0, 
            max_spine_spread_angle, 
            current_spine_spread_angle, 
            help="如果书脊太窄，可以额外展开，最大可以展至完全面向正面.推荐为0。该滑条允许值会自动计算。注意：额外展开书脊会使得书脊的角度不符合真实透视关系",
            key="spine_spread_angle"
        )
        
        spine_width_ratio = st.slider(
            "书脊拉伸", 
            1.0, 
            2.0, 
            get_config_value(imported_config, "spine_width_ratio", 1.0), 
            step=0.05,
            help="如果书脊的视觉展示效果过薄，可在此按比例拉宽书脊，默认为1（即不拉伸）。注意：拉伸会使得书脊的宽度不符合真实透视关系"
        )
        
        stroke_enabled = st.checkbox("封面描边", value=get_config_value(imported_config, "stroke_enabled", False), help="为封面和书脊添加细灰色边框，突出显示图书轮廓")
        
        with st.expander("高级设置", expanded=False):
            st.subheader("透视参数")
            book_distance = st.slider("相机与书距离（mm）", 300, 1000, get_config_value(imported_config, "book_distance", 800))
            camera_height_ratio = st.slider("相机相对高度比例", 0.0, 1.0, get_config_value(imported_config, "camera_height_ratio", 0.5), help="控制3D视角的垂直位置，0表示底部，1表示顶部")
            
            st.subheader("输出图像参数")
            final_size = st.slider("最终图像尺寸（像素）", 800, 2000, get_config_value(imported_config, "final_size", 1200), step=100)
            border_percentage = st.slider("边框占比", 0.0, 0.2, get_config_value(imported_config, "border_percentage", 0.05), step=0.01)
            
            st.subheader("渲染参数")
            bg_color = st.color_picker("背景颜色", get_config_value(imported_config, "bg_color", "#ffffff"))
            bg_alpha = st.slider("背景不透明度", 0, 100, get_config_value(imported_config, "bg_alpha", 100))
            
            settings = {
                "book_type": book_type,
                "cover_width": cover_width,
                "shadow_mode": shadow_mode,
                "perspective_angle": perspective_angle,
                "spine_spread_angle": st.session_state.spine_spread_angle,
                "spine_width_ratio": spine_width_ratio,
                "stroke_enabled": stroke_enabled,
                "book_distance": book_distance,
                "camera_height_ratio": camera_height_ratio,
                "final_size": final_size,
                "border_percentage": border_percentage,
                "bg_color": bg_color,
                "bg_alpha": bg_alpha
            }
        
        with st.expander("配置管理", expanded=False):
            json_data = json.dumps(settings, indent=2, ensure_ascii=False)
            json_bytes = BytesIO(json_data.encode('utf-8'))

            st.write("你可以随时将现有配置导出为文件下载，也可以导入已有的配置文件。")
            
            st.download_button(
                label="导出当前配置",
                data=json_bytes,
                file_name="3d_cover_settings.json",
                mime="application/json"
            )

            uploaded_config = st.file_uploader(
                "导入配置文件（JSON）",
                type=["json"]
            )

            if uploaded_config is not None and not st.session_state.get('config_processed', False):
                try:
                    config_data = json.load(uploaded_config)
                    st.session_state['imported_config'] = config_data
                    st.session_state['config_processed'] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"配置导入失败: {str(e)}")
            elif uploaded_config is None:
                st.session_state['config_processed'] = False
    
    return {
        "book_type": book_type,
        "cover_width": cover_width,
        "shadow_mode": shadow_mode,
        "perspective_angle": perspective_angle,
        "spine_spread_angle": spine_spread_angle,
        "spine_width_ratio": spine_width_ratio,
        "stroke_enabled": stroke_enabled,
        "book_distance": book_distance,
        "camera_height_ratio": camera_height_ratio,
        "final_size": final_size,
        "border_percentage": border_percentage,
        "bg_color": bg_color,
        "bg_alpha": bg_alpha
    }

def main():
    st.title("PDF到3D封面一步生成")
    st.write("上传带出血线的PDF印刷文件，自动提取封面和书脊，生成3D立体封面效果")
    
    if 'imported_config' not in st.session_state:
        st.session_state['imported_config'] = None
    if 'config_processed' not in st.session_state:
        st.session_state['config_processed'] = False
    
    render_params = setup_sidebar(st.session_state.get('imported_config'))
    
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'temp_dir' not in st.session_state:
        st.session_state.temp_dir = None
    if 'pdf_path' not in st.session_state:
        st.session_state.pdf_path = None
    if 'img_path' not in st.session_state:
        st.session_state.img_path = None
    if 'img_width' not in st.session_state:
        st.session_state.img_width = 0
    if 'cover_path' not in st.session_state:
        st.session_state.cover_path = None
    if 'spine_path' not in st.session_state:
        st.session_state.spine_path = None
    if 'visualize_path' not in st.session_state:
        st.session_state.visualize_path = None
    
    st.subheader("上传PDF文件")
    uploaded_file = st.file_uploader("仅接受带出血线的PDF文件，不带血线则无法正确识别", type="pdf")
    
    if uploaded_file != st.session_state.uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        
        if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
            try:
                shutil.rmtree(st.session_state.temp_dir)
            except:
                pass
        
        if uploaded_file:
            st.session_state.temp_dir = tempfile.mkdtemp()
            st.session_state.pdf_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
            with open(st.session_state.pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.session_state.img_path = pdf_to_image(st.session_state.pdf_path, st.session_state.temp_dir)
            
            img = Image.open(st.session_state.img_path)
            st.session_state.img_width = img.size[0]
            
            st.session_state.cover_path = None
            st.session_state.spine_path = None
            st.session_state.visualize_path = None
        else:
            st.session_state.temp_dir = None
            st.session_state.pdf_path = None
            st.session_state.img_path = None
            st.session_state.img_width = 0
            st.session_state.cover_path = None
            st.session_state.spine_path = None
            st.session_state.visualize_path = None
    
    st.write("血线识别算法持续优化中，若出现识别错误，可以在WPS中临时删除错误识别的血线，或用纯白色色块临时遮盖。")
    
    if st.session_state.pdf_path and st.session_state.img_path:
        try:
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("PDF分割参数")
                
                center_skip_width = st.slider(
                    "中间跳过区域宽度（像素）",
                    min_value=0,
                    max_value=CENTER_SKIP_MAX,
                    value=CENTER_SKIP_WIDTH,
                    help="横向扫描时跳过图片中间区域的宽度，用于避开中间的血线干扰，为0时不跳过中间区域",
                    key="center_skip_width_slider"
                )
                
                manual_split_k = st.slider(
                    "手动第一次分割位置k",
                    min_value=0,
                    max_value=K_MAX,
                    value=0,
                    help=f"取值范围为0到{K_MAX}，如果为0则按默认逻辑处理，否则以中间位置m加减k作为第一组分割",
                    key="manual_split_k_slider"
                )
                
                with st.spinner("正在处理PDF文件..."):
                    symmetry_positions, visualize_path, _ = find_symmetry_positions(
                        st.session_state.img_path, st.session_state.temp_dir, 
                        directions=["horizontal", "vertical"], 
                        center_skip_width=center_skip_width,
                        manual_split_k=manual_split_k
                    )
                    
                    cover_path, spine_path = cut_pdf(
                        st.session_state.pdf_path, 
                        st.session_state.temp_dir, 
                        center_skip_width, 
                        manual_split_k
                    )
                    
                    st.session_state.cover_path = cover_path
                    st.session_state.spine_path = spine_path
                    st.session_state.visualize_path = visualize_path
                
                if cover_path and spine_path:
                    st.subheader("界限预览")
                    st.image(visualize_path, width='stretch')
                else:
                    st.error("处理失败，请检查PDF文件是否符合要求")
            
            with col_right:
                if st.session_state.cover_path and st.session_state.spine_path:
                    st.subheader("3D封面渲染")
                    
                    with st.spinner("正在渲染3D封面..."):
                        cover_img = Image.open(st.session_state.cover_path).convert('RGB')
                        spine_img = Image.open(st.session_state.spine_path).convert('RGB')
                        
                        if render_params["spine_width_ratio"] != 1.0:
                            new_width = int(spine_img.width * render_params["spine_width_ratio"])
                            new_height = spine_img.height
                            spine_img = spine_img.resize((new_width, new_height), Image.LANCZOS)
                        
                        renderer = BookCoverRenderer()
                        
                        alpha_value = int(render_params["bg_alpha"] * 255 / 100)
                        
                        result_image = renderer.render_3d_cover(
                            cover_img, [spine_img],
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
                            stroke_enabled=render_params["stroke_enabled"]
                        )
                        
                        st.image(result_image, width='stretch')
                        
                        buf = io.BytesIO()
                        result_pil = Image.fromarray(result_image)
                        result_pil.save(buf, format="PNG")
                        byte_im = buf.getvalue()
                        
                        base_file_name = "3d"
                        try:
                            if st.session_state.uploaded_file and hasattr(st.session_state.uploaded_file, 'name'):
                                pdf_file_name = st.session_state.uploaded_file.name
                                pdf_name_without_ext = pdf_file_name.rsplit('.', 1)[0]
                                base_file_name += f"_{pdf_name_without_ext}"
                        except Exception:
                            pass
                        
                        st.download_button(
                            label="下载3D封面",
                            data=byte_im,
                            file_name=f"{base_file_name}.png",
                            mime="image/png",
                            type="primary"
                        )
                else:
                    st.info("请先在左侧调整分割参数以提取封面和书脊")
                    
        except Exception as e:
            st.error(f"处理过程中发生错误: {str(e)}")
            st.exception(e)
    
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
