#!/usr/bin/env python3

"""
PDF对称像素检测工具
将PDF转换为图片，从上下两端逐行寻找对称的非白色像素位置
"""

import sys
import os
import fitz  # PyMuPDF
from PIL import Image, ImageDraw

def pdf_to_image(pdf_path, output_dir="."):
    """
    将PDF转换为图片
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
    
    Returns:
        图片路径
    """
    print(f"正在将PDF转换为图片: {pdf_path}")
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    
    # 获取第一页
    page = doc[0]
    
    # 按原尺寸转换为图片
    pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # 保存图片
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    img_path = os.path.join(output_dir, "original.png")
    img.save(img_path, format="PNG")
    
    print(f"图片已保存: {img_path}")
    
    # 关闭PDF文件
    doc.close()
    
    return img_path

def is_white_pixel(pixel, tolerance=240):
    """
    判断像素是否为白色
    
    Args:
        pixel: 像素值 (R, G, B)
        tolerance: 白色容忍度
    
    Returns:
        bool: 是否为白色
    """
    return all(c >= tolerance for c in pixel)

def remove_adjacent_positions(positions, threshold=2):
    """
    对相邻的位置取平均值
    
    Args:
        positions: 位置列表
        threshold: 相邻阈值，小于等于此值的视为相邻
    
    Returns:
        处理后的位置列表
    """
    if not positions:
        return []
    
    # 排序位置列表
    sorted_positions = sorted(positions)
    
    # 对相邻位置取平均值
    groups = []
    current_group = [sorted_positions[0]]
    
    for pos in sorted_positions[1:]:
        if pos - current_group[-1] <= threshold:
            current_group.append(pos)
        else:
            # 计算当前组的平均值
            avg_pos = sum(current_group) / len(current_group)
            groups.append(round(avg_pos))
            current_group = [pos]
    
    # 处理最后一组
    if current_group:
        avg_pos = sum(current_group) / len(current_group)
        groups.append(round(avg_pos))
    
    return groups

def is_symmetric(positions1, positions2, tolerance=2):
    """
    检查两个位置列表是否对称，允许一定的误差
    
    Args:
        positions1: 第一个位置列表
        positions2: 第二个位置列表
        tolerance: 位置误差容忍度
    
    Returns:
        bool: 是否对称
    """
    # 两个列表长度必须相同
    if len(positions1) != len(positions2):
        return False
    
    # 排序两个列表
    sorted1 = sorted(positions1)
    sorted2 = sorted(positions2)
    
    # 检查每个位置是否在容忍度范围内
    for p1, p2 in zip(sorted1, sorted2):
        if abs(p1 - p2) > tolerance:
            return False
    
    return True

