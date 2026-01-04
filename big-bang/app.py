import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os

st.title("Big-Bang PDF转JPG工具")

# 上传PDF文件
uploaded_file = st.file_uploader("上传PDF文件", type=["pdf"])

if uploaded_file is not None:
    # 保存上传的PDF文件
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("PDF文件上传成功！")
    
    # 打开PDF文件
    doc = fitz.open("temp.pdf")
    total_pages = len(doc)
    st.write(f"PDF总页数: {total_pages}")
    
    # 选择封面和书脊页面
    col1, col2 = st.columns(2)
    
    with col1:
        cover_page = st.number_input("选择封面页码", 1, total_pages, 1)
    
    with col2:
        spine_page = st.number_input("选择书脊页码", 1, total_pages, min(2, total_pages))
    
    # 处理按钮
    if st.button("转换为JPG"):
        st.info("正在转换...")
        
        # 转换封面
        cover_pix = doc[cover_page-1].get_pixmap(dpi=300)
        cover_img = Image.frombytes("RGB", [cover_pix.width, cover_pix.height], cover_pix.samples)
        
        # 转换书脊
        spine_pix = doc[spine_page-1].get_pixmap(dpi=300)
        spine_img = Image.frombytes("RGB", [spine_pix.width, spine_pix.height], spine_pix.samples)
        
        # 显示转换结果
        st.subheader("转换结果预览")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(cover_img, caption=f"封面 (页码: {cover_page})")
        
        with col2:
            st.image(spine_img, caption=f"书脊 (页码: {spine_page})")
        
        st.success("转换完成！")
        
        # 提供下载选项
        st.subheader("下载图片")
        
        # 下载封面
        cover_buffer = io.BytesIO()
        cover_img.save(cover_buffer, format="JPEG")
        cover_buffer.seek(0)
        
        st.download_button(
            label="下载封面 (JPG)",
            data=cover_buffer,
            file_name="cover.jpg",
            mime="image/jpeg"
        )
        
        # 下载书脊
        spine_buffer = io.BytesIO()
        spine_img.save(spine_buffer, format="JPEG")
        spine_buffer.seek(0)
        
        st.download_button(
            label="下载书脊 (JPG)",
            data=spine_buffer,
            file_name="spine.jpg",
            mime="image/jpeg"
        )
    
    # 关闭PDF文件
    doc.close()
    
    # 删除临时文件
    if os.path.exists("temp.pdf"):
        os.remove("temp.pdf")
