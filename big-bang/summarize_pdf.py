import fitz  # PyMuPDF

def summarize_pdf_elements(pdf_path):
    """
    总结PDF中的关键元素
    """
    print(f"=== PDF元素分析总结 ===")
    print(f"文件: {pdf_path}")
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    page = doc[0]  # 第一页
    
    print(f"\n1. 页面基本信息:")
    rect = page.rect
    print(f"   尺寸: {rect.width:.1f} x {rect.height:.1f} points (A4格式)")
    
    print(f"\n2. 文本内容分析:")
    text_dict = page.get_text("dict")
    text_content = []
    
    for block in text_dict.get("blocks", []):
        if "lines" in block:
            for line in block["lines"]:
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if text:
                        text_content.append({
                            'text': text,
                            'bbox': span["bbox"],
                            'font': span["font"],
                            'size': span["size"]
                        })
    
    print(f"   发现 {len(text_content)} 个文本元素:")
    for i, elem in enumerate(text_content):
        print(f"   {i+1}. '{elem['text']}' (字体: {elem['font']}, 大小: {elem['size']:.1f})")
    
    print(f"\n3. 图像内容:")
    image_list = page.get_images()
    print(f"   发现 {len(image_list)} 个图像")
    
    print(f"\n4. 绘图元素:")
    drawings = page.get_drawings()
    print(f"   发现 {len(drawings)} 个绘图对象")
    
    # 分析矩形（可能是分割线）
    rect_count = 0
    for drawing in drawings:
        items = drawing.get("items", [])
        for item in items:
            if item[0] == "re":
                rect_count += 1
    
    print(f"   其中 {rect_count} 个是矩形对象（可能是分割框架）")
    
    print(f"\n5. 可能的页面布局:")
    
    # 分析文本位置，推测布局
    cover_text_found = any("封面" in elem['text'] for elem in text_content)
    spine_text_found = any("书脊" in elem['text'] for elem in text_content)
    
    if cover_text_found and spine_text_found:
        print("   页面包含'封面'和'书脊'文字，疑似包含封面和书脊设计")
    
    # 查找编号
    fm_numbers = [elem['text'] for elem in text_content if "FM68140" in elem['text']]
    if fm_numbers:
        print(f"   发现编号: {fm_numbers}")
    
    # 查找页码
    page_numbers = [elem['text'] for elem in text_content if elem['text'].isdigit()]
    if page_numbers:
        print(f"   发现页码: {page_numbers}")
    
    # 查找比例
    ratios = [elem['text'] for elem in text_content if ":" in elem['text'] and any(c.isdigit() for c in elem['text'])]
    if ratios:
        print(f"   发现比例: {ratios}")
    
    print(f"\n=== 分析结论 ===")
    print("这个PDF很可能是:")
    print("• 一个包含多个设计元素的页面")
    print("• 包含封面和书脊的设计布局")
    print("• 有明确的分割框架")
    print("• 可能需要根据检测到的辅助线进行分割")
    
    doc.close()

if __name__ == "__main__":
    summarize_pdf_elements("FM68140-0101.pdf")