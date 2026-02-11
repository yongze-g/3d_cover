from dataclasses import dataclass
from typing import List, Optional, Any
from PIL import Image


@dataclass
class UIParams:
    """
    UI参数数据类，封装所有UI相关参数
    """
    cover_image: Optional[Any] = None
    spine_images: Optional[List[Any]] = None
    result_placeholder: Optional[Any] = None
    download_placeholder: Optional[Any] = None
    book_distance: int = 800
    cover_width: int = 187
    perspective_angle: int = 35
    bg_color: str = "#ffffff"
    bg_alpha: int = 100
    spine_spread_angle: int = 0
    camera_height_ratio: float = 0.5
    final_size: int = 1200
    border_percentage: float = 0.1
    book_type: str = "平装"
    spine_shadow_mode: str = "线性"
    spine_width_ratio: float = 1.0
    stroke_enabled: bool = False


@dataclass
class RenderParams:
    """
    渲染参数数据类，封装所有渲染相关参数
    """
    perspective_angle: int
    book_distance: int
    cover_width: int
    bg_color: str
    bg_alpha: int
    spine_spread_angle: int
    camera_height_ratio: float
    final_size: int
    border_percentage: float
    book_type: str
    spine_shadow_mode: str
    spine_width_ratio: float
    stroke_enabled: bool
