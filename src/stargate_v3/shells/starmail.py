"""StarMail v3 placeholder shell."""

from __future__ import annotations

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import palette


def render(console: Console) -> None:
    table = Table(box=box.ROUNDED, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT}", expand=True)
    table.add_column("Lane", width=14)
    table.add_column("Priority", width=10)
    table.add_column("State", width=14)
    table.add_column("Contract")
    table.add_row("Mercury", "WAKE", "SHELL", "Immediate current-path diagnostics only.")
    table.add_row("Odin", "QUEUE", "SHELL", "Supervisor aggregation and final signoff.")
    table.add_row("Euclid", "QUEUE", "SHELL", "Cycle and policy work.")
    table.add_row("Archive", "MONITOR", "SHELL", "Resolved, duplicate, stale, or historical mail.")
    panel = Panel(
        Group(
            Text("STARMAIL v3", style=f"bold {palette.ACCENT}"),
            Text("Blank mailbox and diagnostic routing shell. No service started.", style=palette.MUTED),
            table,
        ),
        title="Mercury Control Surface",
        border_style=palette.ACCENT,
        box=box.HEAVY,
        padding=(0, 1),
    )
    console.clear()
    console.print(Align.center(panel, width=min(console.size.width, 184)))


def main() -> int:
    console = Console()
    render(console)
    console.input(f"[bold {palette.ACCENT}]starmail-v3[/] back > ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

