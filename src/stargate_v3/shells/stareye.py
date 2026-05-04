"""StarEye v3 placeholder shell."""

from __future__ import annotations

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import palette


def book_table() -> Table:
    table = Table(box=box.ROUNDED, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT}", expand=True)
    table.add_column("Runner", min_width=24)
    table.add_column("LTP", width=8, justify="right")
    table.add_column("Back", width=14, justify="right")
    table.add_column("Lay", width=14, justify="right")
    table.add_column("Spread", width=8, justify="right")
    table.add_column("Vol Delta", width=12, justify="right")
    table.add_column("State", width=14)
    table.add_row("> Fav/Target", Text("n/a", style=palette.MUTED), Text("cyan", style=palette.BACK), Text("pink", style=palette.LAY), "n/a", "n/a", "SHELL")
    table.add_row("Runner 2", "n/a", "n/a", "n/a", "n/a", "n/a", "SHELL")
    table.add_row("Runner 3", "n/a", "n/a", "n/a", "n/a", "n/a", "SHELL")
    return table


def render(console: Console) -> None:
    header = Panel(
        Text("Market n/a | Venue n/a | Frame 0/0 | paused | DEPTH n/a | Runner n/a", style=palette.TEXT),
        title="Market Replay",
        border_style=palette.FRAME,
        box=box.ROUNDED,
    )
    ladder = Panel(
        Text("Selected ladder placeholder | back/lay/traded depth template", style=palette.MUTED),
        title="Selected Ladder",
        border_style=palette.FRAME,
        box=box.ROUNDED,
    )
    event = Panel(
        Text("Event tape placeholder | fire/hold/SP/off events render here", style=palette.MUTED),
        title="Events",
        border_style=palette.FRAME,
        box=box.ROUNDED,
    )
    dock = Panel(
        Text("space play/pause | ,/. frame | [ ] runner | f fire | s final/SP | 1 book 2 ladder 3/e event console | q back", style=palette.MUTED),
        title="Command Dock",
        border_style=palette.FRAME,
        box=box.ROUNDED,
    )
    console.clear()
    console.print(Align.center(Group(Panel(Align.center(Text("STARGATE STAREYE v3", style=f"bold {palette.ACCENT}")), border_style=palette.ACCENT, box=box.HEAVY), header, book_table(), ladder, event, dock), width=min(console.size.width, 184)))


def main() -> int:
    console = Console()
    render(console)
    console.input(f"[bold {palette.ACCENT}]stareye-v3[/] back > ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

