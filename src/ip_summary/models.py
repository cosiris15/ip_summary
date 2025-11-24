from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

DirectionLiteral = Literal["upstream", "downstream"]


class LoadedDocument(BaseModel):
    path: Path
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClassificationResult(BaseModel):
    direction: DirectionLiteral
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    raw_response: str


class ExtractionResult(BaseModel):
    contract_path: Path
    direction: DirectionLiteral
    my_party: str
    fields: Dict[str, Any]
    raw_extraction: str | None = None
    classification: ClassificationResult
    prompt_version: str
    notes: Optional[str] = None


class HeaderDefinition(BaseModel):
    upstream_headers: List[str]
    downstream_headers: List[str]


class AggregatedResult(BaseModel):
    direction: DirectionLiteral
    rows: List[Dict[str, Any]]
