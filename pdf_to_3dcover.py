#!/usr/bin/env python3
"""
PDF到3D封面一步生成工具

直接从PDF文件提取封面和书脊，然后生成立体封，无需中间步骤。
"""

import argparse
import os
import sys
import tempfile
import json

# 添加big-bang目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'big-bang'))

from pdf_to_images import cut_pdf
from renderer import BookCoverRenderer
from PIL import Image

# 导入常量
from constants import K_MAX, CENTER_SKIP_WIDTH

def main():
    """主函数，处理命令行参数并执行完整流程"""
    parser = argparse.ArgumentParser(description='PDF到3D封面一步生成工具')
    
    # 必需参数
    parser.add_argument('--pdf', '-p', required=True, help='PDF文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出3D封面图片路径')
    
    # PDF处理参数
    parser.add_argument('--center-skip', '-cs', type=int, default=CENTER_SKIP_WIDTH, help=f'中间跳过区域宽度（像素），默认：{CENTER_SKIP_WIDTH}')
    parser.add_argument('--manual-split', '-ms', type=int, default=0, help=f'手动第一次分割位置k，取值范围为0到{K_MAX}，默认：0')
    parser.add_argument('--temp-dir', '-t', help='临时目录（如果未指定，将使用系统临时目录）')
    
    # 配置文件参数
    parser.add_argument('--config', '-C', help='配置文件路径（JSON格式），配置文件中的参数会被命令行参数覆盖')
    
    # 3D封面渲染参数
    parser.add_argument('--perspective', '-pt', type=int, default=35, help='旋转角度（度），默认：35')
    parser.add_argument('--distance', '-d', type=int, default=800, help='相机与书距离（mm），默认：800')
    parser.add_argument('--width', '-w', type=int, default=187, help='开本宽度（mm），默认：187')
    parser.add_argument('--bg-color', '-b', default='#ffffff', help='背景颜色（十六进制），默认：#ffffff')
    parser.add_argument('--bg-alpha', '-a', type=int, default=100, help='背景透明度（0-100），默认：100')
    parser.add_argument('--spine-spread', '-ss', type=int, default=0, help='书脊额外展开角度（度），默认：0')
    parser.add_argument('--camera-height', '-ch', type=float, default=0.5, help='相机高度比例（0-1），默认：0.5')
    parser.add_argument('--final-size', '-fs', type=int, default=1200, help='最终图像尺寸（像素），默认：1200')
    parser.add_argument('--border', '-bd', type=float, default=0.1, help='边框占比（0-0.2），默认：0.1')
    parser.add_argument('--book-type', '-bt', choices=['平装', '精装'], default='平装', help='书型，默认：平装')
    parser.add_argument('--shadow-mode', '-sm', choices=['无', '线性', '反射'], default='线性', help='书脊阴影模式，默认：线性')
    parser.add_argument('--stroke-enabled', '-se', action='store_true', help='是否为封面描边')
    
    args = parser.parse_args()
    
    # 如果提供了配置文件，读取并应用配置
    if args.config:
        if not os.path.exists(args.config):
            parser.error(f'配置文件不存在: {args.config}')
        
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 命令行参数映射到配置文件键名
            param_mapping = {
                'perspective': 'perspective_angle',
                'distance': 'book_distance',
                'width': 'cover_width',
                'bg_color': 'bg_color',
                'bg_alpha': 'bg_alpha',
                'spine_spread': 'spine_spread_angle',
                'camera_height': 'camera_height_ratio',
                'final_size': 'final_size',
                'border': 'border_percentage',
                'book_type': 'book_type',
                'shadow_mode': 'spine_shadow_mode',
                'stroke_enabled': 'stroke_enabled',
                'center_skip': 'center_skip_width'
            }
            
            # 应用配置文件中的参数（如果命令行没有提供的话）
            for cli_param, config_key in param_mapping.items():
                if config_key in config_data and getattr(args, cli_param) == parser.get_default(cli_param):
                    # 对于布尔值参数，需要特殊处理
                    if cli_param == 'stroke_enabled':
                        setattr(args, cli_param, config_data[config_key])
                    else:
                        setattr(args, cli_param, config_data[config_key])
                        
        except json.JSONDecodeError as e:
            parser.error(f'配置文件解析错误: {str(e)}')
        except Exception as e:
            parser.error(f'配置文件处理错误: {str(e)}')
    
    # 验证参数
    if not os.path.exists(args.pdf):
        parser.error(f'PDF文件不存在: {args.pdf}')
    
    if args.center_skip < 0:
        parser.error('--center-skip 必须大于等于0')
    
    # 验证3D渲染参数
    if not 0 <= args.bg_alpha <= 100:
        parser.error('--bg-alpha 必须在 0-100 之间')
    
    if not 0 <= args.camera_height <= 1:
        parser.error('--camera-height 必须在 0-1 之间')
    
    if not 0 <= args.border <= 0.2:
        parser.error('--border 必须在 0-0.2 之间')
    
    try:
        # 创建临时目录
        if args.temp_dir:
            temp_dir = args.temp_dir
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
        else:
            temp_dir = tempfile.mkdtemp()
        
        print(f"临时目录: {temp_dir}")
        print(f"正在处理PDF文件: {args.pdf}")
        
        # 1. 从PDF提取封面和书脊
        print("\n步骤1: 从PDF提取封面和书脊...")
        print(f"手动分割位置k: {args.manual_split}")
        cover_path, spine_path = cut_pdf(args.pdf, temp_dir, args.center_skip, args.manual_split)
        
        if not cover_path or not spine_path:
            print("错误：无法从PDF中提取封面和书脊")
            sys.exit(1)
        
        print(f"封面提取成功: {cover_path}")
        print(f"书脊提取成功: {spine_path}")
        
        # 2. 生成立体封
        print("\n步骤2: 生成3D封面...")
        
        # 读取提取的图片
        cover_img = Image.open(cover_path).convert('RGB')
        spine_img = Image.open(spine_path).convert('RGB')
        
        # 初始化渲染器
        renderer = BookCoverRenderer()
        
        # 计算背景透明度（转换为0-255范围）
        bg_alpha = int(args.bg_alpha * 255 / 100)
        
        # 执行渲染
        result_image = renderer.render_3d_cover(
            cover_img=cover_img,
            spine_images=[spine_img],  # 传递单个数脊图片列表
            perspective_angle=args.perspective,
            book_distance=args.distance,
            cover_width=args.width,
            bg_color=args.bg_color,
            bg_alpha=bg_alpha,
            spine_spread_angle=args.spine_spread,
            camera_height_ratio=args.camera_height,
            final_size=args.final_size,
            border_percentage=args.border,
            book_type=args.book_type,
            spine_shadow_mode=args.shadow_mode,
            stroke_enabled=args.stroke_enabled
        )
        
        # 保存结果
        result_pil = Image.fromarray(result_image)
        result_pil.save(args.output)
        
        print(f"\n处理完成！")
        print(f"3D封面已保存到: {args.output}")
        print(f"临时文件保存在: {temp_dir}")
        
        # 如果使用系统临时目录，提示用户可以删除
        if not args.temp_dir:
            print("\n注意：临时目录会在系统重启时自动清理，或您可以手动删除它。")
        
    except Exception as e:
        print(f"处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
