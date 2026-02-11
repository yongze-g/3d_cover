#!/usr/bin/env python3

import streamlit as st
import os
import tempfile
import zipfile
import shutil
import atexit
from PIL import Image
from pdf_to_images import cut_pdf, pdf_to_image
from cover_spine_generator import find_symmetry_positions

# 导入常量
from constants import K_MAX, CENTER_SKIP_WIDTH, CENTER_SKIP_MAX

def run_big_bang_app():
    st.title("PDF封面和书脊提取工具（测试）")
    
    # 初始化会话状态
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
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    
    # 上传PDF文件
    uploaded_file = st.file_uploader("仅接受带出血线的PDF文件，不带血线则无法正确识别", type="pdf")
    
    # 处理文件上传
    if uploaded_file != st.session_state.uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.processing = True
        
        # 清理旧的临时目录
        if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
            try:
                shutil.rmtree(st.session_state.temp_dir)
            except:
                pass
        
        if uploaded_file:
            # 创建新的临时目录
            st.session_state.temp_dir = tempfile.mkdtemp()
            
            # 保存上传的PDF文件
            st.session_state.pdf_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
            with open(st.session_state.pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 将PDF转换为图片以获取预览图
            st.session_state.img_path = pdf_to_image(st.session_state.pdf_path, st.session_state.temp_dir)
            
            # 获取图片宽度
            img = Image.open(st.session_state.img_path)
            st.session_state.img_width = img.size[0]
        else:
            # 重置状态
            st.session_state.temp_dir = None
            st.session_state.pdf_path = None
            st.session_state.img_path = None
            st.session_state.img_width = 0
    
    st.write("血线识别算法持续优化中，若出现识别错误，可以在WPS中临时删除错误识别的血线，或用纯白色色块临时遮盖。")
    
    # 侧边栏参数设置
    with st.sidebar:
        st.header("分割参数设置")
        
        center_skip_width = st.slider(
            "中间跳过区域宽度（像素）",
            min_value=0,
            max_value=CENTER_SKIP_MAX,
            value=CENTER_SKIP_WIDTH,
            help="横向扫描时跳过图片中间区域的宽度，用于避开中间的血线干扰，为0时不跳过中间区域"
        )
        
        # 添加手动分割位置设置
        manual_split_k = st.slider(
            "手动第一次分割位置k",
            min_value=0,
            max_value=K_MAX,
            value=0,
            help=f"取值范围为0到{K_MAX}，如果为0则按默认逻辑处理，否则以中间位置m加减k作为第一组分割"
        )
    
    # 处理PDF文件
    if st.session_state.pdf_path and st.session_state.img_path:
        try:
            # 显示处理状态
            with st.spinner("正在处理PDF文件..."):
                # 调用find_symmetry_positions获取可视化图片
                symmetry_positions, visualize_path, _ = find_symmetry_positions(
                    st.session_state.img_path, st.session_state.temp_dir, 
                    directions=["horizontal", "vertical"], 
                    center_skip_width=center_skip_width,
                    manual_split_k=manual_split_k
                )
                
                # 调用cut_pdf生成封面和书脊，传递手动分割参数
                cover_path, spine_path = cut_pdf(
                    st.session_state.pdf_path, 
                    st.session_state.temp_dir, 
                    center_skip_width, 
                    manual_split_k
                )
                
                if cover_path and spine_path:
                    # 显示识别出界限的图片
                    st.subheader("界限预览")
                    st.image(visualize_path, width='stretch')
                    
                    col3, col4 = st.columns(2)
                    
                    # 使用PIL打开图片计算合适的显示宽度，保持宽高比，高度限制为400px
                    
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
                    
                    # 生成包含上传PDF文件名的下载文件名
                    base_file_name = "cover_and_spine"
                    try:
                        # 获取上传的PDF文件名（不带扩展名）
                        if st.session_state.uploaded_file:
                            pdf_file_name = st.session_state.uploaded_file.name
                            # 移除扩展名
                            pdf_name_without_ext = pdf_file_name.rsplit('.', 1)[0]
                            # 添加到下载文件名中
                            base_file_name += f"_{pdf_name_without_ext}"
                    except Exception:
                        # 如果获取文件名失败，使用默认名称
                        pass
                    
                    # 提供下载按钮
                    st.download_button(
                        label="打包下载",
                        data=zip_data,
                        file_name=f"{base_file_name}.zip",
                        mime="application/zip",
                        type="primary"
                    )
                    
                    # 清理临时zip文件
                    os.unlink(zip_path)
                else:
                    st.error("处理失败，请检查PDF文件是否符合要求")
        except Exception as e:
            st.error(f"处理过程中发生错误: {str(e)}")
    
    # 清理临时目录（在会话结束时）
    def cleanup_temp_dir():
        if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
            try:
                shutil.rmtree(st.session_state.temp_dir)
            except:
                pass
    
    # 注册清理函数
    if 'cleanup_registered' not in st.session_state:
        atexit.register(cleanup_temp_dir)
        st.session_state.cleanup_registered = True

def main():
    run_big_bang_app()

if __name__ == "__main__":
    main()
