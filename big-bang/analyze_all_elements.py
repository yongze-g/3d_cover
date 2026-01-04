import fitz  # PyMuPDF
import cv2
import numpy as np
import os

def analyze_all_elements(pdf_path):
    """
    分析PDF中的所有元素，找出最外围的20个
    """
    print(f"=== PDF所有元素详细分析 ===")
    print(f"文件: {pdf_path}")
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    page = doc[0]  # 第一页
    
    # 获取页面尺寸
    page_width = int(page.rect.width)
    page_height = int(page.rect.height)
    print(f"页面尺寸: {page_width} x {page_height} points")
    
    # 存储所有元素
    all_elements = []
    
    # 1. 分析文本元素
    print("正在分析文本元素...")
    text_elements = analyze_text_elements(page, page_width, page_height)
    all_elements.extend(text_elements)
    print(f"发现 {len(text_elements)} 个文本元素")
    
    # 2. 分析图像元素
    print("正在分析图像元素...")
    image_elements = analyze_image_elements(page, page_width, page_height)
    all_elements.extend(image_elements)
    print(f"发现 {len(image_elements)} 个图像元素")
    
    # 3. 分析绘图元素（线条、形状等）
    print("正在分析绘图元素...")
    drawing_elements = analyze_drawing_elements(page, page_width, page_height)
    all_elements.extend(drawing_elements)
    print(f"发现 {len(drawing_elements)} 个绘图元素")
    
    # 4. 分析其他元素
    print("正在分析其他元素...")
    other_elements = analyze_other_elements(page, page_width, page_height)
    all_elements.extend(other_elements)
    print(f"发现 {len(other_elements)} 个其他元素")
    
    # 找出最外围的20个元素
    outer_elements = find_outer_elements(all_elements, page_width, page_height)
    
    # 输出前20个外围元素的详细信息
    print(f"\n=== 最外围的20个元素详细信息 ===")
    
    for i, element in enumerate(outer_elements[:20]):
        print(f"\n元素 {i+1}:")
        print(f"  类型: {element['type']}")
        print(f"  边界框: ({element['x0']:.1f}, {element['y0']:.1f}) 到 ({element['x1']:.1f}, {element['y1']:.1f})")
        print(f"  到左边缘距离: {element['dist_left']:.1f}")
        print(f"  到右边缘距离: {element['dist_right']:.1f}")
        print(f"  到上边缘距离: {element['dist_top']:.1f}")
        print(f"  到下边缘距离: {element['dist_bottom']:.1f}")
        print(f"  最小边缘距离: {element['min_dist']:.1f}")
        if 'details' in element:
            print(f"  详细信息: {element['details']}")
    
    # 生成可视化图像
    create_elements_visualization(page, outer_elements[:20], page_width, page_height)
    
    doc.close()
    return outer_elements[:20]

def analyze_other_elements(page, page_width, page_height):
    """
    分析页面上的其他元素（注释、表单字段等）
    """
    elements = []
    
    try:
        # 获取页面上的注释
        annot = page.first_annot
        while annot:
            try:
                rect = annot.rect  # 注释边界框
                x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
                
                # 计算元素到各边缘的距离
                dist_left = x0
                dist_right = page_width - x1
                dist_top = y0
                dist_bottom = page_height - y1
                min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
                
                # 获取注释类型
                annot_type = annot.type[1] if annot.type else "unknown"
                
                elements.append({
                    'type': f'annot_{annot_type}',
                    'x0': x0,
                    'y0': y0,
                    'x1': x1,
                    'y1': y1,
                    'dist_left': dist_left,
                    'dist_right': dist_right,
                    'dist_top': dist_top,
                    'dist_bottom': dist_bottom,
                    'min_dist': min_dist,
                    'details': f"注释: 类型={annot_type}, 高度={y1-y0:.1f} points, 宽度={x1-x0:.1f} points"
                })
            except Exception as e:
                print(f"处理注释时出错: {e}")
            
            annot = annot.next
        
        # 获取表单字段 - 使用PyMuPDF新API
        try:
            # 在新版本的PyMuPDF中，表单字段通过widgets属性访问
            if hasattr(page, 'widgets'):
                for field in page.widgets():
                    try:
                        rect = field.rect  # 表单字段边界框
                        x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
                        
                        # 计算元素到各边缘的距离
                        dist_left = x0
                        dist_right = page_width - x1
                        dist_top = y0
                        dist_bottom = page_height - y1
                        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
                        
                        field_type = field.field_type if hasattr(field, 'field_type') else "unknown"
                        
                        elements.append({
                            'type': f'form_{field_type}',
                            'x0': x0,
                            'y0': y0,
                            'x1': x1,
                            'y1': y1,
                            'dist_left': dist_left,
                            'dist_right': dist_right,
                            'dist_top': dist_top,
                            'dist_bottom': dist_bottom,
                            'min_dist': min_dist,
                            'details': f"表单字段: 类型={field_type}, 高度={y1-y0:.1f} points, 宽度={x1-x0:.1f} points"
                        })
                    except Exception as e:
                        print(f"处理表单字段时出错: {e}")
            else:
                print("该版本的PyMuPDF不支持widgets()方法")
        except Exception as e:
            print(f"获取表单字段时出错: {e}")
            
    except Exception as e:
        print(f"分析其他元素时出错: {e}")
    
    return elements

