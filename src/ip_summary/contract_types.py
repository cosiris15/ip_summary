"""合同类型定义和识别模块。

基于《各类合同备注参考标准_20251124SD.docx》定义的14种合同类型。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class ContractType:
    """合同类型定义。"""
    name: str
    keywords: List[str]
    template: str


def load_contract_types(config_path: Path) -> Dict[str, ContractType]:
    """从YAML配置文件加载合同类型定义。

    Args:
        config_path: 配置文件路径

    Returns:
        合同类型名称到ContractType对象的映射
    """
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    types = {}
    for name, cfg in data.get("contract_types", {}).items():
        types[name] = ContractType(
            name=name,
            keywords=cfg.get("keywords", []),
            template=cfg.get("template", ""),
        )
    return types


def identify_contract_type_by_keywords(
    contract_text: str,
    contract_types: Dict[str, ContractType],
) -> Optional[str]:
    """基于关键词初步识别合同类型。

    这是一个快速预筛选，最终类型由LLM确定。

    Args:
        contract_text: 合同全文
        contract_types: 合同类型定义

    Returns:
        最可能的合同类型名称，如果无法识别则返回None
    """
    scores: Dict[str, int] = {}

    for type_name, ct in contract_types.items():
        if not ct.keywords:  # 跳过没有关键词的类型（如通用类型）
            continue
        score = sum(1 for kw in ct.keywords if kw in contract_text)
        if score > 0:
            scores[type_name] = score

    if not scores:
        return None

    # 返回匹配关键词最多的类型
    return max(scores, key=lambda k: scores[k])


def get_type_names_for_prompt(contract_types: Dict[str, ContractType]) -> str:
    """生成用于LLM prompt的类型列表说明。

    Args:
        contract_types: 合同类型定义

    Returns:
        格式化的类型列表字符串
    """
    lines = []
    for i, (name, ct) in enumerate(contract_types.items(), 1):
        keywords_str = "、".join(ct.keywords[:3]) if ct.keywords else "无特定关键词"
        lines.append(f"{i}. {name}（关键特征：{keywords_str}）")
    return "\n".join(lines)
