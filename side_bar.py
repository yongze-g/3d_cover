import streamlit as st
import json
from io import BytesIO
from params import UIParams


def get_config_value(imported_config, key, default):
    """获取配置值的辅助函数"""
    if imported_config and key in imported_config:
        return imported_config[key]
    return default


def setup_render_params_sidebar(imported_config=None):
    """
    设置渲染参数侧边栏（共享函数）
    
    此函数被 app.py 和 app_pdf.py 共同使用，用于设置3D渲染参数。
    
    参数:
        imported_config: 导入的配置字典（可选）
    
    返回:
        dict: 包含所有渲染参数的字典
    """
    if imported_config is None:
        imported_config = st.session_state.get('imported_config', None)
    
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
