#!/usr/bin/env python3

import sys
import os
from PIL import Image, ImageDraw

# 导入常量
from constants import K_MAX

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

def split_image_by_symmetry(img_path, symmetry_positions, output_dir, manual_split_k=0):
    """
    根据对称位置将图片分割成若干块
    
    Args:
        img_path: 原始图片路径
        symmetry_positions: 对称位置列表
        output_dir: 输出目录
        manual_split_k: 手动第一次分割位置，取值范围为0到K_MAX
                      如果为0，按现有逻辑处理；如果不为0，以最中间位置m加减k作为第一组分割
    
    Returns:
        list: 分割后的图片路径列表
    """
    # 打开原始图片
    img = Image.open(img_path)
    width, height = img.size
    
    # 计算图片中间位置
    mid_width = width // 2
    
    # 验证manual_split_k参数
    if manual_split_k > 0:
        if manual_split_k > K_MAX:
            print(f"警告：manual_split_k值({manual_split_k})超过最大允许值({K_MAX})，将使用最大值")
            manual_split_k = K_MAX
        elif manual_split_k < 0:
            print(f"警告：manual_split_k值({manual_split_k})为负数，将使用0")
            manual_split_k = 0
    
    # 提取图片名称
    img_name = os.path.splitext(os.path.basename(img_path))[0]
    
    # 收集所有分割边界
    x_lines = []  # 水平扫描结果：X坐标分割线（垂直分割线）
    y_lines = []  # 垂直扫描结果：Y坐标分割线（水平分割线）
    
    # 处理手动分割逻辑
    if manual_split_k > 0:
        print(f"使用手动分割位置k={manual_split_k}")
        # 计算手动分割的左右边界
        left_split = mid_width - manual_split_k
        right_split = mid_width + manual_split_k
        print(f"手动分割边界：{left_split} 和 {right_split}")
        
        # 添加手动分割边界
        x_lines.extend([left_split, right_split])
        
        # 分类收集横向和纵向的对称位置，忽略手动分割区间内的分割
        for pos in symmetry_positions:
            if 'top_row' in pos and 'bottom_row' in pos:
                # 横向对称位置 - horizontal扫描
                # 过滤掉位于手动分割区间内的分割
                filtered_positions = [x for x in pos['positions'] if not (left_split <= x <= right_split)]
                x_lines.extend(filtered_positions)
            elif 'left_col' in pos and 'right_col' in pos:
                # 纵向对称位置 - vertical扫描  
                y_lines.extend(pos['positions'])
    else:
        # 按原有逻辑处理
        for pos in symmetry_positions:
            if 'top_row' in pos and 'bottom_row' in pos:
                # 横向对称位置 - horizontal扫描
                x_lines.extend(pos['positions'])
            elif 'left_col' in pos and 'right_col' in pos:
                # 纵向对称位置 - vertical扫描  
                y_lines.extend(pos['positions'])
    
    print(f"水平扫描分割线（X坐标）: {sorted(x_lines)}")
    print(f"垂直扫描分割线（Y坐标）: {sorted(y_lines)}")
    
    # 添加图片边界作为起始和结束点
    x_coords = sorted(set([0] + x_lines + [width]))
    y_coords = sorted(set([0] + y_lines + [height]))
    
    print(f"垂直分割区域数: {len(x_coords)-1}")
    print(f"水平分割区域数: {len(y_coords)-1}")
    print(f"总分割区域数: {(len(x_coords)-1) * (len(y_coords)-1)}")
    
    # 创建分割区域并保存
    split_images = []
    
    # 创建输出子目录
    split_dir = os.path.join(output_dir, f"{img_name}_splits")
    os.makedirs(split_dir, exist_ok=True)
    
    # 首先收集所有区域的信息
    all_regions = []
    
    # 遍历所有网格区域
    for i in range(len(y_coords) - 1):
        for j in range(len(x_coords) - 1):
            # 提取当前区域的坐标
            x1, x2 = x_coords[j], x_coords[j+1]
            y1, y2 = y_coords[i], y_coords[i+1]
            
            # 检查区域是否有效（宽度和高度都大于0）
            if x2 > x1 and y2 > y1:
                # 记录区域信息
                all_regions.append({
                    'region_id': 0,  # 稍后将分配ID
                    'coordinates': (x1, y1, x2, y2),
                    'size': (x2 - x1, y2 - y1),
                    'grid_position': (j+1, i+1),  # 在网格中的位置
                    'order': i * (len(x_coords) - 1) + j  # 存储顺序
                })
    
    # 计算总区域数和中间位置
    total_regions = len(all_regions)
    
    if total_regions == 0:
        print("未找到有效区域")
        return []
    
    # 中间位置和其右侧位置
    middle_idx = total_regions // 2
    right_of_middle_idx = middle_idx + 1
    
    # 按order排序
    all_regions.sort(key=lambda x: x['order'])
    
    # 只保留中间和其右侧的区域
    selected_regions = []
    if right_of_middle_idx < total_regions:
        selected_regions.append(all_regions[right_of_middle_idx])
    if middle_idx < total_regions:
        selected_regions.append(all_regions[middle_idx])
    
    # 分配新的ID并保存图片
    for i, region in enumerate(selected_regions):
        # 裁剪图片
        x1, y1, x2, y2 = region['coordinates']
        region_img = img.crop((x1, y1, x2, y2))
        
        # 分配新的ID
        region_count = i + 1
        region['region_id'] = region_count
        
        # 保存区域图片
        region_path = os.path.join(split_dir, f"region_{region_count:03d}.png")
        region_img.save(region_path, format="PNG")
        
        # 更新路径
        region['path'] = region_path
        
        # 记录区域信息
        print(f"保存区域 {region_count} (第{region['grid_position'][0]}列第{region['grid_position'][1]}行): "
              f"({x1},{y1}) 到 ({x2},{y2}), 大小: {region['size'][0]}x{region['size'][1]}")

    print(f"图片已分割为 {len(selected_regions)} 个区域")
    print(f"分割结果保存在: {split_dir}")
    
    return selected_regions