def analyze_text_elements(page, page_width, page_height):
    """
    分析页面上的文本元素
    """
    elements = []
    
    # 使用get_text("dict")获取所有文本信息
    text_dict = page.get_text("dict")
    
    for block in text_dict.get("blocks", []):
        # 只处理文本块
        if "lines" in block:
            bbox = block["bbox"]  # 边界框 [x0, y0, x1, y1]
            x0, y0, x1, y1 = bbox
            
            # 计算元素到各边缘的距离
            dist_left = x0
            dist_right = page_width - x1
            dist_top = y0
            dist_bottom = page_height - y1
            min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
            
            elements.append({
                'type': 'text',
                'x0': x0,
                'y0': y0,
                'x1': x1,
                'y1': y1,
                'dist_left': dist_left,
                'dist_right': dist_right,
                'dist_top': dist_top,
                'dist_bottom': dist_bottom,
                'min_dist': min_dist,
                'details': f"文本块: 高度={y1-y0:.1f} points, 宽度={x1-x0:.1f} points"
            })
    
    return elements

def analyze_image_elements(page, page_width, page_height):
    """
    分析页面上的图像元素
    """
    elements = []
    
    # 获取页面上的所有图像
    image_list = page.get_images()
    
    for i, img in enumerate(image_list):
        try:
            # 获取图像的边界框
            xref = img[0]  # 图像的xref
            
            # 尝试从图像列表中获取完整信息
            if len(img) >= 5:
                # img格式: [xref, smask, width, height, bpc, colorspace, ...]
                width = img[2]
                height = img[3]
                
                # 尝试获取图像位置信息
                # 如果无法获取位置，则使用页面中心位置作为默认值
                x0 = page_width / 2 - width / 2
                y0 = page_height / 2 - height / 2
                x1 = x0 + width
                y1 = y0 + height
                
                # 确保图像位置不会超出页面边界
                # 对于超出边界的图像，直接将其限制在页面边界内
                x0 = max(0, min(x0, page_width))
                y0 = max(0, min(y0, page_height))
                x1 = min(page_width, max(x1, 0))
                y1 = min(page_height, max(y1, 0))
                
                # 重新计算尺寸，确保它不会超出边界
                if x1 <= x0 or y1 <= y0:
                    # 如果图像位置有问题，使用默认位置
                    x0 = page_width / 4
                    y0 = page_height / 4
                    x1 = 3 * page_width / 4
                    y1 = 3 * page_height / 4
            else:
                # 如果无法获取完整信息，估算一个边界框
                x0 = page_width / 4
                y0 = page_height / 4
                x1 = 3 * page_width / 4
                y1 = 3 * page_height / 4
            
            # 计算元素到各边缘的距离
            dist_left = x0
            dist_right = page_width - x1
            dist_top = y0
            dist_bottom = page_height - y1
            min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
            
            elements.append({
                'type': 'image',
                'x0': x0,
                'y0': y0,
                'x1': x1,
                'y1': y1,
                'dist_left': dist_left,
                'dist_right': dist_right,
                'dist_top': dist_top,
                'dist_bottom': dist_bottom,
                'min_dist': min_dist,
                'details': f"图像 {i+1}: xref={xref}, 高度={y1-y0:.1f} points, 宽度={x1-x0:.1f} points"
            })
        except Exception as e:
            # 如果处理某个图像时出错，跳过它但记录错误
            print(f"处理图像 {i+1} 时出错: {e}")
    
    return elements

