import fitz  # PyMuPDF
import numpy as np
import cv2
from PIL import Image
import os

def analyze_pdf_elements(pdf_path):
    """
    分析PDF中的各种元素：文本、图片、线条等
    """
    print(f"正在分析PDF文件: {pdf_path}")
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"PDF总页数: {total_pages}")
    
    for page_num in range(total_pages):
        print(f"\n{'='*50}")
        print(f"分析第 {page_num + 1} 页")
        print(f"{'='*50}")
        
        page = doc[page_num]
        
        # 获取页面基本信息
        rect = page.rect
        print(f"页面尺寸: {rect.width:.2f} x {rect.height:.2f}")
        
        # 1. 分析文本内容
        text_dict = page.get_text("dict")
        text_elements = []
        
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        if span["text"].strip():
                            text_elements.append({
                                'text': span["text"].strip(),
                                'bbox': span["bbox"],
                                'font': span["font"],
                                'size': span["size"],
                                'flags': span["flags"]
                            })
        
        print(f"\n文本元素数量: {len(text_elements)}")
        print("主要文本内容:")
        for i, elem in enumerate(text_elements[:10]):  # 只显示前10个
            print(f"  {i+1}. {elem['text'][:50]}...")
            print(f"     位置: {elem['bbox']}")
            print(f"     字体: {elem['font']}, 大小: {elem['size']:.1f}")
        
        if len(text_elements) > 10:
            print(f"  ... 还有 {len(text_elements) - 10} 个文本元素")
        
        # 2. 分析图像
        image_list = page.get_images()
        print(f"\n图像数量: {len(image_list)}")
        
        for i, img in enumerate(image_list):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            print(f"  图像 {i+1}: {pix.width} x {pix.height} pixels")
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                print(f"    格式: {'RGB' if pix.n == 3 else 'GRAY'}")
            else:  # CMYK
                print(f"    格式: CMYK")
            pix = None  # 释放内存
        
        # 3. 分析绘图对象
        drawings = page.get_drawings()
        print(f"\n绘图对象数量: {len(drawings)}")
        
        # 统计不同类型的绘图对象
        rect_count = 0
        line_count = 0
        curve_count = 0
        
        for drawing in drawings:
            items = drawing.get("items", [])
            for item in items:
                item_type = item[0]
                if item_type == "l":
                    line_count += 1
                elif item_type == "re":
                    rect_count += 1
                elif item_type in ["c", "v"]:
                    curve_count += 1
        
        print(f"  直线数量: {line_count}")
        print(f"  矩形数量: {rect_count}")
        print(f"  曲线数量: {curve_count}")
        
        # 4. 将页面转换为图像进行视觉分析
        pix = page.get_pixmap(dpi=200)  # 使用200 DPI
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        
        if pix.n == 3:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        elif pix.n == 4:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        else:
            img_rgb = img
        
        # 保存页面图像用于检查
        output_dir = "analysis_output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        cv2.imwrite(os.path.join(output_dir, f"page_{page_num+1}.png"), img_rgb)
        print(f"\n页面图像已保存到: {output_dir}/page_{page_num+1}.png")
        
        # 5. 边缘检测分析
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img.copy()
        
        # 应用边缘检测
        edges = cv2.Canny(gray, 50, 150)
        cv2.imwrite(os.path.join(output_dir, f"page_{page_num+1}_edges.png"), edges)
        
        # 霍夫线变换检测直线
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
        
        if lines is not None:
            print(f"检测到直线数量: {len(lines)}")
            
            # 分类水平和垂直线
            horizontal_lines = []
            vertical_lines = []
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                
                if abs(angle) < 5 or abs(angle - 180) < 5:
                    horizontal_lines.append((y1 + y2) // 2)
                elif abs(angle - 90) < 5 or abs(angle + 90) < 5:
                    vertical_lines.append((x1 + x2) // 2)
            
            print(f"  水平线数量: {len(horizontal_lines)}")
            print(f"  垂直线数量: {len(vertical_lines)}")
            
            # 去除重复的线
            def remove_close_lines(lines, threshold=10):
                if not lines:
                    return []
                lines.sort()
                unique_lines = [lines[0]]
                for line in lines[1:]:
                    if abs(line - unique_lines[-1]) > threshold:
                        unique_lines.append(line)
                return unique_lines
            
            horizontal_lines = remove_close_lines(horizontal_lines)
            vertical_lines = remove_close_lines(vertical_lines)
            
            print(f"  去重后水平线位置: {horizontal_lines}")
            print(f"  去重后垂直线位置: {vertical_lines}")
        
        # 6. 可能的分割区域分析
        if lines is not None and horizontal_lines and vertical_lines:
            print(f"\n可能的分割区域:")
            all_h_lines = [0] + horizontal_lines + [pix.h]
            all_v_lines = [0] + vertical_lines + [pix.w]
            
            for i, h_line in enumerate(all_h_lines):
                for j, v_line in enumerate(all_v_lines):
                    if i > 0 and j > 0:
                        region_height = h_line - all_h_lines[i-1]
                        region_width = v_line - all_v_lines[j-1]
                        if region_height > 50 and region_width > 50:  # 最小区域大小
                            print(f"  区域 {i}-{j}: ({region_width} x {region_height}) pixels")
        
        print(f"\n第 {page_num + 1} 页分析完成")
    
    doc.close()
    print(f"\n所有页面分析完成！")
    print(f"输出文件保存在: {output_dir} 目录中")

if __name__ == "__main__":
    pdf_path = "FM68140-0101.pdf"
    
    if os.path.exists(pdf_path):
        analyze_pdf_elements(pdf_path)
    else:
        print(f"PDF文件不存在: {pdf_path}")
        print("当前目录内容:")
        for file in os.listdir("."):
            if file.endswith(".pdf"):
                print(f"  发现PDF文件: {file}")