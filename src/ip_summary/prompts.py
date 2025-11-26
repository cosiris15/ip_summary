from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from .models import DirectionLiteral


PROMPT_VERSION = "v1.2"


def build_classification_messages(contract_text: str, my_party: str) -> List[Dict[str, str]]:
    system = (
        "You are a legal contract classifier for IP authorization chains. "
        "Given the contract content and the party representing 'us', decide "
        "whether the contract is upstream or downstream relative to us. "
        "Definitions: upstream = we acquire rights/commission content from the counterparty; "
        "downstream = we license/transfer/authorize rights to the counterparty. "
        "Return JSON only with keys direction (upstream/downstream), confidence (0-1), reason (max 50 Chinese characters). "
        "If both exist, pick the dominant nature."
    )
    user = (
        f"我方主体：{my_party}\n\n"
        f"合同内容：\n{contract_text}\n\n"
        '请只输出 JSON，例如 {"{"}"direction":"upstream","confidence":0.82,"reason":"...原因"}'
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_extraction_messages(
    contract_text: str,
    headers: Sequence[str],
    my_party: str,
    direction: DirectionLiteral,
) -> List[Dict[str, str]]:
    dir_cn = "上游" if direction == "upstream" else "下游"
    template_lines = [f'  "{h}": null' for h in headers]
    json_template = "{\n" + ",\n".join(template_lines) + "\n}"
    system = (
        "You are an IP authorization contract analyst. "
        "Extract required fields as JSON using the provided headers EXACTLY as keys (do not改写字段名). "
        "Use Chinese values from the contract. If a field is not present, keep it null. "
        "Prefer ISO dates (YYYY-MM-DD). Multi-values join with '、'. Do not invent data. "
        "Output MUST be raw JSON only (no Markdown, no code fences, no explanations).\n\n"
        "【重要】对于选项类字段（如'合同类型 1：主合同，2 补充合同3 终止合同'），请输出中文文字值而非编号。\n"
        "例如：\n"
        "- '合同类型'字段：输出'主合同'而非'1'\n"
        "- '我方主体'字段：输出'上海玄霆'而非'1'\n"
        "- '是否独家'字段：输出'是'或'独家'而非'1'\n"
        "- '对方类型'字段：输出'公司'或'个人'而非编号\n"
        "- 其他选项字段同理，一律输出可读的中文文字"
    )
    user = (
        f"我方主体：{my_party}\n"
        f"合同方向：{dir_cn}（direction={direction}）\n"
        "请按下方 JSON 模板填充值，键名不可改动，只替换 null 为提取结果（缺失则保留 null）。\n"
        "【注意】选项类字段请输出中文文字（如'主合同'、'公司'、'是'），不要输出编号！\n"
        f"{json_template}\n\n"
        f"合同全文：\n{contract_text}\n\n"
        "直接输出 JSON（不加```、不加额外文字）。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_type_classification_messages(
    contract_text: str,
    type_list: str,
    hint_type: Optional[str] = None,
) -> List[Dict[str, str]]:
    """构建合同类型识别的prompt。

    Args:
        contract_text: 合同全文
        type_list: 格式化的类型列表说明
        hint_type: 关键词预筛选的提示类型（可选）

    Returns:
        消息列表
    """
    system = (
        "你是一个专业的IP版权合同分类专家。请根据合同内容判断其所属的合同类型。\n"
        "只能从给定的类型列表中选择最匹配的一个类型。\n"
        "如果无法明确归类，请选择'通用类型'。\n"
        "返回JSON格式：{\"contract_type\": \"类型名称\", \"confidence\": 0.0-1.0, \"reason\": \"判断理由（不超过50字）\"}"
    )

    hint = ""
    if hint_type:
        hint = f"\n（关键词预筛选提示：可能是 {hint_type}，请验证）"

    user = (
        f"请判断以下合同属于哪种类型：\n\n"
        f"可选类型列表：\n{type_list}\n\n"
        f"合同内容：\n{contract_text[:8000]}\n{hint}\n\n"
        "请只输出JSON，不要添加其他说明。"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_note_generation_messages(
    contract_text: str,
    contract_type: str,
    template: str,
    my_party: str,
) -> List[Dict[str, str]]:
    """构建备注生成的prompt。

    Args:
        contract_text: 合同全文
        contract_type: 已识别的合同类型
        template: 该类型的备注模板
        my_party: 我方主体名称

    Returns:
        消息列表
    """
    system = (
        "你是一个专业的合同备注生成专家。请根据给定的模板格式，从合同中提取相关信息并生成合同备注。\n"
        "要求：\n"
        "1. 严格按照模板格式输出，保持模板的结构和序号\n"
        "2. 将模板中的{占位符}替换为从合同中提取的实际信息\n"
        "3. 无法从合同中找到的信息，替换为\"未在合同中明确\"\n"
        "4. 金额、日期、比例等数据必须准确提取，不可编造\n"
        "5. 只输出备注内容本身，不要添加额外说明或Markdown格式\n"
        "6. 保持简洁，避免冗余描述"
    )

    user = (
        f"我方主体：{my_party}\n"
        f"合同类型：{contract_type}\n\n"
        f"备注模板：\n{template}\n\n"
        f"合同全文：\n{contract_text}\n\n"
        "请根据模板格式生成合同备注，直接输出备注内容（不要用```包裹）："
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
