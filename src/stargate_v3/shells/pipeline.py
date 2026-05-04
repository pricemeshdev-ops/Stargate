"""Pipeline v3 placeholder shell."""

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
    table.add_column("System", width=16)
    table.add_column("Phase", width=18)
    table.add_column("In", width=8, justify="right")
    table.add_column("Proc", width=8, justify="right")
    table.add_column("Pass", width=8, justify="right")
    table.add_column("Fault", width=8, justify="right")
    table.add_column("Fail", width=8, justify="right")
    table.add_column("Truth", width=14)
    for system, phase in (
        ("Animal", "live-shadow"),
        ("PriceSEER", "model"),
        ("PriceMESH", "truth"),
        ("StarMail", "diagnostics"),
    ):
        table.add_row(system, phase, "0", "0", "0", "0", "0", "SHELL")
    panel = Panel(
        Group(
            Text("PIPELINE v3", style=f"bold {palette.ACCENT}"),
            Text("Blank Epoch 3 board. Truth columns are template only.", style=palette.MUTED),
            table,
        ),
        title="Runtime Shell",
        border_style=palette.ACCENT,
        box=box.HEAVY,
        padding=(0, 1),
    )
    console.clear()
    console.print(Align.center(panel, width=min(console.size.width, 184)))


def main() -> int:
    console = Console()
    render(console)
    console.input(f"[bold {palette.ACCENT}]pipeline-v3[/] back > ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

