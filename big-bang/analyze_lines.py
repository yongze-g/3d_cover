import fitz  # PyMuPDF
import cv2
import numpy as np
import os

def analyze_lines(pdf_path):
    """
    分析PDF中的所有线条对象，找出最外围的20个
    """
    print(f"=== 线条对象详细分析 ===")
    print(f"文件: {pdf_path}")
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    page = doc[0]  # 第一页
    
    # 获取页面尺寸
    page_width = int(page.rect.width)
    page_height = int(page.rect.height)
    print(f"页面尺寸: {page_width} x {page_height} points")
    
    # 获取所有绘图对象
    drawings = page.get_drawings()
    
    # 存储所有线条
    lines = []
    
    # 遍历所有绘图对象
    for drawing in drawings:
        items = drawing.get("items", [])
        
        # 收集这个绘图中的所有线条点
        line_points = []
        for item in items:
            if item[0] == "l":  # 线条点
                point = item[1]  # 这是一个Point对象
                line_points.append(point)
        
        # 如果没有线条点，跳过这个绘图
        if not line_points or len(line_points) < 2:
            continue
            
        # 获取线条样式信息
        color = drawing.get("color", None)
        width = drawing.get("width", 1)
        
        # 将连续的点组合成线段
        for i in range(len(line_points) - 1):
            start_point = line_points[i]
            end_point = line_points[i + 1]
            
            # 提取坐标
            x0, y0 = start_point.x, start_point.y
            x1, y1 = end_point.x, end_point.y
            
            # 计算长度
            line_length = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            
            # 判断方向
            is_horizontal = abs(y1 - y0) < 1
            is_vertical = abs(x1 - x0) < 1
            
            # 计算边界
            min_x = min(x0, x1)
            max_x = max(x0, x1)
            min_y = min(y0, y1)
            max_y = max(y0, y1)
            
            # 添加到线条列表
            lines.append({
                'start': (x0, y0),
                'end': (x1, y1),
                'x0': x0,
                'y0': y0,
                'x1': x1,
                'y1': y1,
                'min_x': min_x,
                'max_x': max_x,
                'min_y': min_y,
                'max_y': max_y,
                'length': line_length,
                'is_horizontal': is_horizontal,
                'is_vertical': is_vertical,
                'color': color,
                'stroke_width': width
            })
    
    print(f"\n总共发现 {len(lines)} 个线条段")
    
    # 找出最外围的线条
    outer_lines = []
    
    if lines:
        # 找最左边的线条
        left_most_line = min(lines, key=lambda l: l['min_x'])
        outer_lines.append(left_most_line)
        
        # 找最右边的线条
        right_most_line = max(lines, key=lambda l: l['max_x'])
        if right_most_line not in outer_lines:
            outer_lines.append(right_most_line)
        
        # 找最上边的线条
        top_most_line = min(lines, key=lambda l: l['min_y'])
        if top_most_line not in outer_lines:
            outer_lines.append(top_most_line)
        
        # 找最下边的线条
        bottom_most_line = max(lines, key=lambda l: l['max_y'])
        if bottom_most_line not in outer_lines:
            outer_lines.append(bottom_most_line)
        
        # 按长度排序，找出较长的线条
        lines_by_length = sorted(lines, key=lambda l: l['length'], reverse=True)
        
        # 添加按长度排序的线条，但去重
        for line in lines_by_length:
            if len(outer_lines) >= 20:
                break
            if line not in outer_lines:
                outer_lines.append(line)
        
        # 如果不够20个，补充其他线条
        if len(outer_lines) < 20:
            for line in lines:
                if len(outer_lines) >= 20:
                    break
                if line not in outer_lines:
                    outer_lines.append(line)
    
    # 输出前20个外围线条的详细信息
    print(f"\n=== 最外围的20个线条对象详细信息 ===")
    
    for i, line in enumerate(outer_lines[:20]):
        print(f"\n线条 {i+1}:")
        print(f"  起点: ({line['x0']:.1f}, {line['y0']:.1f})")
        print(f"  终点: ({line['x1']:.1f}, {line['y1']:.1f})")
        print(f"  长度: {line['length']:.1f}")
        print(f"  方向: {'水平线' if line['is_horizontal'] else '垂直线' if line['is_vertical'] else '斜线'}")
        print(f"  边框颜色: {line['color']}")
        print(f"  边框宽度: {line['stroke_width']}")
    
    # 生成可视化图像
    create_line_visualization(page, outer_lines[:20], page_width, page_height)
    
    doc.close()
    return outer_lines[:20]

