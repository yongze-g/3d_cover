# 3D图书封面渲染器

> **重要声明**：本项目由AI辅助生成，目前处于测试阶段，尚未正式发布。功能可能存在不完善之处，欢迎反馈问题和改进建议。

一个用于生成图书立体封面效果的工具，支持上传封面和书脊图片，通过调整参数实时预览并下载立体效果图片。

## 功能特点

- ✅ 支持上传封面和书脊图片（支持多书脊模式）
- ✅ 支持平装和精装两种书型
- ✅ 支持书脊阴影效果（无/线性/反射）
- ✅ 可调整相机与书距离、开本宽度、旋转角度等参数
- ✅ 支持书脊额外展开角度调节
- ✅ 支持相机高度比例调整，获得不同视角
- ✅ 支持书脊拉伸功能，解决书脊视觉过薄问题
- ✅ 自定义背景颜色和透明度设置
- ✅ 可调整输出图像尺寸和边框占比
- ✅ 实时预览渲染结果
- ✅ 支持示例图片功能（一键使用示例图片）
- ✅ 支持下载示例图片包（zip格式）
- ✅ 下载生成的3D封面图片（支持透明背景PNG格式）
- ✅ 支持Web界面和命令行两种使用方式
- ✅ 内置PDF封面和书脊提取功能（big-bang子项目）
  - 支持从带血线的PDF文件中自动提取封面和书脊
  - 支持手动分割位置设置，提高提取准确性
  - 支持中间跳过区域宽度调整，避开血线干扰
  - 提供可视化预览，显示分割边界
  - 支持Web界面和命令行两种使用方式
- ✅ 支持PDF到3D封面一步生成功能
- ✅ 支持配置文件（JSON格式）批量设置参数

## 技术栈

- **编程语言**: Python 3.9+
- **图像处理**: OpenCV, NumPy, Pillow
- **Web界面**: Streamlit

## 快速开始

### 方法1: Web界面（推荐）

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **启动应用**
   ```bash
   streamlit run app.py
   ```

3. **使用指南**
   - 上传封面和书脊图片
   - 调整侧边栏的渲染参数
   - 实时查看预览效果
   - 点击"下载立体封"保存结果

### 方法2: 命令行快速生成

```bash
# 基本使用
python cli.py --cover example/cover.png --spine example/spine1.png --output result.png

# 从PDF直接生成立体封
python pdf_to_3dcover.py --pdf sample.pdf --output 3d_cover.png
```

## 安装指南

### 方法1: 使用Conda环境（推荐）

```bash
# 创建并激活conda环境
conda create -n 3d_cover python=3.9 -y
conda activate 3d_cover

# 安装依赖
pip install -r requirements.txt
```

### 方法2: 使用Python虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
env\Scripts\activate
# macOS/Linux
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 方法1: Web界面

1. 激活环境（如果尚未激活）
   ```bash
   # Conda环境
   conda activate 3d_cover
   # 或Python虚拟环境
   # Windows: env\Scripts\activate
   # macOS/Linux: source venv/bin/activate
   ```

2. 运行应用程序
   ```bash
   streamlit run app.py
   ```

3. 在浏览器中打开生成的URL（通常是 http://localhost:8501）

4. 使用Web界面：
   - **上传图片**: 上传封面和书脊图片，支持多书脊上传
   - **使用示例图片**: 点击"使用示例图片"按钮快速体验
   - **从PDF提取**: 点击"从PDF提取封面和书脊"切换到PDF提取功能
   - **调整参数**: 在侧边栏调整各种渲染参数
   - **预览结果**: 实时查看渲染效果
   - **下载结果**: 点击"下载立体封"按钮保存结果

### 方法2: 命令行接口

直接通过命令行生成3D封面，无需启动Web界面。

```bash
python cli.py --cover <封面图片路径> --spine <书脊图片路径>... --output <输出图片路径> [可选参数]
```

#### 必需参数
- `--cover, -c`: 封面图片路径
- `--spine, -s`: 书脊图片路径（可以指定多个）
- `--output, -o`: 输出图片路径

#### 可选参数
- `--perspective, -p`: 旋转角度（度），默认：35
- `--distance, -d`: 相机与书距离（mm），默认：800
- `--width, -w`: 开本宽度（mm），默认：187
- `--bg-color, -b`: 背景颜色（十六进制），默认：#ffffff
- `--bg-alpha, -a`: 背景透明度（0-100），默认：100
- `--spine-spread, -ss`: 书脊额外展开角度（度），默认：0
- `--camera-height, -ch`: 相机高度比例（0-1），默认：0.5
- `--final-size, -fs`: 最终图像尺寸（像素），默认：1200
- `--border, -bd`: 边框占比（0-0.2），默认：0.05
- `--book-type, -bt`: 书型（平装/精装），默认：平装
- `--shadow-mode, -sm`: 书脊阴影模式（无/线性/反射），默认：线性
- `--spine-width, -sw`: 书脊拉伸比例（1.0-2.0），默认：1.0
- `--config, -C`: 配置文件路径（JSON格式），配置文件中的参数会被命令行参数覆盖

