#!/usr/bin/env python3

"""
最小化的PDF转图片工具
输入PDF文件，输出两个图片：cover和spine
所有输出保存到单独的目录中
"""

import sys
import os
import fitz  # PyMuPDF
from PIL import Image

def pdf_to_two_images(pdf_path, output_dir="output"):
    """
    将PDF文件转换为两个图片：cover和spine
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
    """
    print(f"正在处理PDF文件: {pdf_path}")
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    
    # 获取总页数
    total_pages = len(doc)
    print(f"PDF总页数: {total_pages}")
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 转换第一页为cover图片
    if total_pages >= 1:
        page = doc[0]
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        cover_path = os.path.join(output_dir, "cover.jpg")
        img.save(cover_path, format="JPEG", quality=95)
        print(f"已生成cover图片: {cover_path}")
    
    # 转换第二页为spine图片，如果没有第二页则使用第一页
    spine_page_idx = 1 if total_pages >= 2 else 0
    page = doc[spine_page_idx]
    pix = page.get_pixmap(dpi=300)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    spine_path = os.path.join(output_dir, "spine.jpg")
    img.save(spine_path, format="JPEG", quality=95)
    print(f"已生成spine图片: {spine_path}")
    
    # 关闭PDF文件
    doc.close()
    
    print(f"转换完成！所有输出已保存到目录: {output_dir}")
    return cover_path, spine_path

def main():
    """主函数"""
    # 默认输入PDF路径
    default_pdf_path = "/Users/yongze/Documents/GitHub/3d_cover/big-bang/frame_cv.pdf"
    
    # 解析命令行参数
    pdf_path = default_pdf_path
    output_dir = "output"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"错误：文件 {pdf_path} 不存在！")
        sys.exit(1)
    
    # 执行转换
    pdf_to_two_images(pdf_path, output_dir)

if __name__ == "__main__":
    main()
