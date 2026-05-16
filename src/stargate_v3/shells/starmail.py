"""StarMail v3 governed local shell."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import palette
from ..starmail_store import DEFAULT_STORE_PATH, StarMailPacket, archive_packet, load_packets, seed_packets, write_packets

DRAFT_PACKETS: tuple[StarMailPacket, ...] = tuple(seed_packets(now="seed"))


def _display_age(updated_at: str) -> str:
    if not updated_at:
        return "missing"
    return updated_at.replace("T", " ").replace("Z", "")


def queue_table(packets: list[StarMailPacket]) -> Table:
    table = Table(box=box.ROUNDED, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT}", expand=True)
    table.add_column("ID", width=8)
    table.add_column("Owner", width=12)
    table.add_column("Priority", width=8)
    table.add_column("Status", width=12)
    table.add_column("Subject", min_width=36)
    table.add_column("Updated", width=22)
    for packet in packets:
        table.add_row(
            packet.packet_id,
            packet.target_owner,
            packet.priority,
            packet.status,
            packet.subject,
            _display_age(packet.updated_at),
        )
    return table


def empty_queue_panel(store_path: Path) -> Panel:
    message = Text.assemble(
        ("No StarMail packets loaded.", palette.TEXT),
        ("\nStore: ", palette.DIM),
        (str(store_path), palette.MUTED),
    )
    return Panel(message, title="Inbox / Queue", border_style=palette.FRAME, box=box.ROUNDED, padding=(0, 1))


def detail_table(packets: list[StarMailPacket]) -> Table:
    table = Table(box=box.SIMPLE_HEAVY, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT}", expand=True)
    table.add_column("ID", width=8)
    table.add_column("Mode", width=14)
    table.add_column("Evidence", width=28)
    table.add_column("Next Action")
    for packet in packets:
        table.add_row(packet.packet_id, packet.mode, packet.evidence_source, packet.action_requested)
    return table


def store_notice(store_path: Path) -> Panel:
    message = Text.assemble(
        ("Local file store. ", palette.TEXT),
        ("No wake service, no agent execution, no service restart, no live authority.", palette.ACCENT_WARN),
        ("  Store: ", palette.DIM),
        (str(store_path), palette.MUTED),
    )
    return Panel(message, title="Source", border_style=palette.FRAME, box=box.ROUNDED, padding=(0, 1))


def render(console: Console, *, store_path: Path = DEFAULT_STORE_PATH) -> None:
    packets = load_packets(store_path)
    commands = Panel(
        Text.assemble(
            ("Commands ", palette.DIM),
            ("back  q", palette.TEXT),
        ),
        title="Command Dock",
        border_style=palette.FRAME,
        box=box.ROUNDED,
        padding=(0, 1),
    )
    panel = Panel(
        Group(
            Text("STARMAIL", style=f"bold {palette.ACCENT}"),
            Text("Inbox / Queue", style=palette.MUTED),
            queue_table(packets) if packets else empty_queue_panel(store_path),
            detail_table(packets) if packets else Text(""),
            store_notice(store_path),
            commands,
        ),
        title="Gateway Mail",
        border_style=palette.ACCENT,
        box=box.HEAVY,
        padding=(0, 1),
    )
    console.clear()
    console.print(Align.center(panel, width=min(console.size.width, 184)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="STARGATE StarMail local shell")
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE_PATH, help="StarMail JSON store path")
    parser.add_argument("--seed", action="store_true", help="write seed packets to the local store")
    parser.add_argument("--list-json", action="store_true", help="print packet JSON and exit")
    parser.add_argument("--open", dest="open_id", help="print one packet as JSON")
    parser.add_argument("--archive", dest="archive_id", help="archive one packet in the local store")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.seed:
        write_packets(seed_packets(), args.store)
    if args.archive_id:
        archive_packet(args.archive_id, args.store)
    packets = load_packets(args.store)
    if args.list_json:
        print(json.dumps([asdict(packet) for packet in packets], indent=2, sort_keys=True))
        return 0
    if args.open_id:
        normalized = args.open_id.strip().upper()
        packet = next((item for item in packets if item.packet_id.upper() == normalized), None)
        if packet is None:
            raise SystemExit(f"unknown StarMail packet {args.open_id}")
        print(json.dumps(asdict(packet), indent=2, sort_keys=True))
        return 0
    console = Console()
    render(console, store_path=args.store)
    console.input(f"[bold {palette.ACCENT}]starmail-v3[/] back > ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
