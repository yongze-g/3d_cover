"""
3D图书封面渲染器 - 主入口文件

该应用程序允许用户上传图书封面和书脊图片，通过调整各种参数生成3D立体效果的图书封面。

结构说明：
- ui.py: 处理用户界面和交互
- renderer.py: 封装所有渲染相关功能
- processor.py: 处理图像处理逻辑
- app.py: 主入口文件，协调各模块
- types.py: 定义数据类，封装参数
- big-bang/: 附属功能，PDF封面和书脊提取
"""

import streamlit as st
import sys
import os

# 添加big-bang目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'big-bang'))

st.set_page_config(
    page_title="立体封渲染器",
    page_icon="📚",
    layout="wide"
)

def main_app():
    
    # 原有功能
    from ui import setup_ui
    from processor import process_images
    
    # 设置用户界面并获取UI元素
    ui_params = setup_ui()
    
    # 处理图像并渲染3D封面
    process_images(ui_params)


def big_bang_app():
    # 返回主应用的按钮
    if st.button("← 返回立体封渲染器", type="secondary"):
        st.query_params["page"] = "main"
        st.rerun()
    
    # 导入并运行big-bang的功能
    # 直接执行big-bang/app.py文件，并在新的命名空间中调用其中的run_big_bang_app函数
    big_bang_app_path = os.path.join(os.path.dirname(__file__), 'big-bang', 'app.py')
    
    # 创建一个新的模块命名空间
    big_bang_module = {}
    
    # 执行big-bang/app.py文件，将其内容加载到新的命名空间中
    exec(open(big_bang_app_path, 'r', encoding='utf-8').read(), big_bang_module)
    
    # 调用其中的run_big_bang_app函数
    big_bang_module['run_big_bang_app']()


def main():
    """根据查询参数决定显示哪个应用"""
    # 获取当前页面参数
    page = st.query_params.get("page", "main")
    
    if page == "big-bang":
        big_bang_app()
    else:
        main_app()


if __name__ == "__main__":
    main()