#### 示例
```bash
# 使用默认参数生成3D封面
python cli.py --cover cover.jpg --spine spine1.jpg --output result.png

# 使用自定义参数生成3D封面
python cli.py --cover cover.jpg --spine spine1.jpg spine2.jpg --output result.png \
  --perspective 45 --distance 1000 --width 200 --bg-color #f0f0f0 --bg-alpha 50 \
  --spine-width 1.2 --book-type 精装 --shadow-mode 反射

# 使用配置文件
python cli.py --cover cover.jpg --spine spine1.jpg --output result.png --config config.json
```

### 方法3: big-bang命令行接口

直接通过命令行从PDF文件中提取封面和书脊图片。

```bash
python big-bang/cli.py --pdf <PDF文件路径> [可选参数]
```

#### 必需参数
- `--pdf, -p`: PDF文件路径

#### 可选参数
- `--output, -o`: 输出目录，默认：output
- `--center-skip, -cs`: 中间跳过区域宽度（像素），默认：5，为0时不跳过中间区域
- `--manual-split, -ms`: 手动第一次分割位置k，取值范围为0到100，默认：0，为0时按自动逻辑处理
- `--zip, -z`: 将结果打包为zip文件
- `--zip-name, -zn`: zip文件名（如果未指定，将使用PDF文件名）

#### 示例
```bash
# 基本使用
python big-bang/cli.py --pdf sample.pdf --output result

# 使用自定义参数
python big-bang/cli.py --pdf sample.pdf --output result --center-skip 10

# 生成zip包
python big-bang/cli.py --pdf sample.pdf --output result --zip
```

### 方法4: PDF到3D封面一步生成

直接从PDF文件提取封面和书脊，然后生成立体封，无需中间步骤。

```bash
python pdf_to_3dcover.py --pdf <PDF文件路径> --output <输出3D封面图片路径> [可选参数]
```

#### 必需参数
- `--pdf, -p`: PDF文件路径
- `--output, -o`: 输出3D封面图片路径

#### 可选参数
- `--center-skip, -cs`: 中间跳过区域宽度（像素），默认：5，为0时不跳过中间区域
- `--manual-split, -ms`: 手动第一次分割位置k，取值范围为0到100，默认：0，为0时按自动逻辑处理
- `--temp-dir, -t`: 临时目录（如果未指定，将使用系统临时目录）
- `--config, -C`: 配置文件路径（JSON格式）
- 以及所有3D封面渲染参数（与cli.py相同）

#### 示例
```bash
# 基本使用
python pdf_to_3dcover.py --pdf sample.pdf --output 3d_cover.png

# 使用自定义参数
python pdf_to_3dcover.py --pdf sample.pdf --output 3d_cover.png --perspective 45 --distance 1000

# 使用配置文件
python pdf_to_3dcover.py --pdf sample.pdf --output 3d_cover.png --config config.json
```

## 参数说明

### 核心参数

| 参数名称 | 描述 | 默认值 | 范围 |
|---------|------|--------|------|
| 书型选择 | 支持平装和精装两种书型 | 平装 | 平装/精装 |
| 开本宽度 | 成品图基于真实空间尺寸计算 | 187mm | - |
| 书脊阴影模式 | 选择书脊阴影效果 | 线性 | 无/线性/反射 |
| 旋转角度 | 调整立体效果的旋转角度 | 35度 | 1-89度 |
| 书脊额外展开角度 | 当书脊太窄时可增加此值 | 0度 | - |
| 书脊拉伸比例 | 解决书脊视觉过薄问题 | 1.0 | 1.0-2.0 |

### 高级参数

| 参数名称 | 描述 | 默认值 | 范围 |
|---------|------|--------|------|
| 相机与书距离 | 控制3D效果的透视深度 | 800mm | - |
| 相机相对高度比例 | 控制3D视角的垂直位置 | 0.5 | 0-1 |
| 最终图像尺寸 | 控制最终生成图像的尺寸 | 1200像素 | - |
| 边框占比 | 控制生成图像中边框的比例 | 0.05 | 0.0-0.2 |
| 背景颜色 | 设置渲染结果的背景色 | #ffffff | 十六进制颜色 |
| 背景不透明度 | 控制背景的透明程度 | 100 | 0-100 |

## 配置文件使用

配置文件是一种批量设置渲染参数的方法，使用JSON格式。

### 配置文件示例

创建一个名为`config.json`的文件：

```json
{
  "perspective_angle": 45,
  "book_distance": 1000,
  "cover_width": 190,
  "bg_color": "#ffffff",
  "bg_alpha": 100,
  "spine_spread_angle": 5,
  "camera_height_ratio": 0.5,
  "final_size": 1500,
  "border_percentage": 0.1,
  "book_type": "精装",
  "spine_shadow_mode": "线性",
  "stroke_enabled": false,
  "center_skip_width": 8,
  "manual_split_k": 0
}
```

