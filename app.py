"""
3D图书封面渲染器 - 主入口文件

该应用程序允许用户上传图书封面和书脊图片，通过调整各种参数生成3D立体效果的图书封面。

结构说明：
- ui.py: 处理用户界面和交互
- renderer.py: 封装所有渲染相关功能
- processor.py: 处理图像处理逻辑
- app.py: 主入口文件，协调各模块
- types.py: 定义数据类，封装参数
- big-bang/: 附属功能，PDF封面和书脊提取
"""

import streamlit as st
import sys
import os

# 添加big-bang目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'big-bang'))

st.set_page_config(
    page_title="立体封渲染器",
    page_icon="📚",
    layout="wide"
)

def main_app():
    
    # 原有功能
    from ui import setup_ui
    from processor import process_images
    
    # 设置用户界面并获取UI元素
    ui_params = setup_ui()
    
    # 处理图像并渲染3D封面
    process_images(ui_params)


def big_bang_app():
    # 返回主应用的按钮
    if st.button("← 返回立体封渲染器", type="secondary"):
        st.query_params["page"] = "main"
        st.rerun()

    st.title("📄 PDF封面和书脊提取工具（测试）")
    
    # 导入必要的模块
    import os
    import tempfile
    import zipfile
    from pdf_to_images import cut_pdf, pdf_to_image
    from cover_spine_generator import find_symmetry_positions
    from PIL import Image
    
    # 上传PDF文件
    uploaded_file = st.file_uploader("仅接受带出血线的PDF文件，不带血线则无法正确识别", type="pdf")
    
    if uploaded_file is not None:
        try:
            # 创建临时目录用于处理文件
            temp_dir = tempfile.mkdtemp()
            
            # 保存上传的PDF文件
            pdf_path = os.path.join(temp_dir, uploaded_file.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 将PDF转换为图片以获取预览图
            img_path = pdf_to_image(pdf_path, temp_dir)
            
            # 调用find_symmetry_positions获取可视化图片
            symmetry_positions, visualize_path, _ = find_symmetry_positions(img_path, temp_dir, directions=["horizontal", "vertical"])
            
            # 调用cut_pdf生成封面和书脊
            cover_path, spine_path = cut_pdf(pdf_path, temp_dir)
            
            if cover_path and spine_path:
                # 显示识别出界限的图片
                st.subheader("界限预览")
                st.image(visualize_path, width='stretch')
                
                col3, col4 = st.columns(2)
                
                # 处理书脊
                with col3:
                    st.subheader("提取书脊")
                    spine_img = Image.open(spine_path)
                    new_spine_width = int(spine_img.size[0] * (400 / spine_img.size[1]))
                    st.image(spine_path, width=new_spine_width, clamp=True)
                
                # 处理封面
                with col4:
                    st.subheader("提取封面")
                    cover_img = Image.open(cover_path)
                    new_cover_width = int(cover_img.size[0] * (400 / cover_img.size[1]))
                    st.image(cover_path, width=new_cover_width, clamp=True)
                
                # 创建临时zip文件
                zip_buffer = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                zip_path = zip_buffer.name
                zip_buffer.close()
                
                # 打包封面和书脊
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    zf.write(cover_path, os.path.basename(cover_path))
                    zf.write(spine_path, os.path.basename(spine_path))
                
                # 读取zip文件内容
                with open(zip_path, "rb") as f:
                    zip_data = f.read()
                
                # 提供下载按钮
                st.download_button(
                    label="打包下载",
                    data=zip_data,
                    file_name="cover_and_spine.zip",
                    mime="application/zip"
                )
                
                # 清理临时zip文件
                os.unlink(zip_path)
            else:
                st.error("处理失败，请检查PDF文件是否符合要求")
        except Exception as e:
            st.error(f"处理过程中发生错误: {str(e)}")
        finally:
            # 手动清理临时目录，避免出现NotADirectoryError
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                # 先删除目录中的所有文件
                for root, dirs, files in os.walk(temp_dir, topdown=False):
                    for name in files:
                        try:
                            os.remove(os.path.join(root, name))
                        except:
                            pass
                    for name in dirs:
                        try:
                            os.rmdir(os.path.join(root, name))
                        except:
                            pass
                # 最后删除目录本身
                try:
                    os.rmdir(temp_dir)
                except:
                    pass


def main():
    """根据查询参数决定显示哪个应用"""
    # 获取当前页面参数
    page = st.query_params.get("page", "main")
    
    if page == "big-bang":
        big_bang_app()
    else:
        main_app()


if __name__ == "__main__":
    main()
