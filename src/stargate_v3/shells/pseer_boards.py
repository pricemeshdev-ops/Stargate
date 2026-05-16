"""PriceSEER analyst board branch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import palette


STARGATE_ROOT = Path(__file__).resolve().parents[3]
ORG_ROOT = STARGATE_ROOT.parent
PRICESEER_ROOT = ORG_ROOT / "PriceSEER"
VALUE_INDEX_PATH = PRICESEER_ROOT / "configs" / "DAY3_MAIN_VALUE_INDEX_V1.json"
BOARD_REGISTRY_PATH = PRICESEER_ROOT / "configs" / "DAY3_ANALYST_BOARD_REGISTRY_V1.json"
VALUE_REPORT_PATH = PRICESEER_ROOT / "docs" / "DAY3_MAIN_VALUE_INDEX_2026-05-14.md"
MAX_TUI_WIDTH = 184


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _short(value: Any, width: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= width else text[: width - 1] + "…"


def value_table(value_index: dict[str, Any]) -> Table:
    table = Table(box=box.ROUNDED, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT_PSEER}", expand=True)
    table.add_column("#", width=3, justify="right")
    table.add_column("Value Work", min_width=28, ratio=2, overflow="fold")
    table.add_column("Why It Matters", min_width=42, ratio=3, overflow="fold")
    table.add_column("Next Action", min_width=36, ratio=3, overflow="fold")
    for item in value_index.get("value_chain", []):
        table.add_row(
            str(item.get("rank", "")),
            Text(str(item.get("work", "")), style=palette.ACCENT_PSEER),
            Text(str(item.get("why_it_creates_value", "")), style=palette.TEXT),
            Text(str(item.get("next_action", "")), style=palette.MUTED),
        )
    return table


def board_table(registry: dict[str, Any]) -> Table:
    table = Table(box=box.ROUNDED, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT_EUCLID}", expand=True)
    table.add_column("#", width=3, justify="right")
    table.add_column("Board", min_width=28, ratio=2, overflow="fold")
    table.add_column("State", width=26, overflow="fold")
    table.add_column("Decision Use", min_width=44, ratio=3, overflow="fold")
    for board in registry.get("boards", []):
        table.add_row(
            str(board.get("priority", "")),
            Text(str(board.get("title", "")), style=palette.ACCENT_PSEER),
            Text(str(board.get("state", "")), style=palette.TEXT),
            Text(str(board.get("decision_use", "")), style=palette.MUTED),
        )
    return table


def command_table(registry: dict[str, Any]) -> Table:
    table = Table(box=box.SIMPLE_HEAVY, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT_MERCURY}", expand=True)
    table.add_column("#", width=3, justify="right")
    table.add_column("Board", min_width=28, ratio=2, overflow="fold")
    table.add_column("Command", min_width=64, ratio=4, overflow="fold")
    for board in registry.get("boards", []):
        table.add_row(
            str(board.get("priority", "")),
            Text(str(board.get("title", "")), style=palette.ACCENT_PSEER),
            Text(str(board.get("command", "")), style=palette.TEXT),
        )
    return table


def command_dock() -> Panel:
    return Panel(
        Text.assemble(
            ("Commands ", palette.DIM),
            ("v value  b boards  c commands  read report  r refresh  back  q", palette.TEXT),
            ("\nRule ", palette.DIM),
            ("every active board must name its decision use and next action", palette.ACCENT_WARN),
        ),
        title="Command Dock",
        border_style=palette.ACCENT_MERCURY,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def render(console: Console, *, view: str = "value") -> None:
    value_index = _load_json(VALUE_INDEX_PATH)
    registry = _load_json(BOARD_REGISTRY_PATH)
    current = value_index.get("current_state", {})
    header = Panel(
        Text.assemble(
            ("PRICESEER BOARD INDEX", f"bold {palette.ACCENT_PSEER}"),
            ("\nGoal ", palette.DIM),
            (str(value_index.get("goal", "unknown")), palette.TEXT),
            ("\nCore ", palette.DIM),
            (str(current.get("core_lane", "unknown")), palette.ACCENT_PSEER),
            (" | Default ", palette.DIM),
            (str(current.get("q1_default_target", "unknown")), palette.TEXT),
            (" | Research ", palette.DIM),
            (str(current.get("q1_research_target", "unknown")), palette.TEXT),
            ("\nBoundary read-only analyst control; no Betfair connection, orders, service control, or cash execution.", palette.ACCENT_FAIL),
        ),
        title="PriceSEER // Analyst Branch",
        border_style=palette.ACCENT_PSEER,
        box=box.HEAVY,
        padding=(0, 1),
    )
    if view == "commands":
        body = command_table(registry)
    elif view == "boards":
        body = board_table(registry)
    else:
        body = value_table(value_index)
    console.clear()
    console.print(Align.center(Group(header, body, command_dock()), width=min(console.size.width, MAX_TUI_WIDTH)))


def render_value_report(console: Console) -> None:
    body = Markdown(VALUE_REPORT_PATH.read_text(encoding="utf-8", errors="replace")) if VALUE_REPORT_PATH.exists() else Text(
        f"Missing value report: {VALUE_REPORT_PATH}",
        style=palette.ACCENT_FAIL,
    )
    console.clear()
    console.print(
        Align.center(
            Group(
                Panel(body, title="DAY3 Main Value Index", border_style=palette.ACCENT_PSEER, box=box.ROUNDED),
                command_dock(),
            ),
            width=min(console.size.width, MAX_TUI_WIDTH),
        )
    )


def loop(console: Console) -> None:
    view = "value"
    while True:
        render(console, view=view)
        try:
            command = console.input(f"[bold {palette.ACCENT_PSEER}]pseer-boards[/] > ").strip().lower()
        except EOFError:
            return
        if command in {"", "back", "q", "quit", "exit"}:
            return
        if command in {"r", "refresh"}:
            continue
        if command in {"v", "value", "main", "index"}:
            view = "value"
            continue
        if command in {"boards", "board"}:
            view = "boards"
            continue
        if command == "b":
            view = "boards"
            continue
        if command in {"c", "commands", "cmd"}:
            view = "commands"
            continue
        if command in {"read", "report", "detail"}:
            render_value_report(console)
            try:
                console.input(f"[bold {palette.ACCENT_PSEER}]pseer-boards[/] back > ")
            except EOFError:
                return
            continue


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description="STARGATE PriceSEER analyst board branch")


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    console = Console()
    loop(console)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
