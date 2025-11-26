from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional

from tqdm.asyncio import tqdm_asyncio

from .config import Settings
from .document_loader import load_document, scan_documents
from .llm_client import LLMClient
from .models import (
    ClassificationResult,
    DirectionLiteral,
    ExtractionResult,
    HeaderDefinition,
    LoadedDocument,
)
from .prompts import (
    PROMPT_VERSION,
    build_classification_messages,
    build_extraction_messages,
    build_type_classification_messages,
    build_note_generation_messages,
)
from .contract_types import (
    ContractType,
    load_contract_types,
    identify_contract_type_by_keywords,
    get_type_names_for_prompt,
)
from .storage import (
    aggregate_results,
    append_history,
    ensure_directories,
    load_header_columns,
    save_intermediate,
    write_tabular_outputs,
)


def load_headers(upstream_path: Path, downstream_path: Path) -> HeaderDefinition:
    return HeaderDefinition(
        upstream_headers=load_header_columns(upstream_path),
        downstream_headers=load_header_columns(downstream_path),
    )


NOTE_TEMPLATES_PATH = Path(__file__).parent.parent.parent / "config" / "contract_note_templates.yaml"


async def process_contracts(
    settings: Settings,
    my_party: str,
    upstream_header_path: Path,
    downstream_header_path: Path,
    force_direction: Optional[DirectionLiteral] = None,
    note_templates_path: Optional[Path] = None,
) -> List[ExtractionResult]:
    headers = load_headers(upstream_header_path, downstream_header_path)
    ensure_directories(
        settings.pipeline.intermediate_dir,
        settings.pipeline.intermediate_dir / "upstream",
        settings.pipeline.intermediate_dir / "downstream",
    )

    # Load contract type templates for note generation
    templates_path = note_templates_path or NOTE_TEMPLATES_PATH
    contract_types = {}
    if templates_path.exists():
        contract_types = load_contract_types(templates_path)

    paths = scan_documents(settings.pipeline.input_dir)
    documents = [load_document(p) for p in paths]
    client = LLMClient(settings.llm)
    semaphore = asyncio.Semaphore(settings.pipeline.concurrent_requests)

    async def _run(loaded: LoadedDocument) -> ExtractionResult:
        classification = await _classify(loaded.text, my_party, client, semaphore)
        direction = force_direction or classification.direction
        header_list = (
            headers.upstream_headers if direction == "upstream" else headers.downstream_headers
        )
        extraction, raw_extraction = await _extract(
            loaded.text, header_list, my_party, direction, client, semaphore
        )

        # Generate contract note based on type
        contract_note = None
        contract_type_name = None
        if contract_types:
            contract_type_name, contract_note = await _generate_contract_note(
                loaded.text, my_party, contract_types, client, semaphore
            )
            # Set the note in the extracted fields if "合同备注" is a field
            if "合同备注" in extraction:
                extraction["合同备注"] = contract_note

        result = ExtractionResult(
            contract_path=loaded.path,
            direction=direction,
            my_party=my_party,
            fields=extraction,
            raw_extraction=raw_extraction,
            classification=classification,
            prompt_version=PROMPT_VERSION,
            notes=f"合同类型：{contract_type_name}" if contract_type_name else None,
        )
        save_intermediate(result, settings.pipeline.intermediate_dir)
        return result

    tasks = [_run(doc) for doc in documents]
    results = await tqdm_asyncio.gather(*tasks)
    return results


async def _classify(
    contract_text: str,
    my_party: str,
    client: LLMClient,
    semaphore: asyncio.Semaphore,
) -> ClassificationResult:
    messages = build_classification_messages(contract_text, my_party)
    raw = await _call_llm(messages, client, semaphore)
    parsed = _safe_json(raw)
    direction = _normalize_direction(parsed.get("direction", "upstream"))
    confidence = float(parsed.get("confidence", 0))
    reason = str(parsed.get("reason", "")).strip()
    return ClassificationResult(
        direction=direction,
        confidence=max(0.0, min(confidence, 1.0)),
        reason=reason or "未提供说明",
        raw_response=raw,
    )