def create_line_visualization(page, lines, page_width, page_height):
    """
    创建线条可视化图像
    """
    print(f"\n正在生成可视化图像...")
    
    # 将页面转换为高分辨率图像
    pix = page.get_pixmap(dpi=200)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    
    if pix.n == 3:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    elif pix.n == 4:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img_rgb = img
    
    # 计算PDF坐标到图像像素的缩放比例
    scale_x = pix.width / page_width
    scale_y = pix.height / page_height
    
    print(f"原始PDF尺寸: {page_width} x {page_height} points")
    print(f"图像尺寸: {pix.width} x {pix.height} pixels")
    print(f"缩放比例: x={scale_x:.4f}, y={scale_y:.4f}")
    
    # 创建一个副本用于绘制线条
    overlay = img_rgb.copy()
    
    # 定义颜色映射
    colors = [
        (255, 0, 0),    # 红色
        (0, 255, 0),    # 绿色
        (0, 0, 255),    # 蓝色
        (255, 255, 0),  # 黄色
        (255, 0, 255),  # 紫色
        (0, 255, 255),  # 青色
        (128, 0, 128),  # 深紫色
        (255, 165, 0),  # 橙色
        (0, 128, 128),  # 深青色
        (128, 128, 0),  # 深黄色
        (0, 0, 128),    # 深蓝色
        (128, 0, 0),    # 深红色
        (0, 128, 0),    # 深绿色
        (255, 192, 203),# 粉色
        (255, 215, 0),  # 金色
        (70, 130, 180), # 钢蓝色
        (34, 139, 34),  # 森林绿
        (220, 20, 60),  # 深粉色
        (255, 140, 0),  # 深橙色
        (138, 43, 226)  # 蓝紫色
    ]
    
    # 绘制线条
    for i, line in enumerate(lines):
        color = colors[i % len(colors)]
        
        # 使用缩放比例正确转换坐标
        x0 = int(line['x0'] * scale_x)
        y0 = int(line['y0'] * scale_y)
        x1 = int(line['x1'] * scale_x)
        y1 = int(line['y1'] * scale_y)
        
        # 绘制线条
        stroke_width = line['stroke_width'] if line['stroke_width'] is not None else 1
        thickness = max(2, int(stroke_width * 2))
        cv2.line(overlay, (x0, y0), (x1, y1), color, thickness)
        
        # 添加标签
        label = f"{i+1}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        font_thickness = 2
        text_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
        
        # 调整文本位置避免超出边界
        text_x = max(5, min(x0, img_rgb.shape[1] - text_size[0] - 5))
        text_y = max(text_size[1] + 5, min(y0 + text_size[1] + 5, img_rgb.shape[0] - 5))
        
        # 绘制文本背景
        cv2.rectangle(overlay, (text_x - 2, text_y - text_size[1] - 2), 
                     (text_x + text_size[0] + 2, text_y + 2), color, -1)
        
        # 绘制文本
        cv2.putText(overlay, label, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness)
    
    # 保存结果
    output_dir = "analysis_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    cv2.imwrite(os.path.join(output_dir, "lines_visualization.png"), overlay)
    print(f"可视化图像已保存到: {output_dir}/lines_visualization.png")
    
    # 创建详细报告
    create_line_report(lines, output_dir)

def create_line_report(lines, output_dir):
    """
    创建线条分析报告
    """
    report_path = os.path.join(output_dir, "lines_report.txt")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== PDF线条对象分析报告 ===\n\n")
        
        for i, line in enumerate(lines):
            f.write(f"线条 {i+1}:\n")
            f.write(f"  起点: ({line['x0']:.1f}, {line['y0']:.1f})\n")
            f.write(f"  终点: ({line['x1']:.1f}, {line['y1']:.1f})\n")
            f.write(f"  长度: {line['length']:.1f}\n")
            f.write(f"  方向: {'水平线' if line['is_horizontal'] else '垂直线' if line['is_vertical'] else '斜线'}\n")
            f.write(f"  边框颜色: {line['color']}\n")
            f.write(f"  边框宽度: {line['stroke_width']}\n")
            f.write("\n")
    
    print(f"详细报告已保存到: {report_path}")

if __name__ == "__main__":
    analyze_lines("FM68140-0101.pdf")