def find_symmetry_positions(img_path, output_dir=".", directions=["horizontal", "vertical"], center_skip_width=5, manual_split_k=0):
    """
    寻找对称的非白色像素位置
    
    Args:
        img_path: 图片路径
        output_dir: 输出目录
        directions: 扫描方向列表，horizontal(横向)或vertical(纵向)
        center_skip_width: 中间跳过区域宽度（像素）
        manual_split_k: 手动第一次分割位置，取值范围为0到K_MAX
                      如果为0，按现有逻辑处理；如果不为0，以最中间位置m加减k作为第一组分割

    Returns:
        tuple: (所有对称位置列表, 可视化图片路径, 分割后的图片路径列表)
    """
    # 打开图片
    img = Image.open(img_path)
    width, height = img.size
    
    # 转换为RGB模式
    img_rgb = img.convert("RGB")
    
    # 创建可视化图片副本
    visualize_img = img_rgb.copy()
    draw = ImageDraw.Draw(visualize_img)
    
    # 存储找到的对称位置
    all_symmetry_positions = []
    line_counter = 1  # 线条编号计数器
    
    # 遍历所有扫描方向
    for direction in directions:
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
                
                # 存储当前行的非白色像素位置
                top_positions = []
                bottom_positions = []
                
                # 扫描上行
                for x in range(width):
                    # 跳过中间区域（如果center_skip_width > 0）
                    if center_skip_width > 0:
                        center_start = width // 2 - center_skip_width // 2
                        center_end = width // 2 + center_skip_width // 2
                        if center_start <= x <= center_end:
                            continue
                    pixel = img_rgb.getpixel((x, top_row))
                    if not is_white_pixel(pixel):
                        top_positions.append(x)
                
                # 扫描下行
                for x in range(width):
                    # 跳过中间区域（如果center_skip_width > 0）
                    if center_skip_width > 0:
                        center_start = width // 2 - center_skip_width // 2
                        center_end = width // 2 + center_skip_width // 2
                        if center_start <= x <= center_end:
                            continue
                    pixel = img_rgb.getpixel((x, bottom_row))
                    if not is_white_pixel(pixel):
                        bottom_positions.append(x)
                
                # 移除相邻位置
                filtered_top = remove_adjacent_positions(top_positions)
                filtered_bottom = remove_adjacent_positions(bottom_positions)
                
                # 1. 取上下行的交集
                set_top = set(filtered_top)
                set_bottom = set(filtered_bottom)
                intersection = list(set_top.intersection(set_bottom))
                
                # 有效位置数量要求：至少6个元素
                if intersection and len(intersection) >= 6:
                    # 对交集进行排序
                    sorted_intersection = sorted(intersection)
                    
                    # 进一步处理有效位置
                    processed_positions = sorted_intersection.copy()
                    
                    # 跳过中间，理论上不会产生奇数个位置
                    # # 1. 如果是奇数个位置，舍弃最中间的
                    # if len(processed_positions) % 2 != 0:
                    #     mid_index = len(processed_positions) // 2
                    #     processed_positions.pop(mid_index)
                    
                    # 2. 检查并替换同一侧距离显著小的相邻位置
                    if len(processed_positions) >= 2:
                        # 计算图片中心对称轴
                        center_axis = width / 2
                        
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
                    
                    # 存储对称位置
                    pos_data = {
                        'top_row': top_row,
                        'bottom_row': bottom_row,
                        'positions': processed_positions,
                        'original_positions': sorted_intersection,
                        'original_top': filtered_top,
                        'original_bottom': filtered_bottom,
                        'line_number': line_counter,
                        'direction': 'horizontal'
                    }
                    symmetry_positions.append(pos_data)
                    all_symmetry_positions.append(pos_data)
                    
                    # 可视化标记
                    for x in processed_positions:
                        # 检查是否在手动分割区间内
                        if manual_split_k > 0:
                            mid_width = width // 2
                            left_split = mid_width - manual_split_k
                            right_split = mid_width + manual_split_k
                            if left_split <= x <= right_split:
                                continue  # 跳过手动分割区间内的线条
                        
                        # 标记上行像素
                        draw.rectangle([(x-2, top_row-2), (x+2, top_row+2)], fill="red")
                        # 标记下行像素
                        draw.rectangle([(x-2, bottom_row-2), (x+2, bottom_row+2)], fill="blue")
                        # 标记对称线
                        draw.line([(x, top_row), (x, bottom_row)], fill="green", width=1)
                    
                    line_counter += 1
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
                
                # 1. 取左右列的交集
                set_left = set(filtered_left)
                set_right = set(filtered_right)
                intersection = list(set_left.intersection(set_right))
                
                # 有效位置数量要求：至少4个元素（纵向要求降低）
                if intersection and len(intersection) >= 4:
                    # 对交集进行排序
                    sorted_intersection = sorted(intersection)
                    
                    # 进一步处理有效位置
                    processed_positions = sorted_intersection.copy()
                    
                    # 1. 如果是奇数个位置，舍弃最中间的
                    if len(processed_positions) % 2 != 0:
                        mid_index = len(processed_positions) // 2
                        processed_positions.pop(mid_index)
                    
                    # 2. 检查并替换同一侧距离显著小的相邻位置
                    if len(processed_positions) >= 2:
                        # 计算图片中心对称轴
                        center_axis = height / 2
                        
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
                    
                    # 仅保留最外侧一对的两个点
                    if len(processed_positions) >= 2:
                        # 最外侧的两个点是第一个和最后一个
                        final_positions = [processed_positions[0], processed_positions[-1]]
                    else:
                        final_positions = processed_positions
                    
                    # 存储对称位置
                    pos_data = {
                        'left_col': left_col,
                        'right_col': right_col,
                        'positions': final_positions,
                        'original_positions': sorted_intersection,
                        'processed_positions': processed_positions,
                        'original_left': filtered_left,
                        'original_right': filtered_right,
                        'line_number': line_counter,
                        'direction': 'vertical'
                    }
                    symmetry_positions.append(pos_data)
                    all_symmetry_positions.append(pos_data)
                    
                    # 可视化标记
                    for y in final_positions:
                        # 标记左列像素
                        draw.rectangle([(left_col-2, y-2), (left_col+2, y+2)], fill="red")
                        # 标记右列像素
                        draw.rectangle([(right_col-2, y-2), (right_col+2, y+2)], fill="blue")
                        # 标记对称线
                        draw.line([(left_col, y), (right_col, y)], fill="green", width=1)
                    
                    line_counter += 1
                    found = True
                    break  # 只找第一组有效位置
    
    # 处理手动分割位置的可视化
    if manual_split_k > 0:
        print(f"可视化手动分割位置k={manual_split_k}")
        # 计算图片中间位置
        mid_width = width // 2
        
        # 验证manual_split_k参数
        max_k = K_MAX
        if manual_split_k > max_k:
            manual_split_k = max_k
        elif manual_split_k < 0:
            manual_split_k = 0
        
        # 计算手动分割的左右边界
        left_split = mid_width - manual_split_k
        right_split = mid_width + manual_split_k
        print(f"手动分割边界：{left_split} 和 {right_split}")
        
        # 绘制手动分割边界（红色虚线）
        # 使用短线段绘制虚线
        dash_length = 5
        gap_length = 5
        
        # 绘制左边界虚线
        y = 0
        while y < height:
            segment_end = min(y + dash_length, height-1)
            draw.line([(left_split, y), (left_split, segment_end)], fill="red", width=2)
            y += dash_length + gap_length
        
        # 绘制右边界虚线
        y = 0
        while y < height:
            segment_end = min(y + dash_length, height-1)
            draw.line([(right_split, y), (right_split, segment_end)], fill="red", width=2)
            y += dash_length + gap_length
        
        # 不添加手动分割标签，因为用户要求不显示任何文字
    
    # 提取源文件名（不含扩展名）
    img_name = os.path.splitext(os.path.basename(img_path))[0]
    
    # 保存可视化图片（合并所有方向的线），添加源文件名前缀
    visualize_path = os.path.join(output_dir, f"{img_name}_symmetry_visualization_combined.png")
    visualize_img.save(visualize_path, format="PNG")
    
    # 返回对称位置、可视化图片路径和空的分割图片列表（在main函数中单独处理分割）
    return all_symmetry_positions, visualize_path, []

