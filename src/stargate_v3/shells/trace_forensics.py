"""SP3-style full trace forensics viewer for cached PriceSEER trade rows."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import palette

MAX_TUI_WIDTH = 320
STARGATE_ROOT = Path(__file__).resolve().parents[3]
ORG_ROOT = STARGATE_ROOT.parent
TRACE_SCRIPT = ORG_ROOT / "PriceSEER" / "scripts" / "show_trade_trace_forensics_azure.sh"
CACHE_DIR = STARGATE_ROOT / "runtime" / "cache" / "trade_trace_forensics"


@dataclass(frozen=True)
class ParsedTracePack:
    title: str
    boundary: str | None
    source_archive: str | None
    source_member: str | None
    raw_messages: int | None
    market_updates: int | None
    frame_interval_ms: int | None
    trade: dict[str, object]
    rows_total: int | None
    start: int | None
    end: int | None
    window: str | None
    max_frames: int | None
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    raw: str
    cached: bool = False
    cache_path: str | None = None


def _clean_azure_output(text: str) -> str:
    if "[stdout]" in text:
        text = text.split("[stdout]", 1)[1]
    if "[stderr]" in text:
        text = text.split("[stderr]", 1)[0]
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line.strip() and not line.startswith("Enable succeeded")).strip()


def _split_markdown_row(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _safe(value: object) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "").strip())
    return cleaned.strip("_")[:96] or "blank"


def _tui_width(console: Console) -> int:
    return max(120, min(console.size.width, MAX_TUI_WIDTH))


def parse_trace_pack(text: str, *, cached: bool = False, path: Path | None = None) -> ParsedTracePack:
    clean = _clean_azure_output(text)
    lines = clean.splitlines()
    title = lines[0].strip() if lines else "PSEER Trade Trace Forensics"
    boundary: str | None = None
    source_archive: str | None = None
    source_member: str | None = None
    raw_messages: int | None = None
    market_updates: int | None = None
    frame_interval_ms: int | None = None
    trade: dict[str, object] = {}
    rows_total: int | None = None
    start: int | None = None
    end: int | None = None
    window: str | None = None
    max_frames: int | None = None
    columns: tuple[str, ...] = ()
    rows: list[tuple[str, ...]] = []

    for line in lines:
        if line.startswith("boundary="):
            boundary = line.split("=", 1)[1].strip()
        elif line.startswith("source_archive="):
            source_archive = line.split("=", 1)[1].strip()
        elif line.startswith("source_member="):
            source_member = line.split("=", 1)[1].strip()
        elif line.startswith("raw_messages="):
            match = re.search(r"raw_messages=(\d+).*market_updates=(\d+).*frame_interval_ms=(\d+)", line)
            if match:
                raw_messages = int(match.group(1))
                market_updates = int(match.group(2))
                frame_interval_ms = int(match.group(3))
        elif line.startswith("trade="):
            try:
                parsed = json.loads(line.split("=", 1)[1])
                if isinstance(parsed, dict):
                    trade = parsed
            except json.JSONDecodeError:
                trade = {}
        elif line.startswith("rows_total="):
            match = re.search(r"rows_total=(\d+).*showing=(\d+)-(\d+).*window=([^|]+).*max_frames=(\d+)", line)
            if match:
                rows_total = int(match.group(1))
                start = int(match.group(2))
                end = int(match.group(3))
                window = match.group(4).strip()
                max_frames = int(match.group(5))

    for index, line in enumerate(lines):
        if line.startswith("| ") and " | " in line:
            maybe_cols = _split_markdown_row(line)
            if maybe_cols and maybe_cols[0] == "frame":
                columns = maybe_cols
                for row_line in lines[index + 2 :]:
                    if not row_line.startswith("| "):
                        break
                    row = _split_markdown_row(row_line)
                    if len(row) == len(columns):
                        rows.append(row)
                break

    return ParsedTracePack(
        title=title,
        boundary=boundary,
        source_archive=source_archive,
        source_member=source_member,
        raw_messages=raw_messages,
        market_updates=market_updates,
        frame_interval_ms=frame_interval_ms,
        trade=trade,
        rows_total=rows_total,
        start=start,
        end=end,
        window=window,
        max_frames=max_frames,
        columns=columns,
        rows=tuple(rows),
        raw=clean,
        cached=cached,
        cache_path=str(path) if path is not None else None,
    )


def _row_maps(pack: ParsedTracePack) -> list[dict[str, str]]:
    return [dict(zip(pack.columns, row, strict=False)) for row in pack.rows]


def trade_cache_path(row: dict[str, str]) -> Path:
    return CACHE_DIR / (
        f"{_safe(row.get('market_id'))}__{_safe(row.get('selection_id'))}"
        f"__{_safe(row.get('side'))}__{_safe(row.get('entry_ts'))}.txt"
    )


def _required_trade_arg(row: dict[str, str], key: str) -> str:
    value = (row.get(key) or "").strip()
    if not value:
        raise ValueError(f"trade row is missing {key}; refresh the bucket ledger with rf so trace-ready fields are cached")
    return value


def fetch_trace_pack(
    row: dict[str, str],
    *,
    force_remote: bool = False,
    seconds_before: int = 180,
    seconds_after: int = 390,
    max_frames: int = 240,
) -> ParsedTracePack:
    if not TRACE_SCRIPT.exists():
        raise FileNotFoundError(f"missing trace script: {TRACE_SCRIPT}")
    path = trade_cache_path(row)
    if path.exists() and not force_remote:
        return parse_trace_pack(path.read_text(encoding="utf-8", errors="replace"), cached=True, path=path)
    args = [
        str(TRACE_SCRIPT),
        "trace",
        _required_trade_arg(row, "market_id"),
        _required_trade_arg(row, "selection_id"),
        _required_trade_arg(row, "side"),
        _required_trade_arg(row, "entry_ts"),
        _required_trade_arg(row, "entry"),
        _required_trade_arg(row, "sp"),
        _required_trade_arg(row, "source_frame"),
        str(seconds_before),
        str(seconds_after),
        str(max_frames),
    ]
    result = subprocess.run(
        args,
        cwd=ORG_ROOT,
        capture_output=True,
        text=True,
        timeout=1200,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if result.returncode != 0:
        if path.exists():
            return parse_trace_pack(path.read_text(encoding="utf-8", errors="replace"), cached=True, path=path)
        raise RuntimeError(output.strip() or f"trace fetch exited {result.returncode}")
    clean = _clean_azure_output(output)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(clean + "\n", encoding="utf-8")
    return parse_trace_pack(clean, path=path)


def _float(value: str | object | None) -> float | None:
    if value is None:
        return None
    text = str(value).replace("$", "").replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _fmt(value: object | None) -> str:
    if value is None:
        return "-"
    text = str(value)
    return text if text else "-"


def trace_graph(pack: ParsedTracePack, width: int = 116, height: int = 13) -> Text:
    rows = _row_maps(pack)
    points: list[tuple[float, float, str, str]] = []
    for row in rows:
        x = _float(row.get("t_fire"))
        y = _float(row.get("fav_ticks"))
        if x is None or y is None:
            continue
        action = row.get("action", "")
        valid = row.get("valid", "")
        points.append((x, y, action, valid))
    if not points:
        return Text("No ordered frames returned for this trade.", style=palette.ACCENT_WARN)
    width = max(64, min(width, 180))
    height = max(7, min(height, 17))
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points] + [0.0]
    y_abs = max(3.0, *(abs(value) for value in y_values))
    y_max = math.ceil(y_abs)
    y_min = -y_max
    x_min = min(-5.0, min(x_values))
    x_max = max(30.0, max(x_values))

    def col_for(x: float) -> int:
        return max(0, min(width - 1, round((x - x_min) / max(1e-9, x_max - x_min) * (width - 1))))

    def row_for(y: float) -> int:
        return max(0, min(height - 1, round((y_max - y) / max(1e-9, y_max - y_min) * (height - 1))))

    grid: list[list[tuple[str, str]]] = [[(" ", palette.DIM) for _ in range(width)] for _ in range(height)]
    baseline = row_for(0.0)
    for col in range(width):
        grid[baseline][col] = (".", palette.DIM)
    for x, y, action, valid in points:
        col = col_for(x)
        row = row_for(y)
        if action.startswith("ENTER"):
            grid[row][col] = ("E", palette.ACCENT_WARN)
        elif action.startswith("SP"):
            grid[row][col] = ("S", palette.GOOD)
        elif y >= 0:
            grid[row][col] = ("+", palette.GOOD if valid == "Y" else palette.MUTED)
        else:
            grid[row][col] = ("-", palette.ACCENT_FAIL if valid == "Y" else palette.MUTED)

    text = Text()
    text.append("-- price path: favourable ticks vs entry\n", style=palette.MUTED)
    for index, row in enumerate(grid):
        tick_value = round(y_max - index * ((y_max - y_min) / max(1, height - 1)))
        text.append(f"{tick_value:+4d} |", style=palette.DIM)
        for char, style in row:
            text.append(char, style=style)
        text.append("|\n", style=palette.DIM)
    text.append("     +", style=palette.DIM)
    text.append("-" * width, style=palette.DIM)
    text.append("+\n", style=palette.DIM)
    fire_col = col_for(0.0)
    text.append("      ")
    text.append("pre", style=palette.DIM)
    text.append(" " * max(1, fire_col - 3), style=palette.DIM)
    text.append("fire", style=palette.ACCENT_WARN)
    text.append(" " * max(1, width - fire_col - 8), style=palette.DIM)
    text.append("off/SP\n", style=palette.GOOD)
    text.append("legend: E entry | S SP/off review | +=favourable | -=adverse | grey=invalid/ltp-only", style=palette.MUTED)
    return text


def trade_header(pack: ParsedTracePack, source_row: dict[str, str]) -> Panel:
    trade = pack.trade
    text = Text()
    text.append("Trade ", style=palette.DIM)
    text.append(source_row.get("row", "-"), style=f"bold {palette.ACCENT_MERCURY}")
    text.append(" | ", style=palette.DIM)
    text.append(str(trade.get("side") or source_row.get("side") or "-"), style=palette.ACCENT_WARN)
    text.append(" | ", style=palette.DIM)
    text.append(str(trade.get("runner") or source_row.get("runner") or "-"), style=f"bold {palette.TEXT}")
    text.append(" | ", style=palette.DIM)
    text.append(str(trade.get("venue") or source_row.get("venue") or "-"), style=palette.TEXT)
    text.append("\nEntry ", style=palette.DIM)
    text.append(_fmt(trade.get("entry_price") or source_row.get("entry")), style=palette.ACCENT_MERCURY)
    text.append(" | SP ", style=palette.DIM)
    text.append(_fmt(trade.get("sp_final") or source_row.get("sp")), style=palette.GOOD)
    text.append(" | SP ticks ", style=palette.DIM)
    text.append(_fmt(trade.get("sp_ticks") or source_row.get("ticks")), style=palette.GOOD)
    text.append(" | adverse/favourable ", style=palette.DIM)
    text.append(f"{_fmt(trade.get('max_adverse_ticks'))}/{_fmt(trade.get('max_favourable_ticks'))}", style=palette.ACCENT_PSEER)
    text.append("\nmarket ", style=palette.DIM)
    text.append(source_row.get("market_id", "-"), style=palette.ACCENT_MERCURY)
    text.append(" selection ", style=palette.DIM)
    text.append(source_row.get("selection_id", "-"), style=palette.ACCENT_MERCURY)
    text.append(" entry_ts ", style=palette.DIM)
    text.append(source_row.get("entry_ts", str(trade.get("entry_ts") or "-")), style=palette.MUTED)
    return Panel(text, title="Trade Execution Signature", border_style=palette.ACCENT_MERCURY, box=box.ROUNDED, padding=(0, 1))


def frame_tape_table(pack: ParsedTracePack, *, offset: int, limit: int) -> Table:
    rows = _row_maps(pack)
    visible = rows[offset : offset + limit]
    table = Table(box=box.SIMPLE_HEAD, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT_MERCURY}", expand=True)
    specs = (
        ("frame", "Frame", 6),
        ("t_fire", "T+Fire", 8),
        ("t_off", "T-Off", 8),
        ("price", "Price", 8),
        ("best_back", "Back", 8),
        ("best_lay", "Lay", 8),
        ("ltp", "LTP", 8),
        ("fav_ticks", "FavTk", 7),
        ("spread", "Spr", 5),
        ("touch", "Touch", 10),
        ("d3", "D3", 10),
        ("d10", "D10", 10),
        ("valid", "V", 3),
        ("clip", "Clip", 5),
        ("action", "Action", 14),
        ("frame_ref", "Frame Ref", 28),
    )
    for key, header, width in specs:
        if key == "frame_ref":
            table.add_column(header, min_width=20, ratio=3, overflow="fold")
        elif key == "action":
            table.add_column(header, width=14, overflow="fold", no_wrap=True)
        else:
            table.add_column(header, width=width, overflow="fold", justify="right" if key not in {"valid", "clip", "action"} else "left")
    for row in visible:
        values: list[Text] = []
        for key, _header, _width in specs:
            value = row.get(key, "")
            style = palette.TEXT
            if key == "fav_ticks":
                number = _float(value)
                style = palette.GOOD if number is not None and number >= 0 else palette.ACCENT_FAIL
            elif key == "valid":
                style = palette.GOOD if value == "Y" else palette.MUTED
            elif key == "clip":
                style = palette.ACCENT_WARN if value == "E" else palette.ACCENT_PSEER
            elif key == "action":
                style = palette.ACCENT_WARN if value.startswith("ENTER") else palette.MUTED
            elif key == "frame_ref":
                style = palette.MUTED
            values.append(Text(value, style=style, overflow="fold", no_wrap=key != "frame_ref"))
        table.add_row(*values)
    if not visible:
        table.add_row(*[Text("no frames" if index == 1 else "-", style=palette.MUTED) for index, _spec in enumerate(specs)])
    table.title = f"Execution Frame Tape {offset + 1 if visible else 0}-{min(offset + limit, len(rows))}/{len(rows)}"
    return table


def source_panel(pack: ParsedTracePack | None, *, note: str | None = None) -> Panel:
    text = Text()
    if pack is not None:
        text.append("Boundary ", style=palette.DIM)
        text.append(pack.boundary or "-", style=palette.GOOD if pack.boundary and pack.boundary.startswith("FULL_FRAME") else palette.ACCENT_WARN)
        text.append("\nRows ", style=palette.DIM)
        text.append(f"{pack.start or 0}-{pack.end or 0}/{pack.rows_total or 0}", style=palette.TEXT)
        text.append(" | raw messages ", style=palette.DIM)
        text.append(str(pack.raw_messages or 0), style=palette.TEXT)
        text.append(" | updates ", style=palette.DIM)
        text.append(str(pack.market_updates or 0), style=palette.TEXT)
        text.append(" | interval ", style=palette.DIM)
        text.append(f"{pack.frame_interval_ms or 0}ms", style=palette.TEXT)
        text.append("\nCache ", style=palette.DIM)
        text.append("hit" if pack.cached else "saved", style=palette.GOOD if pack.cached else palette.ACCENT_WARN)
        if pack.cache_path:
            text.append(" ", style=palette.DIM)
            text.append(pack.cache_path, style=palette.MUTED)
        if pack.source_archive:
            text.append("\nArchive ", style=palette.DIM)
            text.append(pack.source_archive, style=palette.MUTED)
        if pack.source_member:
            text.append("\nMember ", style=palette.DIM)
            text.append(pack.source_member, style=palette.MUTED)
    if note:
        text.append("\n")
        text.append(note, style=palette.ACCENT_WARN)
    text.append("\nRead-only trace recall. No Betfair login, orders, service control, secrets, or cash execution.", style=palette.ACCENT_FAIL)
    return Panel(text, title="Source / Boundary", border_style=palette.FRAME, box=box.ROUNDED, padding=(0, 1))


def command_dock() -> Panel:
    text = Text.assemble(
        ("Trace ", palette.DIM),
        ("n/p frame page  r reload cache  rf force Azure  raw show raw pack  back return  q quit", palette.TEXT),
    )
    return Panel(text, title="Command Dock", border_style=palette.ACCENT_MERCURY, box=box.ROUNDED, padding=(0, 1))


def render(
    console: Console,
    *,
    source_row: dict[str, str],
    pack: ParsedTracePack | None = None,
    frame_offset: int = 0,
    frame_limit: int = 36,
    raw_view: bool = False,
    note: str | None = None,
) -> None:
    body: list[object] = [
        Text("SP3 TRADE TRACE FORENSICS", style=f"bold {palette.ACCENT_PSEER}"),
        Text("Bucket row -> raw DAP member -> ordered frame tape -> cached local trace pack.", style=palette.MUTED),
    ]
    if pack is None:
        body.append(Text("Loading trace pack or use r to fetch.", style=palette.ACCENT_WARN))
    elif raw_view:
        body.append(Panel(pack.raw, title="Raw Trace Pack", border_style=palette.FRAME, box=box.ROUNDED, padding=(0, 1)))
    else:
        body.append(trade_header(pack, source_row))
        body.append(Panel(trace_graph(pack, width=max(80, min(console.size.width - 24, 150))), title="Trade Graph", border_style=palette.ACCENT_MERCURY, box=box.ROUNDED, padding=(0, 1)))
        body.append(frame_tape_table(pack, offset=frame_offset, limit=frame_limit))
    body.append(source_panel(pack, note=note))
    body.append(command_dock())
    panel = Panel(Group(*body), title="PSEER Full Trace // Offline Cache", border_style=palette.ACCENT_MERCURY, box=box.HEAVY, padding=(0, 1))
    console.clear()
    console.print(Align.center(panel, width=_tui_width(console)))


def render_loading(console: Console, row: dict[str, str]) -> None:
    console.clear()
    console.print(
        Align.center(
            Panel(
                Text.assemble(
                    ("Loading full trace ", palette.DIM),
                    (row.get("market_id", "-"), palette.ACCENT_MERCURY),
                    (" / ", palette.DIM),
                    (row.get("selection_id", "-"), palette.ACCENT_PSEER),
                    ("\nRaw DAP archive extraction can take 20-90 seconds. Cached trace packs open offline.", palette.MUTED),
                ),
                title="Trace Fetch",
                border_style=palette.ACCENT_MERCURY,
                box=box.ROUNDED,
                padding=(1, 2),
            ),
            width=_tui_width(console),
        )
    )


def _frame_limit(console: Console) -> int:
    return max(12, min(80, console.size.height - 28))


def loop(console: Console, *, trade_row: dict[str, str]) -> None:
    pack: ParsedTracePack | None = None
    note: str | None = None
    frame_offset = 0
    raw_view = False
    frame_limit = _frame_limit(console)
    try:
        path = trade_cache_path(trade_row)
        if not path.exists():
            render_loading(console, trade_row)
        pack = fetch_trace_pack(trade_row)
    except Exception as exc:
        note = f"trace load failed: {exc}"
    while True:
        frame_limit = _frame_limit(console)
        if pack is not None and frame_offset >= len(pack.rows):
            frame_offset = max(0, len(pack.rows) - frame_limit)
        render(console, source_row=trade_row, pack=pack, frame_offset=frame_offset, frame_limit=frame_limit, raw_view=raw_view, note=note)
        note = None
        try:
            command = console.input(f"[bold {palette.ACCENT_MERCURY}]trace[/] > ").strip().lower()
        except EOFError:
            return
        if command in {"q", "quit", "exit", "back", "b", ""}:
            return
        if command in {"n", "next", "pgdn", "pagedown"}:
            if pack is not None:
                frame_offset = min(max(0, len(pack.rows) - frame_limit), frame_offset + frame_limit)
            continue
        if command in {"p", "prev", "previous", "pgup", "pageup"}:
            frame_offset = max(0, frame_offset - frame_limit)
            continue
        if command in {"raw", "view-raw"}:
            raw_view = not raw_view
            continue
        if command in {"r", "refresh", "reload"}:
            try:
                render_loading(console, trade_row)
                pack = fetch_trace_pack(trade_row)
                frame_offset = 0
                raw_view = False
            except Exception as exc:
                note = f"trace reload failed: {exc}"
            continue
        if command in {"rf", "fresh", "force", "force-refresh", "azure"}:
            try:
                render_loading(console, trade_row)
                pack = fetch_trace_pack(trade_row, force_remote=True)
                frame_offset = 0
                raw_view = False
            except Exception as exc:
                note = f"trace Azure fetch failed: {exc}"
            continue
        note = f"unknown command: {command}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="STARGATE PSEER full trace forensics viewer")
    parser.add_argument("--market-id", required=True)
    parser.add_argument("--selection-id", required=True)
    parser.add_argument("--side", required=True, choices=("BACK", "LAY", "back", "lay"))
    parser.add_argument("--entry-ts", required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--sp", required=True)
    parser.add_argument("--source-frame", required=True)
    parser.add_argument("--runner", default="")
    parser.add_argument("--venue", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    row = {
        "market_id": args.market_id,
        "selection_id": args.selection_id,
        "side": args.side.upper(),
        "entry_ts": args.entry_ts,
        "entry": args.entry,
        "sp": args.sp,
        "source_frame": args.source_frame,
        "runner": args.runner,
        "venue": args.venue,
        "row": "-",
    }
    loop(Console(), trade_row=row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
