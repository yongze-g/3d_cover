#!/usr/bin/env python3

import streamlit as st
import os
import tempfile
import zipfile
from pdf_to_images import cut_pdf, pdf_to_image
from cover_spine_generator import find_symmetry_positions

def main():
    st.title("📄 PDF封面和书脊提取工具")
    
    # 侧边栏参数设置
    center_skip_width = st.sidebar.slider(
        "中间跳过区域宽度（像素）",
        min_value=1,
        max_value=20,
        value=5,
        help="横向扫描时跳过图片中间区域的宽度，用于避开中间的血线干扰"
    )
    
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
            symmetry_positions, visualize_path, _ = find_symmetry_positions(
                img_path, temp_dir, 
                directions=["horizontal", "vertical"], 
                center_skip_width=center_skip_width
            )
            
            # 调用cut_pdf生成封面和书脊
            cover_path, spine_path = cut_pdf(pdf_path, temp_dir)
            
            if cover_path and spine_path:
                # 显示识别出界限的图片
                st.subheader("界限预览")
                st.image(visualize_path, width='stretch')
                
                col3, col4 = st.columns(2)
                
                # 使用PIL打开图片计算合适的显示宽度，保持宽高比，高度限制为400px
                from PIL import Image
                
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
            import shutil
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

if __name__ == "__main__":
    main()