def analyze_drawing_elements(page, page_width, page_height):
    """
    分析页面上的绘图元素（线条、形状等）
    """
    elements = []
    
    # 获取所有绘图对象
    drawings = page.get_drawings()
    
    # 遍历所有绘图对象
    for drawing in drawings:
        try:
            items = drawing.get("items", [])
            bbox = drawing.get("rect", [0, 0, 0, 0])  # 边界框 [x0, y0, x1, y1]
            
            # 如果边界框有效
            if len(bbox) == 4 and (bbox[2] > bbox[0] and bbox[3] > bbox[1]):
                x0, y0, x1, y1 = bbox
                
                # 计算元素到各边缘的距离
                dist_left = x0
                dist_right = page_width - x1
                dist_top = y0
                dist_bottom = page_height - y1
                min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
                
                # 分析绘图类型
                drawing_type = "unknown"
                details = []
                
                for item in items:
                    if item[0] == "l":  # 线条
                        drawing_type = "line"
                        details.append(f"线条")
                    elif item[0] == "re":  # 矩形
                        drawing_type = "rectangle"
                        rect = item[1]
                        details.append(f"矩形: ({rect.x0:.1f}, {rect.y0:.1f}) 到 ({rect.x1:.1f}, {rect.y1:.1f})")
                    elif item[0] == "c":  # 曲线
                        drawing_type = "curve"
                        details.append(f"曲线")
                    elif item[0] == "o":  # 其他对象
                        drawing_type = "other"
                        details.append(f"其他对象")
                
                elements.append({
                    'type': drawing_type,
                    'x0': x0,
                    'y0': y0,
                    'x1': x1,
                    'y1': y1,
                    'dist_left': dist_left,
                    'dist_right': dist_right,
                    'dist_top': dist_top,
                    'dist_bottom': dist_bottom,
                    'min_dist': min_dist,
                    'details': ", ".join(details) if details else "绘图对象"
                })
        except Exception as e:
            # 如果处理某个绘图对象时出错，跳过它但记录错误
            print(f"处理绘图对象时出错: {e}")
    
    return elements

def find_outer_elements(all_elements, page_width, page_height):
    """
    从所有元素中找出最外围的20个
    """
    # 先过滤掉有负距离的元素（这些元素可能计算错误）
    valid_elements = [e for e in all_elements if e['min_dist'] >= 0]
    
    print(f"过滤前: {len(all_elements)} 个元素")
    print(f"过滤后: {len(valid_elements)} 个有效元素")
    
    # 按最小边缘距离排序（距离越小的越靠外）
    sorted_elements = sorted(valid_elements, key=lambda e: e['min_dist'])
    
    # 使用更宽松的去重策略，收集更多元素
    unique_elements = []
    for element in sorted_elements:
        # 检查是否与已有元素重复或高度重叠
        is_duplicate = False
        for existing in unique_elements:
            # 计算两个元素的交集面积与最小元素面积的比值
            x_overlap = max(0, min(element['x1'], existing['x1']) - max(element['x0'], existing['x0']))
            y_overlap = max(0, min(element['y1'], existing['y1']) - max(element['y0'], existing['y0']))
            overlap_area = x_overlap * y_overlap
            
            element_area = (element['x1'] - element['x0']) * (element['y1'] - element['y0'])
            existing_area = (existing['x1'] - existing['x0']) * (existing['y1'] - existing['y0'])
            
            # 只有当元素面积都大于0时进行比较
            if element_area > 0 and existing_area > 0:
                min_area = min(element_area, existing_area)
                # 如果交集面积超过较小元素面积的95%，认为它们是重复的
                if overlap_area / min_area > 0.95:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_elements.append(element)
        
        # 如果已经收集了足够的元素，停止
        if len(unique_elements) >= 20:
            break
    
    # 如果去重后元素不足20个，则从原始元素中补充（包含可能有负距离的元素）
    if len(unique_elements) < 20:
        print(f"去重后元素不足20个，从原始元素中补充...")
        
        # 重新按最小边缘距离排序，包括可能有负距离的元素
        sorted_all_elements = sorted(all_elements, key=lambda e: e['min_dist'])
        
        for element in sorted_all_elements:
            # 检查是否已经存在于unique_elements中
            is_duplicate = False
            for existing in unique_elements:
                # 简单的边界框比较
                if abs(element['x0'] - existing['x0']) < 5 and \
                   abs(element['y0'] - existing['y0']) < 5 and \
                   abs(element['x1'] - existing['x1']) < 5 and \
                   abs(element['y1'] - existing['y1']) < 5:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_elements.append(element)
            
            # 如果已经收集了足够的元素，停止
            if len(unique_elements) >= 20:
                break
    
    return unique_elements