def process_image_for_cover_and_spine(img_path, output_dir, center_skip_width=5, manual_split_k=0):
    """
    处理图像生成封面和书脊
    
    Args:
        img_path: 原始图片路径
        output_dir: 输出目录
        center_skip_width: 中间跳过区域宽度（像素）
        manual_split_k: 手动第一次分割位置，取值范围为0到K_MAX
                      如果为0，按现有逻辑处理；如果不为0，以最中间位置m加减k作为第一组分割
    
    Returns:
        tuple: (cover_path, spine_path) 封面和书脊的路径
    """
    # 1. 执行横向和纵向扫描（合并到同一张图）
    directions = ["horizontal", "vertical"]  # 同时执行横向和纵向扫描
    symmetry_positions, visualize_path, _ = find_symmetry_positions(img_path, output_dir, directions, center_skip_width, manual_split_k)
    
    if not symmetry_positions:
        print("未找到对称位置，无法进行分割")
        return None, None
    
    print(f"找到 {len(symmetry_positions)} 组对称位置")
    
    # 2. 根据对称位置分割图片
    split_images = split_image_by_symmetry(img_path, symmetry_positions, output_dir, manual_split_k)
    
    if not split_images:
        print("未成功分割图片")
        return None, None
    
    print(f"图片已分割为 {len(split_images)} 个区域")
    
    # 3. 将分割后的区域保存为cover和spine
    cover_path = None
    spine_path = None
    
    # 第一个分割区域作为cover
    if len(split_images) >= 1:
        cover_region = split_images[0]
        cover_path = os.path.join(output_dir, "cover.jpg")
        cover_img = Image.open(cover_region['path'])
        cover_img.save(cover_path, format="JPEG", quality=95)
        print(f"已生成cover图片: {cover_path}")
    
    # 第二个分割区域作为spine
    if len(split_images) >= 2:
        spine_region = split_images[1]
        spine_path = os.path.join(output_dir, "spine.jpg")
        spine_img = Image.open(spine_region['path'])
        spine_img.save(spine_path, format="JPEG", quality=95)
        print(f"已生成spine图片: {spine_path}")
    
    return cover_path, spine_path


def main():
    """主函数"""
    # 默认输入图像路径
    default_img_path = ""
    
    # 解析命令行参数
    img_path = default_img_path
    output_dir = "output"
    
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
    else:
        print("错误：请提供图像文件路径作为参数！")
        print("用法：python find_symmetry.py <图像文件路径> [输出目录]")
        sys.exit(1)
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    # 检查文件是否存在
    if not os.path.exists(img_path):
        print(f"错误：文件 {img_path} 不存在！")
        sys.exit(1)
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 处理图像生成封面和书脊
    cover_path, spine_path = process_image_for_cover_and_spine(img_path, output_dir)
    
    print(f"\n所有输出已保存到目录: {output_dir}")

if __name__ == "__main__":
    main()