### 配置项说明

| 配置项 | 描述 | 默认值 |
|-------|------|--------|
| perspective_angle | 旋转角度（度） | 35 |
| book_distance | 相机与书距离（mm） | 800 |
| cover_width | 开本宽度（mm） | 187 |
| bg_color | 背景颜色（十六进制） | #ffffff |
| bg_alpha | 背景透明度（0-100） | 100 |
| spine_spread_angle | 书脊额外展开角度（度） | 0 |
| camera_height_ratio | 相机高度比例（0-1） | 0.5 |
| final_size | 最终图像尺寸（像素） | 1200 |
| border_percentage | 边框占比（0-0.2） | 0.05 |
| book_type | 书型（平装/精装） | 平装 |
| spine_shadow_mode | 书脊阴影模式（无/线性/反射） | 线性 |
| stroke_enabled | 是否为封面描边 | false |
| center_skip_width | 中间跳过区域宽度（像素） | 5 |
| manual_split_k | 手动第一次分割位置k | 0 |

### 使用方法

在命令行中使用`--config`参数指定配置文件：

```bash
# 使用配置文件生成3D封面
python cli.py --cover cover.jpg --spine spine1.jpg --output result.png --config config.json

# 使用配置文件从PDF生成立体封
python pdf_to_3dcover.py --pdf sample.pdf --output 3d_cover.png --config config.json
```

**注意**：命令行参数会覆盖配置文件中的对应参数。

## 文件结构

```
3d_cover/
├── app.py                # 主应用程序入口文件（支持两个应用模式）
├── cli.py                # 命令行接口文件
├── pdf_to_3dcover.py     # PDF到3D封面一步生成工具
├── renderer.py           # 渲染器模块，处理3D封面生成核心逻辑
├── ui.py                 # 用户界面模块，处理交互界面
├── processor.py          # 处理器模块，处理图片和结果展示
├── params.py             # 参数配置文件（定义数据类）
├── requirements.txt      # 项目依赖
├── shadows/              # 阴影图片资源文件夹
│   ├── linear.png        # 线性阴影图片
│   └── reflect.png       # 反射阴影图片
├── example/              # 示例图片文件夹
│   ├── cover.png         # 示例封面图片
│   ├── spine1.png        # 示例书脊图片1
│   └── spine2.png        # 示例书脊图片2
├── test_resource/        # 测试资源文件夹
├── big-bang/             # PDF封面和书脊提取子项目
│   ├── app.py            # 子项目入口
│   ├── cli.py            # 子项目命令行接口
│   ├── constants.py      # 常量定义文件
│   ├── cover_spine_generator.py  # 封面书脊生成器
│   ├── pdf_to_images.py  # PDF转图片功能
│   └── symmetry_detection_algorithm.md  # 对称检测算法文档
└── README.md             # 项目说明文档
```

## 系统要求

- Python 3.9或更高版本
- 支持的操作系统：Windows, macOS, Linux
- 推荐至少4GB RAM以处理较大的图片文件

## 注意事项

### 图片处理
- 为获得最佳效果，请确保上传的封面和书脊图片具有相同的高度
- 支持的图片格式：PNG, JPG, JPEG
- 对于大型图片文件，处理时间可能会略有延长

### 渲染效果
- 当设置背景不透明度小于100时，下载的PNG图片将保留透明背景
- 系统会自动将多个书脊图片拼合，单书脊视为长度为1的多书脊
- 线性阴影模式可以为书脊添加更真实的阴影效果
- 书脊额外展开角度会影响透视关系的真实性
- 书脊拉伸会改变书脊的真实宽度比例

### PDF处理
- PDF提取功能基于对称检测算法，对于某些特殊设计的封面可能效果不佳
- 可以通过调整`center_skip_width`参数来优化提取效果
- 可以通过设置`manual_split_k`参数来手动指定分割位置，提高提取准确性
- 当`center_skip_width`为0时，不会跳过中间区域，会扫描整个图片宽度

## 常见问题解答（FAQ）

### Q: 为什么我的书脊看起来很薄？
A: 可以尝试以下方法：
- 增加"书脊拉伸比例"参数
- 增加"书脊额外展开角度"参数
- 选择"精装"书型

### Q: 如何获得透明背景的立体封？
A: 在侧边栏将"背景不透明度"设置为0，然后下载结果即可获得透明背景的PNG图片。

### Q: PDF提取功能无法正确识别封面和书脊怎么办？
A: 可以尝试调整`center_skip_width`参数，增加中间跳过区域的宽度，以排除封面和书脊之间的干扰。

### Q: 如何批量生成多个3D封面？
A: 可以使用配置文件和批处理脚本，例如：

```bash
# Windows批处理示例
for %%f in (*.pdf) do (
    python pdf_to_3dcover.py --pdf "%%f" --output "%%~nf_3d.png" --config config.json
)
```

## 许可证

本项目采用MIT许可证。