async def _extract(
    contract_text: str,
    headers: List[str],
    my_party: str,
    direction: DirectionLiteral,
    client: LLMClient,
    semaphore: asyncio.Semaphore,
) -> tuple[Dict[str, object], str]:
    messages = build_extraction_messages(contract_text, headers, my_party, direction)
    raw = await _call_llm(messages, client, semaphore)
    parsed = _safe_json(raw)
    # Ensure all headers exist even when the model omits them.
    fields = {h: parsed.get(h) if isinstance(parsed, dict) else None for h in headers}
    return fields, raw


async def _identify_contract_type(
    contract_text: str,
    contract_types: Dict[str, ContractType],
    client: LLMClient,
    semaphore: asyncio.Semaphore,
) -> str:
    """识别合同类型，返回最匹配的类型名称。"""
    # 先用关键词预筛选
    hint_type = identify_contract_type_by_keywords(contract_text, contract_types)

    # 生成类型列表说明
    type_list = get_type_names_for_prompt(contract_types)

    # 调用LLM进行类型识别
    messages = build_type_classification_messages(contract_text, type_list, hint_type)
    raw = await _call_llm(messages, client, semaphore)
    parsed = _safe_json(raw)

    contract_type = parsed.get("contract_type", "")
    # 验证返回的类型是否在定义中
    if contract_type and contract_type in contract_types:
        return contract_type

    # 如果LLM返回的类型不在列表中，使用关键词匹配结果或默认通用类型
    return hint_type or "通用类型"


async def _generate_contract_note(
    contract_text: str,
    my_party: str,
    contract_types: Dict[str, ContractType],
    client: LLMClient,
    semaphore: asyncio.Semaphore,
) -> tuple[str, str]:
    """生成合同备注。

    Returns:
        (合同类型名称, 生成的备注内容)
    """
    # 识别合同类型
    contract_type_name = await _identify_contract_type(
        contract_text, contract_types, client, semaphore
    )

    # 获取对应模板
    ct = contract_types.get(contract_type_name)
    if not ct:
        ct = contract_types.get("通用类型")
    if not ct:
        return contract_type_name, "无法生成备注：未找到对应模板"

    # 调用LLM生成备注
    messages = build_note_generation_messages(
        contract_text, contract_type_name, ct.template, my_party
    )
    note = await _call_llm(messages, client, semaphore)

    # 清理可能的Markdown格式
    note = note.strip()
    if note.startswith("```"):
        lines = note.split("\n")
        if len(lines) > 2:
            note = "\n".join(lines[1:-1])

    return contract_type_name, note


async def _call_llm(
    messages: List[Dict[str, str]],
    client: LLMClient,
    semaphore: asyncio.Semaphore,
) -> str:
    async with semaphore:
        return await client.chat(messages)


def _safe_json(payload: str) -> Dict[str, object]:
    cleaned = (payload or "").strip()
    if cleaned.startswith("```"):
        # Remove Markdown code fences if present.
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return {}


def _normalize_direction(value: str) -> DirectionLiteral:
    val = (value or "").strip().lower()
    if "上" in val or val == "upstream":
        return "upstream"
    if "下" in val or val == "downstream":
        return "downstream"
    # Default to upstream if unclear to reduce risk of missed license acquisition.
    return "upstream"


def aggregate_to_outputs(
    settings: Settings,
    headers: HeaderDefinition,
    direction: DirectionLiteral,
    basename: str,
) -> Dict[str, Path]:
    df = aggregate_results(
        settings.pipeline.intermediate_dir, headers.upstream_headers if direction == "upstream" else headers.downstream_headers, direction
    )
    outputs = write_tabular_outputs(df, settings.pipeline.final_dir, basename)
    history_file = settings.pipeline.history_dir / f"{direction}_history.csv"
    append_history(df, history_file)
    return outputs
