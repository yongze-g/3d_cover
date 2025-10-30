import streamlit as st


def setup_ui():
    """
    设置Streamlit用户界面
    
    返回:
        cover_image: 上传的封面图片
        spine_image: 上传的单个书脊图片（单书脊模式）
        spine_images: 上传的多个书脊图片列表（多书脊模式）
        result_placeholder: 渲染结果占位符
        download_placeholder: 下载按钮占位符
        book_distance: 相机与书距离（mm）
        cover_width: 开本宽度（mm）
        perspective_angle: 旋转角度（度）
        bg_color: 背景颜色（十六进制）
        bg_alpha: 背景不透明度（0-100）
        spine_spread_angle: 书脊额外展开角度（度）
        camera_height_ratio: 相机相对高度比例（0-1）
        final_size: 最终图像尺寸（像素）
        border_percentage: 边框占比
        multi_spine_mode: 是否启用多书脊模式
        book_type: 书型（平装/精装）
    """
    # 初始化session_state以保存状态值
    if 'spine_spread_angle' not in st.session_state:
        st.session_state.spine_spread_angle = 0
    
    # 初始化多书脊模式开关状态
    if 'multi_spine_mode' not in st.session_state:
        st.session_state.multi_spine_mode = False
    
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
            # 图书尺寸参数
            st.subheader("透视参数")
            book_distance = st.slider("相机与书距离（mm）", 300, 1000, 800)
            camera_height_ratio = st.slider("相机相对高度比例", 0.0, 1.0, 0.5, help="控制3D视角的垂直位置，0表示底部，1表示顶部")
            
            # 输出图像参数
            st.subheader("输出图像参数")
            final_size = st.slider("最终图像尺寸（像素）", 800, 2000, 1200, step=100)
            border_percentage = st.slider("边框占比", 0.0, 0.2, 0.1, step=0.01)

        with st.expander("未完成功能", expanded=False):
            # 添加书型选择（平装/精装）
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
            options=["无", "线性"],
            index=1
        )
        
        perspective_angle = st.slider("旋转角度（°）", 1, 89, 35)
        
        # 计算最大允许的书脊额外展开角度
        max_spine_spread_angle = 90 - perspective_angle
        
        # 如果当前保存的值超过新的上限，则截断
        if st.session_state.spine_spread_angle > max_spine_spread_angle:
            st.session_state.spine_spread_angle = max_spine_spread_angle
        
        # 使用key参数绑定组件与session_state，同时保留默认值逻辑
        # 这样既可以在perspective_angle改变时保留值，又能解决滑块弹回问题
        spine_spread_angle = st.slider(
            "书脊额外展开角度（°）", 
            0, 
            max_spine_spread_angle, 
            st.session_state.spine_spread_angle, 
            help="如果书脊太窄，可以额外展开，最大可以展至完全面向正面.推荐为0。该滑条允许值会自动计算",
            key="spine_spread_angle"  # 添加key参数实现自动绑定
        )
        
        # 不需要手动更新，因为key参数已经实现了自动绑定
        
        
        # 渲染参数
        bg_color = st.color_picker("背景颜色", "#ffffff")
        bg_alpha = st.slider("背景不透明度", 0, 100, 100)

    # 主内容区域 - 文件上传和渲染
    col1, col2 = st.columns(2)

    with col1:
        st.header("上传图片")
        cover_image = st.file_uploader("上传封面图片", type=["png", "jpg", "jpeg"])
        
        # 多书脊模式开关，位于上传书脊边上
        multi_spine_mode = st.checkbox("启用多书脊模式", value=False, 
                                       help="套书请启用多书脊模式，并按从前到后顺序上传书脊")
        # 更新session_state
        st.session_state.multi_spine_mode = multi_spine_mode
        
        # 根据多书脊模式选择上传组件
        if st.session_state.multi_spine_mode:
            # 多书脊模式 - 支持上传多个文件
            spine_images = st.file_uploader("上传书脊图片（多个）", type=["png", "jpg", "jpeg"], 
                                           accept_multiple_files=True)
            # 设置单个spine_image为None以保持向后兼容性
            spine_image = None
        else:
            # 单书脊模式 - 保持原有功能
            spine_image = st.file_uploader("上传书脊图片", type=["png", "jpg", "jpeg"])
            spine_images = []

    with col2:
        st.header("渲染结果")
        result_placeholder = st.empty()
        download_placeholder = st.empty()
    
    # 返回所有参数，包括新添加的多书脊相关参数和书型参数
    return cover_image, spine_image, spine_images, result_placeholder, download_placeholder, \
           book_distance, cover_width, perspective_angle, bg_color, bg_alpha, st.session_state.spine_spread_angle, \
           camera_height_ratio, final_size, border_percentage, st.session_state.multi_spine_mode, \
           book_type, spine_shadow_mode
