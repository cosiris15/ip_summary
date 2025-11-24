from __future__ import annotations

from typing import Dict, List, Sequence

from .models import DirectionLiteral


PROMPT_VERSION = "v1.0"


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
        "Output MUST be raw JSON only (no Markdown, no code fences, no explanations)."
    )
    user = (
        f"我方主体：{my_party}\n"
        f"合同方向：{dir_cn}（direction={direction}）\n"
        "请按下方 JSON 模板填充值，键名不可改动，只替换 null 为提取结果（缺失则保留 null）。\n"
        f"{json_template}\n\n"
        f"合同全文：\n{contract_text}\n\n"
        "直接输出 JSON（不加```、不加额外文字）。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
