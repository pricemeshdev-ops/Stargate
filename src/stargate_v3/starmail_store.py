"""Local file-backed StarMail packet store.

This is not a wake service and not an execution router. It is a small
local backend for governed StarMail packets under STARGATE.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE_PATH = REPO_ROOT / "runtime" / "starmail" / "packets.json"

VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_STATUSES = {"OPEN", "QUEUED", "IN_PROGRESS", "MONITOR", "ARCHIVED", "BLOCKED"}


@dataclass(frozen=True)
class StarMailPacket:
    packet_id: str
    source_system: str
    target_owner: str
    priority: str
    status: str
    mode: str
    subject: str
    created_at: str
    updated_at: str
    action_requested: str
    latest_disposition: str
    repo: str = "Cross-Org"
    fault_code: str = "NONE"
    current_path: bool = False
    evidence_source: str = "NONE"
    execution_authority: str = "NONE"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StarMailPacket":
        return cls(
            packet_id=str(data["packet_id"]),
            source_system=str(data.get("source_system", "STARGATE")),
            target_owner=str(data["target_owner"]),
            priority=str(data.get("priority", "P2")),
            status=str(data.get("status", "OPEN")),
            mode=str(data.get("mode", "read-only")),
            subject=str(data["subject"]),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            action_requested=str(data.get("action_requested", "")),
            latest_disposition=str(data.get("latest_disposition", "")),
            repo=str(data.get("repo", "Cross-Org")),
            fault_code=str(data.get("fault_code", "NONE")),
            current_path=bool(data.get("current_path", False)),
            evidence_source=str(data.get("evidence_source", "NONE")),
            execution_authority=str(data.get("execution_authority", "NONE")),
        )

    def validate(self) -> None:
        if not self.packet_id.strip():
            raise ValueError("packet_id is required")
        if not self.target_owner.strip():
            raise ValueError(f"{self.packet_id}: target_owner is required")
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"{self.packet_id}: invalid priority {self.priority}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"{self.packet_id}: invalid status {self.status}")
        if not self.subject.strip():
            raise ValueError(f"{self.packet_id}: subject is required")
        if self.execution_authority.upper() not in {"NONE", "READ_ONLY", "DRY_RUN"}:
            raise ValueError(f"{self.packet_id}: StarMail cannot grant execution authority")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def seed_packets(now: str | None = None) -> list[StarMailPacket]:
    timestamp = now or utc_now()
    return [
        StarMailPacket(
            packet_id="M-001",
            source_system="STARGATE",
            target_owner="MERCURY",
            priority="P0",
            status="IN_PROGRESS",
            mode="read-only",
            subject="Build STARGATE v3 gateway portal",
            created_at=timestamp,
            updated_at=timestamp,
            action_requested="Keep portal shell clean",
            latest_disposition="Local StarMail backend attached",
            repo="STARGATE",
            evidence_source="runtime/starmail/packets.json",
        ),
        StarMailPacket(
            packet_id="L-001",
            source_system="LUCY",
            target_owner="LUCY",
            priority="P0",
            status="OPEN",
            mode="read-only",
            subject="Supervise Epoch 3 gateway milestone",
            created_at=timestamp,
            updated_at=timestamp,
            action_requested="Hold boundaries",
            latest_disposition="Awaiting operator direction",
            repo="agent-org",
            evidence_source="agent-org/CURRENT_CONTEXT.md",
        ),
        StarMailPacket(
            packet_id="A-001",
            source_system="LUCY",
            target_owner="ANUBIS",
            priority="P1",
            status="QUEUED",
            mode="read-only",
            subject="Define Animal surface contract",
            created_at=timestamp,
            updated_at=timestamp,
            action_requested="Await lane brief",
            latest_disposition="No execution authority",
            repo="Animal",
            evidence_source="NONE",
        ),
    ]


def serialize_packets(packets: list[StarMailPacket]) -> dict[str, Any]:
    for packet in packets:
        packet.validate()
    return {
        "schema_version": 1,
        "store_authority": "Mercury/STARGATE local file store",
        "execution_authority": "NONE",
        "packets": [asdict(packet) for packet in packets],
    }


def write_packets(packets: list[StarMailPacket], path: Path = DEFAULT_STORE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serialize_packets(packets), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_packets(path: Path = DEFAULT_STORE_PATH) -> list[StarMailPacket]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    packets = [StarMailPacket.from_dict(item) for item in data.get("packets", [])]
    for packet in packets:
        packet.validate()
    return packets


def load_or_seed_packets(path: Path = DEFAULT_STORE_PATH) -> list[StarMailPacket]:
    packets = load_packets(path)
    if packets:
        return packets
    packets = seed_packets()
    write_packets(packets, path)
    return packets


def find_packet(packet_id: str, path: Path = DEFAULT_STORE_PATH) -> StarMailPacket | None:
    normalized = packet_id.strip().upper()
    return next((packet for packet in load_packets(path) if packet.packet_id.upper() == normalized), None)


def archive_packet(packet_id: str, path: Path = DEFAULT_STORE_PATH) -> StarMailPacket:
    packets = load_packets(path)
    normalized = packet_id.strip().upper()
    updated: list[StarMailPacket] = []
    archived: StarMailPacket | None = None
    for packet in packets:
        if packet.packet_id.upper() == normalized:
            archived = StarMailPacket(
                **{
                    **asdict(packet),
                    "status": "ARCHIVED",
                    "updated_at": utc_now(),
                    "latest_disposition": "Archived locally by Mercury/STARGATE shell",
                }
            )
            updated.append(archived)
        else:
            updated.append(packet)
    if archived is None:
        raise KeyError(f"unknown StarMail packet {packet_id}")
    write_packets(updated, path)
    return archived
