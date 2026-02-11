import streamlit as st
import json
import os
import zipfile
from io import BytesIO
from PIL import Image
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
    if 'imported_config' not in st.session_state:
        st.session_state.imported_config = None
    if 'config_processed' not in st.session_state:
        st.session_state.config_processed = False
    
    # 设置页面配置
    st.set_page_config(
        page_title="立体封渲染器",
        page_icon="📚",
        layout="wide"
    )

    # 页面标题和说明
    st.title("立体封渲染器")
    st.write("上传图书封面和书脊图片，调整参数生成专业的立体图书效果")

    # 获取导入的配置
    imported_config = st.session_state.imported_config
    
    # 获取配置值的辅助函数
    def get_config_value(key, default):
        if imported_config and key in imported_config:
            return imported_config[key]
        return default

    # 侧边栏 - 参数调整
    with st.sidebar:
        
        st.header("参数设置")
        
        # 书型选择
        book_type = st.radio(
            "选择书型",
            options=["平装", "精装"],
            index=["平装", "精装"].index(get_config_value("book_type", "平装")),
        )

        cover_width = st.slider("开本宽度（mm）", 120, 200, get_config_value("cover_width", 187), 
                                help="成品图基于真实空间尺寸计算，开本宽度不同会导致透视关系不同，请选择该书真实的开本宽度") 
    
        # 书脊阴影模式选择
        spine_shadow_mode = st.radio(
            "书脊阴影模式",
            options=["无", "线性", "反射"],
            index=["无", "线性", "反射"].index(get_config_value("spine_shadow_mode", "线性"))
        )
        
        perspective_angle = st.slider("旋转角度（°）", 1, 89, get_config_value("perspective_angle", 35))
        
        # 计算最大允许的书脊额外展开角度
        max_spine_spread_angle = 90 - perspective_angle
        
        # 获取当前的spine_spread_angle值（优先使用导入的配置）
        current_spine_spread_angle = get_config_value("spine_spread_angle", st.session_state.spine_spread_angle)
        
        # 如果当前值超过新的上限，则截断
        if current_spine_spread_angle > max_spine_spread_angle:
            current_spine_spread_angle = max_spine_spread_angle
            # 更新session_state以保存截断后的值
            st.session_state.spine_spread_angle = current_spine_spread_angle
        
        # 使用key参数绑定组件与session_state
        spine_spread_angle = st.slider(
            "书脊额外展开角度（°）", 
            0, 
            max_spine_spread_angle, 
            current_spine_spread_angle, 
            help="如果书脊太窄，可以额外展开，最大可以展至完全面向正面.推荐为0。该滑条允许值会自动计算。注意：额外展开书脊会使得书脊的角度不符合真实透视关系",
            key="spine_spread_angle"
        )
        
        # 书脊加宽比例
        spine_width_ratio = st.slider(
            "书脊拉伸", 
            1.0, 
            2.0, 
            get_config_value("spine_width_ratio", 1.0), 
            step=0.05,
            help="如果书脊的视觉展示效果过薄，可在此按比例拉宽书脊，默认为1（即不拉伸）。注意：拉伸会使得书脊的宽度不符合真实透视关系"
        )
        
        # 封面描边选项（不折叠）
        stroke_enabled = st.checkbox("封面描边", value=get_config_value("stroke_enabled", False), help="为封面和书脊添加细灰色边框，突出显示图书轮廓")
        
        # 使用expander实现折叠设置
        with st.expander("高级设置", expanded=False):
            # 透视参数
            st.subheader("透视参数")
            book_distance = st.slider("相机与书距离（mm）", 300, 1000, get_config_value("book_distance", 800))
            camera_height_ratio = st.slider("相机相对高度比例", 0.0, 1.0, get_config_value("camera_height_ratio", 0.5), help="控制3D视角的垂直位置，0表示底部，1表示顶部")
            
            # 输出图像参数
            st.subheader("输出图像参数")
            final_size = st.slider("最终图像尺寸（像素）", 800, 2000, get_config_value("final_size", 1200), step=100)
            border_percentage = st.slider("边框占比", 0.0, 0.2, get_config_value("border_percentage", 0.05), step=0.01)
            
            # 渲染参数
            st.subheader("渲染参数")
            bg_color = st.color_picker("背景颜色", get_config_value("bg_color", "#ffffff"))
            bg_alpha = st.slider("背景不透明度", 0, 100, get_config_value("bg_alpha", 100))
            
            # 收集所有设置参数
            settings = {
                "book_type": book_type,
                "cover_width": cover_width,
                "spine_shadow_mode": spine_shadow_mode,
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
        
        # 配置管理 - 放在高级设置下方，使用折叠栏
        with st.expander("配置管理", expanded=False):
            # 导出设置为JSON
            # 将设置转换为JSON
            json_data = json.dumps(settings, indent=2, ensure_ascii=False)
            # 将JSON字符串转换为BytesIO对象
            json_bytes = BytesIO(json_data.encode('utf-8'))

            st.write("你可以随时将现有配置导出为文件下载，也可以导入已有的配置文件。")
            
            st.download_button(
                label="导出当前配置",
                data=json_bytes,
                file_name="3d_cover_settings.json",
                mime="application/json"
            )

            # 导入JSON配置
            uploaded_config = st.file_uploader(
                "导入配置文件（JSON）",
                type=["json"]
            )

            # 如果有导入的配置且未处理过，应用到UI
            if uploaded_config is not None and not st.session_state.config_processed:
                try:
                    # 读取并解析JSON配置
                    config_data = json.load(uploaded_config)
                    
                    # 保存导入的配置到session_state
                    st.session_state.imported_config = config_data
                    
                    # 设置处理标志为True，避免重新运行后再次处理
                    st.session_state.config_processed = True
                    
                    # spine_spread_angle将在重新运行时通过get_config_value获取
                    
                    # 重新运行应用以应用新配置
                    st.rerun()
                except Exception as e:
                    st.error(f"配置导入失败: {str(e)}")
            # 如果没有上传新文件，重置处理标志
            elif uploaded_config is None:
                st.session_state.config_processed = False

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

        # 使用查询参数切换到big-bang功能
        if st.button("从印刷文件提取封面和书脊　→", type="secondary", help="使用带血线的PDF印刷文件，提取封面和书脊图片"):
            st.query_params["page"] = "big-bang"
            st.rerun()
        
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
        
        # 快速演示功能 - 使用折叠栏
        with st.expander("功能演示", expanded=False):
            if st.session_state.example_mode:
                if st.button("关闭示例图片以继续"):
                    st.session_state.example_mode = False
                    st.rerun()
                
                # 下载示例图片按钮
                
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
        spine_width_ratio=spine_width_ratio,
        stroke_enabled=stroke_enabled
    )
