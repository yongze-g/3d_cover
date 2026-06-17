# 3D Cover 项目记忆

## 项目架构
- 核心渲染: renderer.py (BookCoverRenderer 类)
- 参数传递: side_bar.py → app.py → params.py (UIParams/RenderParams) → processor.py → renderer.py
- 多页面路由: app.py (main/big-bang), app_pdf.py (PDF整合版)
- CLI: cli.py, pdf_to_3dcover.py, big-bang/cli.py
- PDF提取: big-bang/ (pdf_to_images.py, cover_spine_generator.py)

## 关键约定
- border_percentage 默认值: 0.05 (已统一)
- 书型选项: 平装 / 精装 (2.5D已砍除)
- st.image 使用 use_container_width=True (不用 width='stretch')
- renderer.py render_3d_cover 方法不再有 is_2d 参数

## 已知待改进
- app.py big_bang_app() 使用 exec() → 应改为 import
- cover_spine_generator.py find_symmetry_positions 函数过长 → 应拆分
