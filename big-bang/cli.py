#!/usr/bin/env python3
"""
PDF封面和书脊提取工具 - 命令行接口

允许用户直接通过命令行从PDF文件中提取封面和书脊图片，无需启动Web界面。
"""

import argparse
import os
import sys
import zipfile
import tempfile
from pdf_to_images import cut_pdf

# 导入常量
from constants import K_MAX, CENTER_SKIP_WIDTH

def main():
    """主函数，处理命令行参数并执行PDF处理"""
    parser = argparse.ArgumentParser(description='PDF封面和书脊提取工具 - 命令行接口')
    
    # 必需参数
    parser.add_argument('--pdf', '-p', required=True, help='PDF文件路径')
    parser.add_argument('--output', '-o', default='output', help='输出目录，默认：output')
    
    # PDF处理参数
    parser.add_argument('--center-skip', '-cs', type=int, default=CENTER_SKIP_WIDTH, help=f'中间跳过区域宽度（像素），默认：{CENTER_SKIP_WIDTH}')
    parser.add_argument('--manual-split', '-ms', type=int, default=0, help=f'手动第一次分割位置k，取值范围为0到{K_MAX}，默认：0')
    parser.add_argument('--zip', '-z', action='store_true', help='将结果打包为zip文件')
    parser.add_argument('--zip-name', '-zn', help='zip文件名（如果未指定，将使用PDF文件名）')
    
    args = parser.parse_args()
    
    # 验证参数
    if not os.path.exists(args.pdf):
        parser.error(f'PDF文件不存在: {args.pdf}')
    
    if args.center_skip < 0:
        parser.error('--center-skip 必须大于等于0')
    
    try:
        # 确保输出目录存在
        if not os.path.exists(args.output):
            os.makedirs(args.output)
        
        # 处理PDF文件
        print(f"正在处理PDF文件: {args.pdf}")
        print(f"输出目录: {args.output}")
        print(f"中间跳过区域宽度: {args.center_skip}")
        print(f"手动分割位置k: {args.manual_split}")
        
        # 调用PDF处理函数
        cover_path, spine_path = cut_pdf(args.pdf, args.output, args.center_skip, args.manual_split)
        
        if not cover_path or not spine_path:
            print("错误：无法从PDF中提取封面和书脊")
            sys.exit(1)
        
        print(f"\n处理完成！")
        print(f"封面图片: {cover_path}")
        print(f"书脊图片: {spine_path}")
        
        # 如果需要打包为zip文件
        if args.zip:
            # 生成zip文件名
            if args.zip_name:
                zip_filename = args.zip_name
                if not zip_filename.endswith('.zip'):
                    zip_filename += '.zip'
            else:
                pdf_name = os.path.splitext(os.path.basename(args.pdf))[0]
                zip_filename = f"{pdf_name}_cover_spine.zip"
            
            zip_path = os.path.join(args.output, zip_filename)
            
            # 创建zip文件
            print(f"\n正在创建zip文件: {zip_path}")
            with zipfile.ZipFile(zip_path, 'w') as zf:
                # 添加封面和书脊图片
                zf.write(cover_path, os.path.basename(cover_path))
                zf.write(spine_path, os.path.basename(spine_path))
            
            print(f"Zip文件创建成功: {zip_path}")
            print("\n所有输出已准备就绪！")
        
    except Exception as e:
        print(f"处理失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
