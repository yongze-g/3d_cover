import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image, ImageDraw
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
    
    # 提取所有线条信息
    lines = []
    line_count = 0
    
    for drawing in drawings:
        items = drawing.get("items", [])
        # 尝试从绘图中提取线条信息
        # 注意：在PyMuPDF中，线条(类型为"l")通常由一系列点组成
        # 而不是单一的两点定义
        # 我们将所有连续的"l"类型的点组合成线条
        
        line_points = []  # 存储所有线条的点
        
        # 首先收集所有线条类型的点
        for item in items:
            if item[0] == "l":  # 线条点
                point = item[1]  # 这是一个Point对象
                line_points.append(point)
        
        # 如果没有线条点，跳过这个绘图
        if not line_points:
            continue
            
        # 处理连续的线条点，将它们组合成线条
        # 如果只有一个点，它可能是一个起点
        # 如果有多个点，它们形成一条多段线
        
        # 创建一个多段线对象
        if len(line_points) >= 2:
            # 对于连续的点，创建一个线条
            for i in range(len(line_points) - 1):
                start_point = line_points[i]
                end_point = line_points[i + 1]
                
                # 提取线条的起点和终点坐标
                x0, y0 = start_point.x, start_point.y
                x1, y1 = end_point.x, end_point.y
                
                # 计算线条长度
                line_length = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)
                
                # 判断线条方向
                is_horizontal = abs(y1 - y0) < 1  # 水平线
                is_vertical = abs(x1 - x0) < 1    # 垂直线
                
                # 找出最接近页面边缘的点
                min_x = min(x0, x1)
                max_x = max(x0, x1)
                min_y = min(y0, y1)
                max_y = max(y0, y1)
                
                # 获取线条的样式信息
                color = drawing.get("color", None)
                width = drawing.get("width", 1)
                
                lines.append({
                    'line': [start_point, end_point],
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
                
                line_count += 1
    
    print(f"\n总共发现 {len(lines)} 个线条对象")
    
    # 计算外围线条
    # 方法：基于边界，找出最接近页面边缘的线条
    outer_lines = []
    seen_coords = set()
    
    # 找最左边的线条（min_x最小）
    if lines:
        left_most_line = min(lines, key=lambda l: l['min_x'])
        left_edge_coord = (left_most_line['start'], left_most_line['end'])
        if left_edge_coord not in seen_coords:
            outer_lines.append(left_most_line)
            seen_coords.add(left_edge_coord)
        
        # 找最右边的线条（max_x最大）
        right_most_line = max(lines, key=lambda l: l['max_x'])
        right_edge_coord = (right_most_line['start'], right_most_line['end'])
        if right_edge_coord not in seen_coords:
            outer_lines.append(right_most_line)
            seen_coords.add(right_edge_coord)
        
        # 找最上边的线条（min_y最小）
        top_most_line = min(lines, key=lambda l: l['min_y'])
        top_edge_coord = (top_most_line['start'], top_most_line['end'])
        if top_edge_coord not in seen_coords:
            outer_lines.append(top_most_line)
            seen_coords.add(top_edge_coord)
        
        # 找最下边的线条（max_y最大）
        bottom_most_line = max(lines, key=lambda l: l['max_y'])
        bottom_edge_coord = (bottom_most_line['start'], bottom_most_line['end'])
        if bottom_edge_coord not in seen_coords:
            outer_lines.append(bottom_most_line)
            seen_coords.add(bottom_edge_coord)
        
        # 找最长的线条
        if lines:
            longest_line = max(lines, key=lambda l: l['length'])
            longest_coord = (longest_line['start'], longest_line['end'])
            if longest_coord not in seen_coords:
                outer_lines.append(longest_line)
                seen_coords.add(longest_coord)
        
        # 找最左端的线条（x0或x1最接近0）
        left_edge_lines = []
        for line in lines:
            # 计算线条端点到页面左边的距离
            dist_start = abs(line['x0'] - 0)
            dist_end = abs(line['x1'] - 0)
            min_dist = min(dist_start, dist_end)
            left_edge_lines.append((line, min_dist))
        
        if left_edge_lines:
            left_edge_line = min(left_edge_lines, key=lambda x: x[1])[0]
            left_edge_coord = (left_edge_line['start'], left_edge_line['end'])
            if left_edge_coord not in seen_coords:
                outer_lines.append(left_edge_line)
                seen_coords.add(left_edge_coord)
        
        # 找最右端的线条（x0或x1最接近页面宽度）
        right_edge_lines = []
        for line in lines:
            # 计算线条端点到页面右边的距离
            dist_start = abs(line['x0'] - page_width)
            dist_end = abs(line['x1'] - page_width)
            min_dist = min(dist_start, dist_end)
            right_edge_lines.append((line, min_dist))
        
        if right_edge_lines:
            right_edge_line = min(right_edge_lines, key=lambda x: x[1])[0]
            right_edge_coord = (right_edge_line['start'], right_edge_line['end'])
            if right_edge_coord not in seen_coords:
                outer_lines.append(right_edge_line)
                seen_coords.add(right_edge_coord)
        
        # 找最上端的线条（y0或y1最接近0）
        top_edge_lines = []
        for line in lines:
            # 计算线条端点到页面顶边的距离
            dist_start = abs(line['y0'] - 0)
            dist_end = abs(line['y1'] - 0)
            min_dist = min(dist_start, dist_end)
            top_edge_lines.append((line, min_dist))
        
        if top_edge_lines:
            top_edge_line = min(top_edge_lines, key=lambda x: x[1])[0]
            top_edge_coord = (top_edge_line['start'], top_edge_line['end'])
            if top_edge_coord not in seen_coords:
                outer_lines.append(top_edge_line)
                seen_coords.add(top_edge_coord)
        
        # 找最下端的线条（y0或y1最接近页面高度）
        bottom_edge_lines = []
        for line in lines:
            # 计算线条端点到页面底边的距离
            dist_start = abs(line['y0'] - page_height)
            dist_end = abs(line['y1'] - page_height)
            min_dist = min(dist_start, dist_end)
            bottom_edge_lines.append((line, min_dist))
        
        if bottom_edge_lines:
            bottom_edge_line = min(bottom_edge_lines, key=lambda x: x[1])[0]
            bottom_edge_coord = (bottom_edge_line['start'], bottom_edge_line['end'])
            if bottom_edge_coord not in seen_coords:
                outer_lines.append(bottom_edge_line)
                seen_coords.add(bottom_edge_coord)
    
    
    # 收集所有线条，按照它们到页面边缘的最小距离分类
    outer_line_candidates = []
    
    # 收集最接近每条边缘的线条
    if lines:
        # 收集最接近左边缘的线条
        left_edge_candidates = []
        for line in lines:
            dist_start = abs(line['x0'] - 0)
            dist_end = abs(line['x1'] - 0)
            min_dist = min(dist_start, dist_end)
            left_edge_candidates.append((line, min_dist))
        
        # 收集最接近右边缘的线条
        right_edge_candidates = []
        for line in lines:
            dist_start = abs(line['x0'] - page_width)
            dist_end = abs(line['x1'] - page_width)
            min_dist = min(dist_start, dist_end)
            right_edge_candidates.append((line, min_dist))
        
        # 收集最接近上边缘的线条
        top_edge_candidates = []
        for line in lines:
            dist_start = abs(line['y0'] - 0)
            dist_end = abs(line['y1'] - 0)
            min_dist = min(dist_start, dist_end)
            top_edge_candidates.append((line, min_dist))
        
        # 收集最接近下边缘的线条
        bottom_edge_candidates = []
        for line in lines:
            dist_start = abs(line['y0'] - page_height)
            dist_end = abs(line['y1'] - page_height)
            min_dist = min(dist_start, dist_end)
            bottom_edge_candidates.append((line, min_dist))
        
        # 获取每类中距离最近的线条（可能重复）
        if left_edge_candidates:
            left_edge_line = min(left_edge_candidates, key=lambda x: x[1])[0]
            outer_line_candidates.append(('左边缘', left_edge_line))
        
        if right_edge_candidates:
            right_edge_line = min(right_edge_candidates, key=lambda x: x[1])[0]
            outer_line_candidates.append(('右边缘', right_edge_line))
        
        if top_edge_candidates:
            top_edge_line = min(top_edge_candidates, key=lambda x: x[1])[0]
            outer_line_candidates.append(('上边缘', top_edge_line))
        
        if bottom_edge_candidates:
            bottom_edge_line = min(bottom_edge_candidates, key=lambda x: x[1])[0]
            outer_line_candidates.append(('下边缘', bottom_edge_line))
        
        # 找出最长的水平线和垂直线
        horizontal_lines = [line for line in lines if line['is_horizontal']]
        vertical_lines = [line for line in lines if line['is_vertical']]
        
        if horizontal_lines:
            longest_horizontal = max(horizontal_lines, key=lambda l: l['length'])
            outer_line_candidates.append(('最长水平线', longest_horizontal))
        
        if vertical_lines:
            longest_vertical = max(vertical_lines, key=lambda l: l['length'])
            outer_line_candidates.append(('最长垂直线', longest_vertical))
        
        # 找出最长的线条
        if lines:
            longest_line = max(lines, key=lambda l: l['length'])
            outer_line_candidates.append(('最长线条', longest_line))
    
    # 去重并添加到外层线条列表
    seen_coords = set()
    for category, line in outer_line_candidates:
        line_coord = (line['start'], line['end'])
        if line_coord not in seen_coords:
            outer_lines.append(line)
            seen_coords.add(line_coord)
    
    # 如果还不够20个，按照长度排序，补充其他线条
    lines_by_length = sorted(lines, key=lambda l: l['length'], reverse=True)
    
    for line in lines_by_length:
        if len(outer_lines) >= 20:
            break
        line_coord = (line['start'], line['end'])
        if line_coord not in seen_coords:
            outer_lines.append(line)
            seen_coords.add(line_coord)
    
    # 如果还不够20个，直接添加其他线条
    if len(outer_lines) < 20:
        for line in lines:
            if len(outer_lines) >= 20:
                break
            line_coord = (line['start'], line['end'])
            if line_coord not in seen_coords:
                outer_lines.append(line)
                seen_coords.add(line_coord)
    
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
    # 我们使用与PDF页面相同比例的DPI来确保比例一致
    # 对于A4页面(595.27 x 841.89 points)，使用200 DPI会比较合适
    pix = page.get_pixmap(dpi=200)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    
    if pix.n == 3:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    elif pix.n == 4:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img_rgb = img
    
    # 计算PDF坐标到图像像素的缩放比例
    # PDF中的坐标单位是points，而图像中是pixels
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