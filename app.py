"""
3D图书封面渲染器 - 主入口文件

该应用程序允许用户上传图书封面和书脊图片，通过调整各种参数生成3D立体效果的图书封面。

结构说明：
- ui.py: 处理用户界面和交互
- renderer.py: 封装所有渲染相关功能
- processor.py: 处理图像处理逻辑
- app.py: 主入口文件，协调各模块
"""

# 导入必要的模块
from ui import setup_ui
from processor import process_images


def main():
    """
    主函数，协调整个应用程序的流程
    """
    # 设置用户界面并获取UI元素
    ui_elements = setup_ui()
    
    # 处理图像并渲染3D封面
    process_images(*ui_elements)


if __name__ == "__main__":
    main()