"""Blank STARGATE v3 gateway shell."""

from __future__ import annotations

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import palette
from .navigation import SURFACES, surface_by_key

CONSOLE = Console()


def header() -> Panel:
    return Panel(
        Group(
            Align.center(Text("STARGATE v3.0", style=f"bold {palette.ACCENT}")),
            Align.center(Text("Epoch 3 gateway boilerplate | live integrations disabled", style=palette.MUTED)),
        ),
        title="AA Stargate Launcher",
        subtitle="Mercury StarMail owner | Odin signoff | Euclid planning",
        border_style=palette.ACCENT,
        box=box.HEAVY,
        padding=(0, 1),
    )


def surface_table() -> Table:
    table = Table(
        box=box.ROUNDED,
        border_style=palette.FRAME,
        header_style=f"bold {palette.ACCENT}",
        row_styles=["", "on #111821"],
        expand=True,
    )
    table.add_column("Key", width=6)
    table.add_column("Section", min_width=18)
    table.add_column("Owner", width=12)
    table.add_column("Status", width=14)
    table.add_column("Purpose", min_width=48)
    for surface in SURFACES:
        status_style = palette.DIM if surface.status == "LOCKED" else palette.ACCENT_WARN
        table.add_row(
            Text(surface.key, style=f"bold {surface.accent}"),
            Text(surface.label, style=surface.accent),
            Text(surface.owner, style=palette.TEXT),
            Text(surface.status, style=status_style),
            Text(surface.summary, style=palette.MUTED),
        )
    return table


def command_dock() -> Panel:
    return Panel(
        Text.assemble(
            ("Open ", palette.DIM),
            ("a animal  ar reports  ps pseer  pm pmesh  b blog  x stareye  z starmail  p pipeline  e2 legacy", palette.TEXT),
            ("\nUtility ", palette.DIM),
            ("r refresh  q quit", palette.MUTED),
        ),
        title="Command Dock",
        border_style=palette.FRAME,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def placeholder(surface_key: str) -> Panel:
    surface = surface_by_key(surface_key)
    if surface is None:
        return Panel(Text(f"Unknown section: {surface_key}", style=palette.ACCENT_FAIL), border_style=palette.ACCENT_FAIL)
    return Panel(
        Group(
            Text(surface.label.upper(), style=f"bold {surface.accent}"),
            Text(surface.summary, style=palette.MUTED),
            Text(""),
            Text("Status: shell only. No live function wired.", style=palette.ACCENT_WARN),
            Text("Next: attach source contract, fixtures, tests, then runtime command.", style=palette.MUTED),
        ),
        title=f"{surface.label} // placeholder",
        border_style=surface.accent,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def render_home(notes: list[str] | None = None) -> None:
    notes = notes or []
    body = [header(), surface_table(), command_dock()]
    if notes:
        body.append(Panel("\n".join(notes[-4:]), title="Recent Action", border_style=palette.FRAME, box=box.ROUNDED))
    CONSOLE.clear()
    CONSOLE.print(Align.center(Group(*body), width=min(CONSOLE.size.width, 184)))


def main() -> int:
    notes: list[str] = []
    while True:
        render_home(notes)
        notes = []
        try:
            command = CONSOLE.input(f"[bold {palette.ACCENT}]stargate-v3[/] > ").strip().lower()
        except EOFError:
            return 0
        if command in {"q", "quit", "exit"}:
            return 0
        if command in {"", "r", "refresh"}:
            continue
        if command in {"x", "stareye"}:
            from .shells.stareye import render as render_stareye

            render_stareye(CONSOLE)
            CONSOLE.input(f"[bold {palette.ACCENT}]stargate-v3[/] back > ")
            continue
        if command in {"z", "mail", "starmail"}:
            from .shells.starmail import render as render_starmail

            render_starmail(CONSOLE)
            CONSOLE.input(f"[bold {palette.ACCENT}]stargate-v3[/] back > ")
            continue
        if command in {"p", "pipeline"}:
            from .shells.pipeline import render as render_pipeline

            render_pipeline(CONSOLE)
            CONSOLE.input(f"[bold {palette.ACCENT}]stargate-v3[/] back > ")
            continue
        surface = surface_by_key(command)
        if surface is None:
            notes.append(f"unknown command: {command}")
            continue
        CONSOLE.clear()
        CONSOLE.print(Align.center(Group(header(), placeholder(command), command_dock()), width=min(CONSOLE.size.width, 184)))
        CONSOLE.input(f"[bold {palette.ACCENT}]stargate-v3[/] back > ")


if __name__ == "__main__":
    raise SystemExit(main())

