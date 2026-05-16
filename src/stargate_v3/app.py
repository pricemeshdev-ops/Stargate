"""Blank STARGATE v3 gateway shell."""

from __future__ import annotations

import subprocess
from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import palette
from .identity import IDENTITY_MARK_NAME, PENTAGRAM_MARK, RUNTIME_FLOW, RUNTIME_FLOW_INTERPRETATION, TOPOLOGY_STAGES
from .navigation import SURFACES, surface_by_key

CONSOLE = Console()
REPO_ROOT = Path(__file__).resolve().parents[2]
ORG_ROOT = REPO_ROOT.parent
ANIMAL_ROOT = ORG_ROOT / "PriceLIVE" / "Animal"


def header() -> Panel:
    mark = "\n".join(PENTAGRAM_MARK)
    return Panel(
        Group(
            Align.center(Text(mark, style=f"bold {palette.ACCENT_PORTAL}")),
            Align.center(Text("STARGATE v3.0", style=f"bold {palette.ACCENT_PORTAL}")),
            Align.center(Text("Epoch 3 Gateway", style=palette.MUTED)),
        ),
        title="AA Stargate",
        subtitle="Gateway",
        border_style=palette.ACCENT_PORTAL,
        box=box.HEAVY,
        padding=(0, 1),
    )


def topology_card(stage_key: str, *, width: int) -> Panel:
    stage = next(item for item in TOPOLOGY_STAGES if item.key == stage_key)
    open_keys = {
        "live": "a",
        "mesh": "pm",
        "seer": "ps",
        "org": "lu",
    }
    body = Table.grid(padding=(0, 1))
    body.add_column(ratio=1)
    body.add_row(Text(stage.contract, style=palette.MUTED))
    body.add_row(Text.assemble(("owner ", palette.DIM), (stage.owner, palette.TEXT)))
    body.add_row(Text.assemble(("open ", palette.DIM), (open_keys[stage.key], stage.accent)))
    return Panel(
        body,
        title=stage.label,
        title_align="left",
        subtitle=f"[{stage.key}]",
        subtitle_align="right",
        border_style=stage.accent,
        box=box.SIMPLE_HEAVY,
        width=width,
        padding=(1, 1),
    )


def gateway_card(*, width: int) -> Panel:
    body = Table.grid(padding=(0, 1))
    body.add_column(ratio=1)
    body.add_row(Text("STARGATE", style=palette.MUTED))
    body.add_row(Text.assemble(("owner ", palette.DIM), ("MERCURY", palette.TEXT)))
    body.add_row(Text.assemble(("open ", palette.DIM), ("x stareye  z starmail  p pipeline", palette.ACCENT_MERCURY)))
    return Panel(
        body,
        title="GATEWAY",
        title_align="left",
        subtitle="[me] mercury",
        subtitle_align="right",
        border_style=palette.ACCENT_MERCURY,
        box=box.SIMPLE_HEAVY,
        width=width,
        padding=(1, 1),
    )


