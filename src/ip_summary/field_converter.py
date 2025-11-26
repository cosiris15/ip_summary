"""字段值转换模块。

用于将可读文字值转换为入库所需的编号。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml


def load_field_mappings(config_path: Path) -> Dict[str, Dict[str, int]]:
    """从YAML配置文件加载字段映射。

    Args:
        config_path: 配置文件路径

    Returns:
        字段名 -> (文字值 -> 编号) 的映射
    """
    if not config_path.exists():
        return {}

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("field_mappings", {})


def _normalize_field_name(field_name: str) -> str:
    """规范化字段名，去除编号说明部分。

    例如：'合同类型 1：主合同，2 补充合同3 终止合同' -> '合同类型'
    """
    # 找到第一个数字或冒号的位置
    for i, char in enumerate(field_name):
        if char.isdigit() or char in "：:（(":
            return field_name[:i].strip()
    return field_name.strip()


def _find_mapping_for_field(
    field_name: str, mappings: Dict[str, Dict[str, int]]
) -> Optional[Dict[str, int]]:
    """根据字段名找到对应的映射表。

    支持模糊匹配，例如 '合同类型 1：主合同...' 可以匹配 '合同类型'。
    """
    normalized = _normalize_field_name(field_name)

    # 精确匹配
    if normalized in mappings:
        return mappings[normalized]

    # 部分匹配（字段名包含映射键）
    for key in mappings:
        if key in normalized or normalized in key:
            return mappings[key]

    return None


def convert_value_to_code(
    field_name: str,
    value: Any,
    mappings: Dict[str, Dict[str, int]],
) -> Union[int, str, Any]:
    """将字段的文字值转换为编号。

    Args:
        field_name: 字段名
        value: 原始值（可能是文字或已经是编号）
        mappings: 字段映射配置

    Returns:
        转换后的编号，如果无法转换则返回原值
    """
    if value is None:
        return None

    # 如果已经是数字，直接返回
    if isinstance(value, (int, float)):
        return value

    value_str = str(value).strip()

    # 尝试解析为数字
    try:
        return int(value_str)
    except ValueError:
        pass

    # 查找映射表
    mapping = _find_mapping_for_field(field_name, mappings)
    if not mapping:
        return value

    # 精确匹配
    if value_str in mapping:
        return mapping[value_str]

    # 模糊匹配（值包含映射键）
    for text, code in mapping.items():
        if text in value_str or value_str in text:
            return code

    return value


def convert_fields_to_codes(
    fields: Dict[str, Any],
    mappings: Dict[str, Dict[str, int]],
) -> Dict[str, Any]:
    """批量转换字段值为编号。

    Args:
        fields: 字段名 -> 值的映射
        mappings: 字段映射配置

    Returns:
        转换后的字段映射
    """
    return {
        field_name: convert_value_to_code(field_name, value, mappings)
        for field_name, value in fields.items()
    }


class FieldConverter:
    """字段值转换器，封装映射加载和转换功能。"""

    def __init__(self, config_path: Optional[Path] = None):
        """初始化转换器。

        Args:
            config_path: 映射配置文件路径，默认为 config/field_value_mappings.yaml
        """
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent
                / "config"
                / "field_value_mappings.yaml"
            )
        self.mappings = load_field_mappings(config_path)

    def convert(self, field_name: str, value: Any) -> Union[int, str, Any]:
        """转换单个字段值。"""
        return convert_value_to_code(field_name, value, self.mappings)

    def convert_all(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """批量转换字段值。"""
        return convert_fields_to_codes(fields, self.mappings)