def create_elements_visualization(page, elements, page_width, page_height):
    """
    创建元素可视化图像
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
    
    # 创建一个副本用于绘制元素框
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
    
    # 定义每种类型的线型
    line_styles = {
        'text': cv2.LINE_AA,          # 文本: 抗锯齿线
        'image': cv2.LINE_4,          # 图像: 4-connected line
        'line': cv2.LINE_8,           # 线条: 8-connected line
        'rectangle': cv2.LINE_AA,     # 矩形: 抗锯齿线
        'curve': cv2.LINE_AA,         # 曲线: 抗锯齿线
        'other': cv2.LINE_8,          # 其他: 8-connected line
        'unknown': cv2.LINE_8         # 未知: 8-connected line
    }
    
    # 绘制元素边界框
    for i, element in enumerate(elements):
        color = colors[i % len(colors)]
        
        # 使用缩放比例正确转换坐标
        x0 = int(element['x0'] * scale_x)
        y0 = int(element['y0'] * scale_y)
        x1 = int(element['x1'] * scale_x)
        y1 = int(element['y1'] * scale_y)
        
        # 绘制边界框
        line_style = line_styles.get(element['type'], cv2.LINE_8)
        thickness = 2
        cv2.rectangle(overlay, (x0, y0), (x1, y1), color, thickness, line_style)
        
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
    
    cv2.imwrite(os.path.join(output_dir, "elements_visualization.png"), overlay)
    print(f"可视化图像已保存到: {output_dir}/elements_visualization.png")
    
    # 创建详细报告
    create_elements_report(elements, output_dir)

def create_elements_report(elements, output_dir):
    """
    创建元素分析报告
    """
    report_path = os.path.join(output_dir, "elements_report.txt")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== PDF元素分析报告 ===\n\n")
        
        for i, element in enumerate(elements):
            f.write(f"元素 {i+1}:\n")
            f.write(f"  类型: {element['type']}\n")
            f.write(f"  边界框: ({element['x0']:.1f}, {element['y0']:.1f}) 到 ({element['x1']:.1f}, {element['y1']:.1f})\n")
            f.write(f"  到左边缘距离: {element['dist_left']:.1f}\n")
            f.write(f"  到右边缘距离: {element['dist_right']:.1f}\n")
            f.write(f"  到上边缘距离: {element['dist_top']:.1f}\n")
            f.write(f"  到下边缘距离: {element['dist_bottom']:.1f}\n")
            f.write(f"  最小边缘距离: {element['min_dist']:.1f}\n")
            if 'details' in element:
                f.write(f"  详细信息: {element['details']}\n")
            f.write("\n")
    
    print(f"详细报告已保存到: {report_path}")

def analyze_other_elements(page, page_width, page_height):
    """
    分析页面上的其他元素（注释、表单字段等）
    """
    elements = []
    
    try:
        # 获取页面上的注释
        annot = page.first_annot
        while annot:
            try:
                rect = annot.rect  # 注释边界框
                x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
                
                # 计算元素到各边缘的距离
                dist_left = x0
                dist_right = page_width - x1
                dist_top = y0
                dist_bottom = page_height - y1
                min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
                
                # 获取注释类型
                annot_type = annot.type[1] if annot.type else "unknown"
                
                elements.append({
                    'type': f'annot_{annot_type}',
                    'x0': x0,
                    'y0': y0,
                    'x1': x1,
                    'y1': y1,
                    'dist_left': dist_left,
                    'dist_right': dist_right,
                    'dist_top': dist_top,
                    'dist_bottom': dist_bottom,
                    'min_dist': min_dist,
                    'details': f"注释: 类型={annot_type}, 高度={y1-y0:.1f} points, 宽度={x1-x0:.1f} points"
                })
            except Exception as e:
                print(f"处理注释时出错: {e}")
            
            annot = annot.next
        
        # 获取表单字段
        try:
            form_fields = page.get_widgets()
            for field in form_fields:
                try:
                    rect = field.rect  # 表单字段边界框
                    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
                    
                    # 计算元素到各边缘的距离
                    dist_left = x0
                    dist_right = page_width - x1
                    dist_top = y0
                    dist_bottom = page_height - y1
                    min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
                    
                    field_type = field.field_type if hasattr(field, 'field_type') else "unknown"
                    
                    elements.append({
                        'type': f'form_{field_type}',
                        'x0': x0,
                        'y0': y0,
                        'x1': x1,
                        'y1': y1,
                        'dist_left': dist_left,
                        'dist_right': dist_right,
                        'dist_top': dist_top,
                        'dist_bottom': dist_bottom,
                        'min_dist': min_dist,
                        'details': f"表单字段: 类型={field_type}, 高度={y1-y0:.1f} points, 宽度={x1-x0:.1f} points"
                    })
                except Exception as e:
                    print(f"处理表单字段时出错: {e}")
        except Exception as e:
            print(f"获取表单字段时出错: {e}")
            
    except Exception as e:
        print(f"分析其他元素时出错: {e}")
    
    return elements

if __name__ == "__main__":
    analyze_all_elements("FM68140-0101.pdf")