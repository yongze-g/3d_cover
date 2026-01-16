#!/usr/bin/env python3
"""
3D图书封面渲染器 - 命令行接口

允许用户直接通过命令行生成3D封面，无需启动Web界面。
"""

import argparse
import os
import json
from PIL import Image
from renderer import BookCoverRenderer

def main():
    """主函数，处理命令行参数并执行渲染"""
    parser = argparse.ArgumentParser(description='3D图书封面渲染器 - 命令行接口')
    
    # 必需参数
    parser.add_argument('--cover', '-c', required=True, help='封面图片路径')
    parser.add_argument('--spine', '-s', required=True, nargs='+', help='书脊图片路径（可以指定多个）')
    parser.add_argument('--output', '-o', required=True, help='输出图片路径')
    
    # 可选参数
    parser.add_argument('--perspective', '-p', type=int, default=35, help='旋转角度（度），默认：35')
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
    parser.add_argument('--stroke-enabled', '-se', action='store_true', help='是否为封面描边，默认：False')
    parser.add_argument('--config', '-C', help='配置文件路径（JSON格式），配置文件中的参数会被命令行参数覆盖')
    
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
                'stroke_enabled': 'stroke_enabled'
            }
            
            # 应用配置文件中的参数（如果命令行没有提供的话）
            for cli_param, config_key in param_mapping.items():
                if config_key in config_data and getattr(args, cli_param) is None or getattr(args, cli_param) == parser.get_default(cli_param):
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
    if not 0 <= args.bg_alpha <= 100:
        parser.error('--bg-alpha 必须在 0-100 之间')
    
    if not 0 <= args.camera_height <= 1:
        parser.error('--camera-height 必须在 0-1 之间')
    
    if not 0 <= args.border <= 0.2:
        parser.error('--border 必须在 0-0.2 之间')
    
    # 检查输入文件是否存在
    if not os.path.exists(args.cover):
        parser.error(f'封面图片不存在: {args.cover}')
    
    for spine_path in args.spine:
        if not os.path.exists(spine_path):
            parser.error(f'书脊图片不存在: {spine_path}')
    
    try:
        # 读取图片
        cover_img = Image.open(args.cover).convert('RGB')
        spine_imgs = [Image.open(path).convert('RGB') for path in args.spine]
        
        # 初始化渲染器
        renderer = BookCoverRenderer()
        
        # 计算背景透明度（转换为0-255范围）
        bg_alpha = int(args.bg_alpha * 255 / 100)
        
        # 执行渲染
        print("正在渲染3D封面...")
        result_image = renderer.render_3d_cover(
            cover_img=cover_img,
            spine_images=spine_imgs,
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
        print(f"渲染完成！结果已保存到: {args.output}")
        
    except Exception as e:
        print(f"渲染失败: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()