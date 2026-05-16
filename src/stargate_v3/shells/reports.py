"""STARGATE report archive shell."""

from __future__ import annotations

import argparse
from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import palette
from ..report_archive import DEFAULT_REPORT_ARCHIVE_PATH, REQUIRED_STATE_MEMORY_PRIMITIVES, ReportArchive, load_report_archive


MAX_TUI_WIDTH = 184


def _node_or_empty(archive: ReportArchive, node_key: str):
    return archive.nodes.get(node_key.strip().lower())


def _status_style(status: str) -> str:
    token = status.upper()
    if any(item in token for item in ("FAIL", "REJECT", "BLOCK", "MISSING")):
        return palette.ACCENT_FAIL
    if any(item in token for item in ("BUILT", "ACTIVE", "PROMOTED", "REPLAY", "TRACE", "AUDIT")):
        return palette.GOOD
    if any(item in token for item in ("APPROX", "PROBE", "CHECKLIST", "WORKING", "BRIEF")):
        return palette.ACCENT_WARN
    return palette.TEXT


def _short_path(source_path: str) -> str:
    path = Path(source_path)
    parts = path.parts
    if "AA-SG-LAUNCHER" in parts:
        index = parts.index("AA-SG-LAUNCHER")
        return "/".join(parts[index + 1 :])
    if len(parts) > 3:
        return "/".join(parts[-3:])
    return str(path)


def report_table(archive: ReportArchive, node_key: str) -> Table | Text:
    node = _node_or_empty(archive, node_key)
    if node is None or not node.reports:
        return Text("No reports archived for this node yet.", style=palette.MUTED)

    table = Table(box=box.ROUNDED, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT_PSEER}", expand=True)
    table.add_column("#", width=3, justify="right")
    table.add_column("Report", min_width=34, ratio=4)
    table.add_column("Author", width=14)
    table.add_column("Status", width=20)
    table.add_column("Source Link", min_width=38, ratio=3)
    for index, report in enumerate(node.reports, start=1):
        table.add_row(
            str(index),
            Text(report.title, style=palette.TEXT),
            Text(report.author, style=palette.ACCENT_EUCLID if report.author.upper() == "EUCLID" else palette.TEXT),
            Text(report.status, style=_status_style(report.status)),
            Text(_short_path(report.source_path), style=palette.MUTED),
        )
    return table


def report_detail_table(archive: ReportArchive, node_key: str) -> Table | Text:
    node = _node_or_empty(archive, node_key)
    if node is None or not node.reports:
        return Text("")

    table = Table(box=box.SIMPLE_HEAVY, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT_PSEER}", expand=True)
    table.add_column("ID", width=22)
    table.add_column("Authority", min_width=26, ratio=2)
    table.add_column("Boundary", min_width=42, ratio=3)
    table.add_column("Tags", min_width=26, ratio=2)
    for report in node.reports:
        table.add_row(report.report_id, report.authority, report.boundary, ", ".join(report.tags))
    return table


