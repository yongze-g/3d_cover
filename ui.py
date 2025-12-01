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
    st.title("📚 立体封渲染器")
    st.write("上传图书封面和书脊图片，调整参数生成专业的立体图书效果")

    # 侧边栏 - 参数调整
    with st.sidebar:
        st.header("参数设置")
        
        # 使用expander实现折叠设置
        with st.expander("高级设置", expanded=False):
            # 透视参数
            st.subheader("透视参数")
            book_distance = st.slider("相机与书距离（mm）", 300, 1000, 800)
            camera_height_ratio = st.slider("相机相对高度比例", 0.0, 1.0, 0.5, help="控制3D视角的垂直位置，0表示底部，1表示顶部")
            
            # 输出图像参数
            st.subheader("输出图像参数")
            final_size = st.slider("最终图像尺寸（像素）", 800, 2000, 1200, step=100)
            border_percentage = st.slider("边框占比", 0.0, 0.2, 0.1, step=0.01)

        # 书型选择
        book_type = st.radio(
            "选择书型",
            options=["平装", "精装"],
            index=0,
        )

        cover_width = st.slider("开本宽度（mm）", 120, 200, 187, 
                                help="成品图基于真实空间尺寸计算，开本宽度不同会导致3D效果的深度不同会导致透视程度不同") 
    
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
            help="如果书脊太窄，可以额外展开，最大可以展至完全面向正面.推荐为0。该滑条允许值会自动计算",
            key="spine_spread_angle"
        )
        
        # 渲染参数
        bg_color = st.color_picker("背景颜色", "#ffffff")
        bg_alpha = st.slider("背景不透明度", 0, 100, 100)

    # 主内容区域 - 文件上传和渲染
    col1, col2 = st.columns(2)

    with col1:
        st.header("上传图片")
        cover_image = st.file_uploader("上传封面图片", type=["png", "jpg", "jpeg"])
        
        # 默认使用多书脊模式，支持上传多个文件
        spine_images = st.file_uploader(
            "上传书脊图片（可上传多个）", 
            type=["png", "jpg", "jpeg"], 
            help="对于套书，可以从前到后依次上传书脊。书脊会缩放至统一高度处理", 
            accept_multiple_files=True
        )

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
        spine_shadow_mode=spine_shadow_mode
    )
