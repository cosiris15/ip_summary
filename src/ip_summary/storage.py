from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .models import DirectionLiteral, ExtractionResult
from .field_converter import FieldConverter


def load_header_columns(path: Path) -> List[str]:
    """
    Read header names from the provided Excel file.
    """
    df = pd.read_excel(path)
    return list(df.columns)


def ensure_directories(*paths: Path) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def save_intermediate(result: ExtractionResult, intermediate_dir: Path) -> Path:
    target_dir = intermediate_dir / result.direction
    ensure_directories(target_dir)
    output_path = target_dir / f"{result.contract_path.stem}.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            result.model_dump(mode="json"),
            f,
            ensure_ascii=False,
            indent=2,
        )
    return output_path


def load_intermediate_folder(
    folder: Path, direction: DirectionLiteral
) -> List[ExtractionResult]:
    files = sorted(folder.glob("*.json"))
    results: List[ExtractionResult] = []
    for path in files:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        results.append(ExtractionResult.model_validate(payload))
    return [r for r in results if r.direction == direction]


def aggregate_results(
    intermediate_dir: Path,
    headers: List[str],
    direction: DirectionLiteral,
) -> pd.DataFrame:
    """
    Load user-edited JSON files for the given direction and assemble into a DataFrame.
    """
    folder = intermediate_dir / direction
    results = load_intermediate_folder(folder, direction)
    rows: List[Dict[str, object]] = []
    for res in results:
        base = {
            "合同源文件": str(res.contract_path),
            "合同方向": direction,
            "LLM置信度": res.classification.confidence,
            "LLM判定理由": res.classification.reason,
        }
        fields = {h: res.fields.get(h) for h in headers}
        base.update(fields)
        rows.append(base)
    columns = ["合同源文件", "合同方向", "LLM置信度", "LLM判定理由"] + headers
    df = pd.DataFrame(rows, columns=columns)
    return df


def write_tabular_outputs(
    df: pd.DataFrame, output_dir: Path, basename: str
) -> Dict[str, Path]:
    ensure_directories(output_dir)
    csv_path = output_dir / f"{basename}.csv"
    excel_path = output_dir / f"{basename}.xlsx"
    df.to_csv(csv_path, index=False)
    df.to_excel(excel_path, index=False)
    return {"csv": csv_path, "excel": excel_path}


def append_history(df: pd.DataFrame, history_file: Path) -> None:
    ensure_directories(history_file.parent)
    if history_file.exists():
        existing = pd.read_csv(history_file)
        combined = pd.concat([existing, df], ignore_index=True)
    else:
        combined = df
    combined.to_csv(history_file, index=False)


def aggregate_results_for_database(
    intermediate_dir: Path,
    headers: List[str],
    direction: DirectionLiteral,
    converter: Optional[FieldConverter] = None,
) -> pd.DataFrame:
    """
    Load results and convert text values to codes for database import.

    Args:
        intermediate_dir: 中间结果目录
        headers: 表头字段列表
        direction: 合同方向
        converter: 字段转换器，如果为None则创建默认转换器

    Returns:
        转换后的DataFrame，文字值已替换为编号
    """
    if converter is None:
        converter = FieldConverter()

    folder = intermediate_dir / direction
    results = load_intermediate_folder(folder, direction)
    rows: List[Dict[str, object]] = []

    for res in results:
        base = {
            "合同源文件": str(res.contract_path),
            "合同方向": direction,
            "LLM置信度": res.classification.confidence,
            "LLM判定理由": res.classification.reason,
        }
        # 转换字段值为编号
        fields = {h: converter.convert(h, res.fields.get(h)) for h in headers}
        base.update(fields)
        rows.append(base)

    columns = ["合同源文件", "合同方向", "LLM置信度", "LLM判定理由"] + headers
    df = pd.DataFrame(rows, columns=columns)
    return df


def write_database_outputs(
    df: pd.DataFrame, output_dir: Path, basename: str
) -> Dict[str, Path]:
    """
    Write outputs formatted for database import (with codes instead of text).
    """
    ensure_directories(output_dir)
    csv_path = output_dir / f"{basename}_db.csv"
    excel_path = output_dir / f"{basename}_db.xlsx"
    df.to_csv(csv_path, index=False)
    df.to_excel(excel_path, index=False)
    return {"csv": csv_path, "excel": excel_path}