def state_memory_panel() -> Panel:
    body = Table.grid(padding=(0, 1))
    body.add_column(ratio=1)
    for item in REQUIRED_STATE_MEMORY_PRIMITIVES:
        body.add_row(Text.assemble(("• ", palette.ACCENT_PSEER), (item, palette.TEXT)))
    return Panel(
        body,
        title="Epoch 3 State Memory Primitives",
        border_style=palette.ACCENT_EUCLID,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def source_notice(path: Path, archive: ReportArchive) -> Panel:
    return Panel(
        Text.assemble(
            ("Archive index ", palette.DIM),
            (str(path), palette.MUTED),
            (" | updated ", palette.DIM),
            (archive.updated_at, palette.TEXT),
            ("\nSTARGATE is the recall shell only. Canonical reports stay in their source repos.", palette.ACCENT_WARN),
            ("\nBlocked: orders, Betfair login, secret inspection, service control, runtime mutation.", palette.ACCENT_FAIL),
        ),
        title="Source / Boundary",
        border_style=palette.FRAME,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def command_dock(*, context: str = "archive") -> Panel:
    if context == "report":
        command_text = "# open another report  enter/back return  q quit"
    else:
        command_text = "# open report  r refresh  back  q"
    return Panel(
        Text.assemble(("Commands ", palette.DIM), (command_text, palette.TEXT)),
        title="Command Dock",
        border_style=palette.ACCENT_MERCURY,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def render(console: Console, *, node_key: str = "pseer", archive_path: Path = DEFAULT_REPORT_ARCHIVE_PATH) -> None:
    archive = load_report_archive(archive_path)
    node = _node_or_empty(archive, node_key)
    label = node.label if node is not None else f"{node_key.upper()} Reports"
    owner = node.owner if node is not None else "unknown"
    report_count = len(node.reports) if node is not None else 0
    panel = Panel(
        Group(
            Text(label.upper(), style=f"bold {palette.ACCENT_PSEER}"),
            Text.assemble(
                ("owner ", palette.DIM),
                (owner, palette.TEXT),
                (" | state read-only report recall", palette.MUTED),
                (" | reports ", palette.DIM),
                (str(report_count), palette.TEXT),
            ),
            report_table(archive, node_key),
            report_detail_table(archive, node_key),
            state_memory_panel() if node_key.strip().lower() == "pseer" else Text(""),
            source_notice(archive_path, archive),
            command_dock(),
        ),
        title=f"{label} // Archive",
        border_style=palette.ACCENT_MERCURY if node_key.strip().lower() == "pseer" else palette.FRAME,
        box=box.HEAVY,
        padding=(0, 1),
    )
    console.clear()
    console.print(Align.center(panel, width=min(console.size.width, MAX_TUI_WIDTH)))


def render_report(console: Console, report_index: int, *, node_key: str = "pseer", archive_path: Path = DEFAULT_REPORT_ARCHIVE_PATH) -> None:
    archive = load_report_archive(archive_path)
    node = _node_or_empty(archive, node_key)
    if node is None or report_index < 1 or report_index > len(node.reports):
        console.clear()
        console.print(Panel(Text(f"No report #{report_index} for {node_key}.", style=palette.ACCENT_FAIL)))
        return

    report = node.reports[report_index - 1]
    source_path = Path(report.source_path)
    if source_path.exists():
        body = Markdown(source_path.read_text(encoding="utf-8", errors="replace"))
    else:
        body = Text(f"Missing report source: {source_path}", style=palette.ACCENT_FAIL)

    meta = Panel(
        Text.assemble(
            ("Report ", palette.DIM),
            (f"#{report_index} ", palette.ACCENT_PSEER),
            (report.title, palette.TEXT),
            ("\nStatus ", palette.DIM),
            (report.status, _status_style(report.status)),
            (" | Owner ", palette.DIM),
            (report.owner, palette.TEXT),
            ("\nSource ", palette.DIM),
            (str(source_path), palette.MUTED),
            ("\nAuthority ", palette.DIM),
            (report.authority, palette.TEXT),
            ("\nBoundary ", palette.DIM),
            (report.boundary, palette.ACCENT_WARN),
        ),
        title="Report Source",
        border_style=palette.ACCENT_MERCURY,
        box=box.ROUNDED,
        padding=(0, 1),
    )
    body_panel = Panel(
        body,
        title="Report Body",
        border_style=palette.FRAME,
        box=box.ROUNDED,
        padding=(0, 1),
    )
    console.clear()
    console.print(Align.center(Group(meta, body_panel, command_dock(context="report")), width=min(console.size.width, MAX_TUI_WIDTH)))


def loop(console: Console, *, node_key: str = "pseer", archive_path: Path = DEFAULT_REPORT_ARCHIVE_PATH) -> None:
    while True:
        render(console, node_key=node_key, archive_path=archive_path)
        try:
            command = console.input(f"[bold {palette.ACCENT}]reports-v3[/] > ").strip().lower()
        except EOFError:
            return
        if command in {"", "b", "back", "q", "quit", "exit"}:
            return
        if command in {"r", "refresh", "reload"}:
            continue
        if command.isdigit():
            report_index = int(command)
            archive = load_report_archive(archive_path)
            node = _node_or_empty(archive, node_key)
            report = node.reports[report_index - 1] if node is not None and 1 <= report_index <= len(node.reports) else None
            if report is not None and "venue-bucket-pager" in report.tags:
                from .venue_buckets import loop as venue_bucket_loop

                venue_bucket_loop(console)
                continue
            render_report(console, report_index, node_key=node_key, archive_path=archive_path)
            try:
                console.input(f"[bold {palette.ACCENT}]reports-v3[/] back > ")
            except EOFError:
                return
            continue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="STARGATE report archive shell")
    parser.add_argument("--node", default="pseer", help="report node key, e.g. pseer, animal, pricemesh, stargate, agent-org")
    parser.add_argument("--archive", type=Path, default=DEFAULT_REPORT_ARCHIVE_PATH, help="report archive JSON index")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console()
    loop(console, node_key=args.node, archive_path=args.archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
