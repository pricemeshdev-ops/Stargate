"""Read-only report archive index for STARGATE recall surfaces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_ARCHIVE_PATH = REPO_ROOT / "runtime" / "reports" / "index.json"

REQUIRED_STATE_MEMORY_PRIMITIVES: tuple[str, ...] = (
    "30s/60s/120s price velocity",
    "volume acceleration",
    "multi-frame order-book imbalance trend",
    "cross-runner pressure",
    "market-level favourite compression",
    "late reversal shape",
    "SP projection drift over time",
)


@dataclass(frozen=True)
class ReportRecord:
    report_id: str
    title: str
    node: str
    author: str
    owner: str
    status: str
    created_at: str
    source_path: str
    summary: str
    authority: str
    boundary: str
    tags: tuple[str, ...]
    required_state_memory: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReportRecord":
        return cls(
            report_id=str(data["id"]),
            title=str(data["title"]),
            node=str(data["node"]),
            author=str(data["author"]),
            owner=str(data["owner"]),
            status=str(data["status"]),
            created_at=str(data["created_at"]),
            source_path=str(data["source_path"]),
            summary=str(data["summary"]),
            authority=str(data["authority"]),
            boundary=str(data["boundary"]),
            tags=tuple(str(item) for item in data.get("tags", [])),
            required_state_memory=tuple(str(item) for item in data.get("required_state_memory", [])),
        )


@dataclass(frozen=True)
class NodeArchive:
    key: str
    label: str
    owner: str
    reports: tuple[ReportRecord, ...]

    @classmethod
    def from_dict(cls, key: str, data: dict[str, Any]) -> "NodeArchive":
        return cls(
            key=key,
            label=str(data["label"]),
            owner=str(data["owner"]),
            reports=tuple(ReportRecord.from_dict(item) for item in data.get("reports", [])),
        )


@dataclass(frozen=True)
class ReportArchive:
    schema: str
    updated_at: str
    nodes: dict[str, NodeArchive]


def load_report_archive(path: Path = DEFAULT_REPORT_ARCHIVE_PATH) -> ReportArchive:
    if not path.exists():
        return ReportArchive(schema="stargate.report_archive.v1", updated_at="missing", nodes={})
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = {key: NodeArchive.from_dict(key, value) for key, value in data.get("nodes", {}).items()}
    return ReportArchive(schema=str(data["schema"]), updated_at=str(data["updated_at"]), nodes=nodes)


def reports_for_node(node_key: str, path: Path = DEFAULT_REPORT_ARCHIVE_PATH) -> tuple[ReportRecord, ...]:
    archive = load_report_archive(path)
    node = archive.nodes.get(node_key.strip().lower())
    if node is None:
        return ()
    return node.reports
