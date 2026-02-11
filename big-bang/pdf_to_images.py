#!/usr/bin/env python3

"""
PDF转图片工具（使用对称检测分割）
输入PDF文件，输出两个图片：cover和spine
所有输出保存到单独的目录中
"""

import sys
import os
import fitz  # PyMuPDF
from PIL import Image

# 导入常量
from constants import CENTER_SKIP_WIDTH

def pdf_to_image(pdf_path, output_dir="."):
    """
    将PDF转换为图片
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
    
    Returns:
        图片路径
    """
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    
    # 获取第一页
    page = doc[0]
    
    # 按原尺寸转换为图片，使用2倍缩放以获得更清晰的图像
    scale = 2
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # 提取PDF文件名（不含扩展名）
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # 保存图片，使用PDF文件名作为前缀
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    img_path = os.path.join(output_dir, f"{pdf_name}_original.png")
    img.save(img_path, format="PNG")
    
    # 关闭PDF文件
    doc.close()
    
    return img_path

def cut_pdf(pdf_path, output_dir="output", center_skip_width=CENTER_SKIP_WIDTH, manual_split_k=0):
    """
    将PDF文件转换为两个图片：cover和spine
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
        center_skip_width: 中间跳过区域宽度（像素），默认：CENTER_SKIP_WIDTH
        manual_split_k: 手动第一次分割位置，取值范围为0到100
                      如果为0，按现有逻辑处理；如果不为0，以最中间位置m加减k作为第一组分割
    
    Returns:
        tuple: (cover_path, spine_path)
    """
    print(f"正在处理PDF文件: {pdf_path}")
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 1. 将PDF转换为图片
    img_path = pdf_to_image(pdf_path, output_dir)
    print(f"PDF已转换为图片: {img_path}")
    
    # 2. 调用cover_spine_generator中的整合函数生成封面和书脊
    from cover_spine_generator import process_image_for_cover_and_spine
    cover_path, spine_path = process_image_for_cover_and_spine(img_path, output_dir, center_skip_width, manual_split_k)
    
    print(f"转换完成！所有输出已保存到目录: {output_dir}")
    return cover_path, spine_path

def main():
    """主函数"""
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("错误：请提供PDF文件路径作为参数！")
        print("用法：python pdf_to_images.py <PDF文件路径> [输出目录]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = "output" if len(sys.argv) < 3 else sys.argv[2]
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"错误：文件 {pdf_path} 不存在！")
        sys.exit(1)
    
    # 执行转换
    cut_pdf(pdf_path, output_dir)

if __name__ == "__main__":
    main()