def find_symmetry_positions(img_path, output_dir=".", direction="horizontal"):
    """
    寻找对称的非白色像素位置
    
    Args:
        img_path: 图片路径
        output_dir: 输出目录
        direction: 扫描方向，horizontal(横向)或vertical(纵向)
    
    Returns:
        tuple: (对称位置列表, 可视化图片路径)
    """
    print(f"正在分析图片: {img_path}")
    print(f"扫描方向: {direction}")
    
    # 打开图片
    img = Image.open(img_path)
    width, height = img.size
    
    # 转换为RGB模式
    img_rgb = img.convert("RGB")
    
    # 创建可视化图片副本
    visualize_img = img_rgb.copy()
    draw = ImageDraw.Draw(visualize_img)
    
    # 存储找到的对称位置
    symmetry_positions = []
    
    if direction == "horizontal":
        # 横向扫描：从上下两端逐行检测
        mid_row = height // 2
        found = False
        
        for offset in range(height // 2):
            # 计算当前扫描行
            top_row = offset
            bottom_row = height - 1 - offset
            
            # 如果扫描到中间，停止
            if top_row > mid_row:
                break
            
            print(f"正在扫描行: {top_row} (上) 和 {bottom_row} (下)")
            
            # 存储当前行的非白色像素位置
            top_positions = []
            bottom_positions = []
            
            # 扫描上行
            for x in range(width):
                pixel = img_rgb.getpixel((x, top_row))
                if not is_white_pixel(pixel):
                    top_positions.append(x)
            
            # 扫描下行
            for x in range(width):
                pixel = img_rgb.getpixel((x, bottom_row))
                if not is_white_pixel(pixel):
                    bottom_positions.append(x)
            
            # 移除相邻位置
            filtered_top = remove_adjacent_positions(top_positions)
            filtered_bottom = remove_adjacent_positions(bottom_positions)
            
            print(f"  去重前 - 上行: {len(top_positions)}, 下行: {len(bottom_positions)}")
            print(f"  去重后 - 上行: {len(filtered_top)}, 下行: {len(filtered_bottom)}")
            
            # 1. 取上下行的交集
            set_top = set(filtered_top)
            set_bottom = set(filtered_bottom)
            intersection = list(set_top.intersection(set_bottom))
            print(f"  交集大小: {len(intersection)}")
            
            # 有效位置数量要求：至少6个元素
            if intersection and len(intersection) >= 6:
                # 对交集进行排序
                sorted_intersection = sorted(intersection)
                
                print(f"找到对称行: {top_row} 和 {bottom_row}")
                print(f"去重前非白色像素位置 - 上行: {top_positions}")
                print(f"去重前非白色像素位置 - 下行: {bottom_positions}")
                print(f"去重后非白色像素位置 - 上行: {filtered_top}")
                print(f"去重后非白色像素位置 - 下行: {filtered_bottom}")
                print(f"对称交集位置: {sorted_intersection}")
                print(f"对称位置数量: {len(sorted_intersection)}")
                
                # 进一步处理有效位置
                processed_positions = sorted_intersection.copy()
                
                # 1. 如果是奇数个位置，舍弃最中间的
                if len(processed_positions) % 2 != 0:
                    mid_index = len(processed_positions) // 2
                    print(f"  奇数个位置，舍弃中间位置: {processed_positions[mid_index]}")
                    processed_positions.pop(mid_index)
                
                # 2. 检查并替换同一侧距离显著小的相邻位置
                if len(processed_positions) >= 2:
                    # 计算图片中心对称轴
                    center_axis = width / 2
                    print(f"  图片中心对称轴: {center_axis}")
                    
                    # 计算相邻位置之间的距离
                    distances = []
                    for i in range(len(processed_positions) - 1):
                        dist = processed_positions[i+1] - processed_positions[i]
                        distances.append(dist)
                    
                    # 计算距离的平均值和标准差，找出显著小的距离
                    avg_dist = sum(distances) / len(distances)
                    if len(distances) > 1:
                        # 计算标准差
                        variance = sum((d - avg_dist) ** 2 for d in distances) / len(distances)
                        std_dev = variance ** 0.5
                        
                        # 找出显著小的距离（小于平均值的一半）
                        threshold = avg_dist / 2
                        print(f"  平均距离: {avg_dist}, 标准差: {std_dev}, 阈值: {threshold}")
                        
                        # 从右向左检查，避免索引问题
                        for i in range(len(distances) - 1, -1, -1):
                            if distances[i] < threshold:
                                pos1 = processed_positions[i]
                                pos2 = processed_positions[i+1]
                                
                                # 检查是否在同一侧
                                pos1_side = "left" if pos1 < center_axis else "right"
                                pos2_side = "left" if pos2 < center_axis else "right"
                                
                                if pos1_side == pos2_side:
                                    # 计算平均值
                                    avg_pos = round((pos1 + pos2) / 2)
                                    print(f"  替换位置 {pos1} 和 {pos2} 为平均值 {avg_pos}")
                                    
                                    # 替换这两个位置为平均值
                                    processed_positions.pop(i+1)
                                    processed_positions.pop(i)
                                    processed_positions.insert(i, avg_pos)
                                    
                                    # 重新计算距离
                                    distances = []
                                    for j in range(len(processed_positions) - 1):
                                        dist = processed_positions[j+1] - processed_positions[j]
                                        distances.append(dist)
                                    
                                    # 重新计算平均值
                                    avg_dist = sum(distances) / len(distances)
                                    threshold = avg_dist / 2
                
                print(f"  处理后位置: {processed_positions}")
                
                # 存储对称位置
                symmetry_positions.append({
                    'top_row': top_row,
                    'bottom_row': bottom_row,
                    'positions': processed_positions,
                    'original_positions': sorted_intersection,
                    'original_top': filtered_top,
                    'original_bottom': filtered_bottom
                })
                
                # 可视化标记
                for x in processed_positions:
                    # 标记上行像素
                    draw.rectangle([(x-2, top_row-2), (x+2, top_row+2)], fill="red")
                    # 标记下行像素
                    draw.rectangle([(x-2, bottom_row-2), (x+2, bottom_row+2)], fill="blue")
                    # 标记对称线
                    draw.line([(x, top_row), (x, bottom_row)], fill="green", width=1)
                
                found = True
                break  # 只找第一组有效位置
    
    elif direction == "vertical":
        # 纵向扫描：从左右两端逐列检测
        mid_col = width // 2
        found = False
        
        for offset in range(width // 2):
            # 计算当前扫描列
            left_col = offset
            right_col = width - 1 - offset
            
            # 如果扫描到中间，停止
            if left_col > mid_col:
                break
            
            print(f"正在扫描列: {left_col} (左) 和 {right_col} (右)")
            
            # 存储当前列的非白色像素位置
            left_positions = []
            right_positions = []
            
            # 扫描左列
            for y in range(height):
                pixel = img_rgb.getpixel((left_col, y))
                if not is_white_pixel(pixel):
                    left_positions.append(y)
            
            # 扫描右列
            for y in range(height):
                pixel = img_rgb.getpixel((right_col, y))
                if not is_white_pixel(pixel):
                    right_positions.append(y)
            
            # 移除相邻位置
            filtered_left = remove_adjacent_positions(left_positions)
            filtered_right = remove_adjacent_positions(right_positions)
            
            print(f"  去重前 - 左列: {len(left_positions)}, 右列: {len(right_positions)}")
            print(f"  去重后 - 左列: {len(filtered_left)}, 右列: {len(filtered_right)}")
            
            # 1. 取左右列的交集
            set_left = set(filtered_left)
            set_right = set(filtered_right)
            intersection = list(set_left.intersection(set_right))
            print(f"  交集大小: {len(intersection)}")
            
            # 有效位置数量要求：至少4个元素（纵向要求降低）
            if intersection and len(intersection) >= 4:
                # 对交集进行排序
                sorted_intersection = sorted(intersection)
                
                print(f"找到对称列: {left_col} 和 {right_col}")
                print(f"去重前非白色像素位置 - 左列: {left_positions}")
                print(f"去重前非白色像素位置 - 右列: {right_positions}")
                print(f"去重后非白色像素位置 - 左列: {filtered_left}")
                print(f"去重后非白色像素位置 - 右列: {filtered_right}")
                print(f"对称交集位置: {sorted_intersection}")
                print(f"对称位置数量: {len(sorted_intersection)}")
                
                # 进一步处理有效位置
                processed_positions = sorted_intersection.copy()
                
                # 1. 如果是奇数个位置，舍弃最中间的
                if len(processed_positions) % 2 != 0:
                    mid_index = len(processed_positions) // 2
                    print(f"  奇数个位置，舍弃中间位置: {processed_positions[mid_index]}")
                    processed_positions.pop(mid_index)
                
                # 2. 检查并替换同一侧距离显著小的相邻位置
                if len(processed_positions) >= 2:
                    # 计算图片中心对称轴
                    center_axis = height / 2
                    print(f"  图片中心对称轴: {center_axis}")
                    
                    # 计算相邻位置之间的距离
                    distances = []
                    for i in range(len(processed_positions) - 1):
                        dist = processed_positions[i+1] - processed_positions[i]
                        distances.append(dist)
                    
                    # 计算距离的平均值和标准差，找出显著小的距离
                    avg_dist = sum(distances) / len(distances)
                    if len(distances) > 1:
                        # 计算标准差
                        variance = sum((d - avg_dist) ** 2 for d in distances) / len(distances)
                        std_dev = variance ** 0.5
                        
                        # 找出显著小的距离（小于平均值的一半）
                        threshold = avg_dist / 2
                        print(f"  平均距离: {avg_dist}, 标准差: {std_dev}, 阈值: {threshold}")
                        
                        # 从下向上检查，避免索引问题
                        for i in range(len(distances) - 1, -1, -1):
                            if distances[i] < threshold:
                                pos1 = processed_positions[i]
                                pos2 = processed_positions[i+1]
                                
                                # 检查是否在同一侧
                                pos1_side = "top" if pos1 < center_axis else "bottom"
                                pos2_side = "top" if pos2 < center_axis else "bottom"
                                
                                if pos1_side == pos2_side:
                                    # 计算平均值
                                    avg_pos = round((pos1 + pos2) / 2)
                                    print(f"  替换位置 {pos1} 和 {pos2} 为平均值 {avg_pos}")
                                    
                                    # 替换这两个位置为平均值
                                    processed_positions.pop(i+1)
                                    processed_positions.pop(i)
                                    processed_positions.insert(i, avg_pos)
                                    
                                    # 重新计算距离
                                    distances = []
                                    for j in range(len(processed_positions) - 1):
                                        dist = processed_positions[j+1] - processed_positions[j]
                                        distances.append(dist)
                                    
                                    # 重新计算平均值
                                    avg_dist = sum(distances) / len(distances)
                                    threshold = avg_dist / 2
                
                print(f"  处理后位置: {processed_positions}")
                
                # 仅保留最外侧一对的两个点
                if len(processed_positions) >= 2:
                    # 最外侧的两个点是第一个和最后一个
                    final_positions = [processed_positions[0], processed_positions[-1]]
                    print(f"  仅保留最外侧一对: {final_positions}")
                else:
                    final_positions = processed_positions
                
                # 存储对称位置
                symmetry_positions.append({
                    'left_col': left_col,
                    'right_col': right_col,
                    'positions': final_positions,
                    'original_positions': sorted_intersection,
                    'processed_positions': processed_positions,
                    'original_left': filtered_left,
                    'original_right': filtered_right
                })
                
                # 可视化标记
                for y in final_positions:
                    # 标记左列像素
                    draw.rectangle([(left_col-2, y-2), (left_col+2, y+2)], fill="red")
                    # 标记右列像素
                    draw.rectangle([(right_col-2, y-2), (right_col+2, y+2)], fill="blue")
                    # 标记对称线
                    draw.line([(left_col, y), (right_col, y)], fill="green", width=1)
                
                found = True
                break  # 只找第一组有效位置
    
    if not found:
        print("未找到符合条件的对称位置")
    
    # 保存可视化图片
    visualize_path = os.path.join(output_dir, f"symmetry_visualization_{direction}.png")
    visualize_img.save(visualize_path, format="PNG")
    print(f"可视化结果已保存: {visualize_path}")
    
    return symmetry_positions, visualize_path

def main():
    """主函数"""
    # 默认输入PDF路径
    default_pdf_path = "/Users/yongze/Documents/GitHub/3d_cover/big-bang/frame_cv.pdf"
    
    # 解析命令行参数
    pdf_path = default_pdf_path
    output_dir = "output"
    directions = ["horizontal", "vertical"]  # 默认同时执行横向和纵向扫描
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"错误：文件 {pdf_path} 不存在！")
        sys.exit(1)
    
    # 1. 将PDF转换为图片
    img_path = pdf_to_image(pdf_path, output_dir)
    
    # 2. 分别执行横向和纵向扫描
    all_symmetry_positions = []
    
    for direction in directions:
        print(f"\n{'='*50}")
        print(f"开始{direction}扫描...")
        print(f"{'='*50}")
        
        symmetry_positions, visualize_path = find_symmetry_positions(img_path, output_dir, direction)
        all_symmetry_positions.extend(symmetry_positions)
    
    # 3. 输出结果
    print("\n=== 分析结果 ===")
    if all_symmetry_positions:
        for i, pos in enumerate(all_symmetry_positions):
            print(f"对称组 {i+1}:")
            if 'top_row' in pos:
                print(f"  类型: 横向扫描")
                print(f"  上行: {pos['top_row']}")
                print(f"  下行: {pos['bottom_row']}")
            elif 'left_col' in pos:
                print(f"  类型: 纵向扫描")
                print(f"  左列: {pos['left_col']}")
                print(f"  右列: {pos['right_col']}")
            print(f"  非白色像素位置数量: {len(pos['positions'])}")
            print(f"  位置示例: {pos['positions'][:10]}...")
    else:
        print("未找到符合条件的对称位置")
    
    print(f"\n所有输出已保存到目录: {output_dir}")

if __name__ == "__main__":
    main()