def portal_grid() -> Table:
    card_width = max(42, min(CONSOLE.size.width, 184) // 2 - 6)
    grid = Table.grid(expand=False, padding=(1, 2))
    grid.add_column(width=card_width)
    grid.add_column(width=card_width)
    grid.add_row(topology_card("live", width=card_width), topology_card("mesh", width=card_width))
    grid.add_row(topology_card("seer", width=card_width), topology_card("org", width=card_width))
    grid.add_row(gateway_card(width=card_width), surface_summary_card(width=card_width))
    return grid


def surface_summary_card(*, width: int) -> Panel:
    body = Table.grid(padding=(0, 1))
    body.add_column(ratio=1)
    body.add_row(Text("Portal", style=palette.MUTED))
    body.add_row(Text.assemble(("open ", palette.DIM), ("a animal node  as server  at trade  ar animal reports", palette.TEXT)))
    body.add_row(Text.assemble(("pseer ", palette.DIM), ("pb pseer boards  ps pseer reports  pr archive  vb venue buckets  br bucket review  tf trace forensics", palette.ACCENT_PSEER)))
    body.add_row(Text.assemble(("other ", palette.DIM), ("pm pmesh  b blog  e2 legacy", palette.MUTED)))
    return Panel(
        body,
        title="SURFACES",
        title_align="left",
        subtitle="[a/ar/ps/pm/b/e2]",
        subtitle_align="right",
        border_style=palette.FRAME,
        box=box.SIMPLE_HEAVY,
        width=width,
        padding=(1, 1),
    )


def surface_table() -> Table:
    table = Table(
        box=box.ROUNDED,
        border_style=palette.FRAME,
        header_style=f"bold {palette.ACCENT_PORTAL}",
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
            ("Navigate ", palette.DIM),
            ("live  mesh  seer  org  me gateway", palette.TEXT),
            ("\nOpen ", palette.DIM),
            ("a animal node  as animal server console  at animal trade terminal  ar animal reports", palette.TEXT),
            ("\nReports ", palette.DIM),
            ("pb pseer boards  ps pseer reports  pr archive  vb venue buckets  br bucket review  tf trace forensics", palette.ACCENT_PSEER),
            ("\nUtility ", palette.DIM),
            ("x stareye  z starmail  p pipeline  r refresh  q quit", palette.MUTED),
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
        ),
        title=f"{surface.label} // placeholder",
        border_style=surface.accent,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def animal_node_panel(notes: list[str] | None = None) -> Panel:
    notes = notes or []
    table = Table.grid(padding=(0, 1))
    table.add_column(ratio=1)
    table.add_row(Text("ANIMAL NODE", style=f"bold {palette.ACCENT_ANIMAL}"))
    table.add_row(Text("Owner: ANUBIS / PriceLIVE. Shell owner: MERCURY / STARGATE.", style=palette.MUTED))
    table.add_row(Text("Execution authority: NONE in this gateway. Commands are explicit operator launchers.", style=palette.ACCENT_WARN))
    table.add_row("")
    table.add_row(Text.assemble(("as", "bold cyan"), ("  open Animal Azure telemetry tunnel console", palette.TEXT)))
    table.add_row(Text.assemble(("at", "bold cyan"), ("  open Animal trade terminal, read-only SSE telemetry", palette.TEXT)))
    table.add_row(Text.assemble(("ar", "bold cyan"), ("  open Animal report archive", palette.TEXT)))
    table.add_row("")
    table.add_row(Text("Order placement, Betfair login, secret inspection, and VM service control are blocked here.", style=palette.ACCENT_FAIL))
    if notes:
        table.add_row("")
        for note in notes[-3:]:
            table.add_row(Text(note, style=palette.MUTED))
    return Panel(
        table,
        title="Animal Node // explicit consoles",
        border_style=palette.ACCENT_ANIMAL,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def open_animal_tunnel_console() -> str:
    script = ANIMAL_ROOT / "scripts" / "open_animal_azure_tunnel_console.sh"
    if not script.exists():
        return f"missing Animal server console launcher: {script}"
    subprocess.Popen([str(script)], cwd=ANIMAL_ROOT)
    return "opened Animal Azure telemetry tunnel console"


def open_animal_trade_terminal() -> str:
    script = ANIMAL_ROOT / "scripts" / "open_animal_gateway.sh"
    if not script.exists():
        return f"missing Animal trade terminal launcher: {script}"
    subprocess.Popen([str(script)], cwd=ANIMAL_ROOT)
    return "opened Animal trade terminal"


def render_animal_node(notes: list[str] | None = None) -> None:
    CONSOLE.clear()
    CONSOLE.print(Align.center(Group(header(), animal_node_panel(notes), command_dock()), width=min(CONSOLE.size.width, 184)))


def animal_node_loop() -> None:
    notes: list[str] = []
    while True:
        render_animal_node(notes)
        notes = []
        try:
            command = CONSOLE.input(f"[bold {palette.ACCENT_ANIMAL}]animal-node[/] > ").strip().lower()
        except EOFError:
            return
        if command in {"", "b", "back", "q", "quit", "exit"}:
            return
        if command in {"as", "server", "tunnel"}:
            notes.append(open_animal_tunnel_console())
            continue
        if command in {"at", "trade", "terminal"}:
            notes.append(open_animal_trade_terminal())
            continue
        if command in {"ar", "reports"}:
            from .shells.reports import loop as report_loop

            report_loop(CONSOLE, node_key="animal")
            continue
        notes.append(f"unknown Animal node command: {command}")


def render_home(notes: list[str] | None = None) -> None:
    notes = notes or []
    body = [header(), portal_grid(), command_dock()]
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
        topology_aliases = {"live": "an", "mesh": "sa", "seer": "od", "org": "lu", "gateway": "me"}
        if command in topology_aliases:
            command = topology_aliases[command]
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
        if command in {"a", "animal"}:
            animal_node_loop()
            continue
        if command in {"as", "animal-server", "server"}:
            notes.append(open_animal_tunnel_console())
            continue
        if command in {"at", "animal-terminal", "trade"}:
            notes.append(open_animal_trade_terminal())
            continue
        if command in {"pb", "pseer-boards", "boards", "pseer-board", "analyst-boards"}:
            from .shells.pseer_boards import loop as pseer_boards_loop

            pseer_boards_loop(CONSOLE)
            continue
        if command in {"ps", "pseer", "pseer-reports", "price-seer", "pr", "report-archive"}:
            from .shells.reports import loop as report_loop

            report_loop(CONSOLE, node_key="pseer")
            continue
        if command in {"vb", "venue", "venues", "venue-buckets", "pseer-venues"}:
            from .shells.venue_buckets import loop as venue_bucket_loop

            venue_bucket_loop(CONSOLE)
            continue
        if command in {"br", "bucket-review", "trade-review", "pseer-trades"}:
            from .shells.bucket_review import loop as bucket_review_loop

            bucket_review_loop(CONSOLE)
            continue
        if command in {"tf", "trace-forensics", "pseer-trace"}:
            from .shells.bucket_review import loop as bucket_review_loop

            bucket_review_loop(CONSOLE)
            continue
        if command in {"ar", "animal-reports"}:
            from .shells.reports import loop as report_loop

            report_loop(CONSOLE, node_key="animal")
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
