"""Offline-capable bucket -> trade -> full trace review TUI."""

from __future__ import annotations

import argparse
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
VIEWER_SCRIPT = ORG_ROOT / "PriceSEER" / "scripts" / "show_bucket_trade_review_azure.sh"
CACHE_DIR = STARGATE_ROOT / "runtime" / "cache" / "bucket_trade_review"


@dataclass(frozen=True)
class ParsedTradePage:
    title: str
    source: str | None
    boundary: str | None
    rows_total: int | None
    start: int | None
    end: int | None
    limit: int
    offset: int
    sort: str
    next_command: str | None
    prev_command: str | None
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


def _tui_width(console: Console) -> int:
    return max(120, min(console.size.width, MAX_TUI_WIDTH))


def _safe(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return cleaned.strip("_")[:96] or "blank"


def cache_path(region: str, venue: str, bucket_key: str, limit: int, offset: int, sort: str) -> Path:
    return CACHE_DIR / (
        f"{_safe(region.upper())}__{_safe(venue)}__{_safe(bucket_key or 'ALL')}"
        f"__sort-{_safe(sort)}__limit-{limit}__offset-{offset}.txt"
    )


def parse_trade_page(
    text: str,
    *,
    region: str,
    venue: str,
    bucket_key: str,
    limit: int,
    offset: int,
    sort: str,
    cached: bool = False,
    path: Path | None = None,
) -> ParsedTradePage:
    clean = _clean_azure_output(text)
    lines = clean.splitlines()
    title = lines[0].strip() if lines else f"Bucket Trade Review {region} {venue} {bucket_key}"
    source: str | None = None
    boundary: str | None = None
    rows_total: int | None = None
    start: int | None = None
    end: int | None = None
    next_command: str | None = None
    prev_command: str | None = None
    columns: tuple[str, ...] = ()
    rows: list[tuple[str, ...]] = []

    for line in lines:
        if line.startswith("source="):
            source = line.split("=", 1)[1].strip()
        elif line.startswith("boundary="):
            boundary = line.split("=", 1)[1].strip()
        elif line.startswith("rows_total="):
            match = re.search(r"rows_total=(\d+).*showing=(\d+)-(\d+).*limit=(\d+).*offset=(\d+).*sort=([A-Za-z0-9_-]+)", line)
            if match:
                rows_total = int(match.group(1))
                start = int(match.group(2))
                end = int(match.group(3))
                limit = int(match.group(4))
                offset = int(match.group(5))
                sort = match.group(6)
        elif line.startswith("next:"):
            next_command = line.split(":", 1)[1].strip()
        elif line.startswith("prev:"):
            prev_command = line.split(":", 1)[1].strip()

    for index, line in enumerate(lines):
        if line.startswith("| ") and " | " in line:
            maybe_cols = _split_markdown_row(line)
            if maybe_cols and maybe_cols[0] == "row":
                columns = maybe_cols
                for row_line in lines[index + 2 :]:
                    if not row_line.startswith("| "):
                        break
                    row = _split_markdown_row(row_line)
                    if len(row) == len(columns):
                        rows.append(row)
                break

    return ParsedTradePage(
        title=title,
        source=source,
        boundary=boundary,
        rows_total=rows_total,
        start=start,
        end=end,
        limit=limit,
        offset=offset,
        sort=sort,
        next_command=next_command,
        prev_command=prev_command,
        columns=columns,
        rows=tuple(rows),
        raw=clean,
        cached=cached,
        cache_path=str(path) if path is not None else None,
    )


def fetch_trade_page(
    region: str,
    venue: str,
    bucket_key: str,
    limit: int,
    offset: int,
    sort: str,
    *,
    force_remote: bool = False,
) -> ParsedTradePage:
    if region.upper() not in {"AU", "GB"}:
        raise ValueError(f"unknown region: {region}")
    if not VIEWER_SCRIPT.exists():
        raise FileNotFoundError(f"missing viewer script: {VIEWER_SCRIPT}")
    path = cache_path(region, venue, bucket_key, limit, offset, sort)
    if path.exists() and not force_remote:
        cached_page = parse_trade_page(
            path.read_text(encoding="utf-8", errors="replace"),
            region=region,
            venue=venue,
            bucket_key=bucket_key,
            limit=limit,
            offset=offset,
            sort=sort,
            cached=True,
            path=path,
        )
        if "entry_ts" in cached_page.columns and not (cached_page.boundary or "").startswith("SUMMARY_TRACE_ONLY"):
            return cached_page
    result = subprocess.run(
        [str(VIEWER_SCRIPT), "trades", region.upper(), venue, bucket_key or "ALL", str(limit), str(offset), sort],
        cwd=ORG_ROOT,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if result.returncode != 0:
        if path.exists():
            return parse_trade_page(
                path.read_text(encoding="utf-8", errors="replace"),
                region=region,
                venue=venue,
                bucket_key=bucket_key,
                limit=limit,
                offset=offset,
                sort=sort,
                cached=True,
                path=path,
            )
        raise RuntimeError(output.strip() or f"viewer exited {result.returncode}")
    clean = _clean_azure_output(output)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(clean + "\n", encoding="utf-8")
    return parse_trade_page(clean, region=region, venue=venue, bucket_key=bucket_key, limit=limit, offset=offset, sort=sort, path=path)


def _row_maps(page: ParsedTradePage) -> list[dict[str, str]]:
    return [dict(zip(page.columns, row, strict=False)) for row in page.rows]


def _money_style(value: str) -> str:
    return palette.GOOD if value.strip().startswith("$") and not value.strip().startswith("$-") else palette.ACCENT_FAIL


TRADE_BANDS: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    (
        "Trade Identity",
        (
            ("row", "#"),
            ("date", "Date"),
            ("venue", "Venue"),
            ("runner", "Runner"),
            ("off", "Off"),
            ("side", "Side"),
            ("dna", "DNA"),
        ),
    ),
    (
        "Execution / P/L",
        (
            ("row", "#"),
            ("time_band", "Band"),
            ("entry", "Entry"),
            ("sp", "SP"),
            ("ticks", "Tk"),
            ("raw_pnl_5", "Raw $5"),
            ("paper_pnl", "Paper"),
            ("trace", "Trace min/mean/max/best"),
            ("path", "Path"),
        ),
    ),
    (
        "Capacity / Source",
        (
            ("row", "#"),
            ("cap", "Cap"),
            ("touch", "Touch"),
            ("d3", "D3"),
            ("d10", "D10"),
            ("spread", "Spread"),
            ("market_id", "Market"),
            ("selection_id", "Sel"),
            ("source_frame", "Source Frame"),
        ),
    ),
    (
        "Bucket Key",
        (
            ("row", "#"),
            ("bucket_key", "Bucket"),
        ),
    ),
)


def _trade_cell_style(column: str, value: str) -> str:
    if column in {"raw_pnl_5", "paper_pnl"}:
        return _money_style(value)
    if column in {"runner", "market_id", "selection_id"}:
        return palette.ACCENT_MERCURY
    if column in {"dna", "bucket_key"}:
        return palette.ACCENT_PSEER
    if column == "sp":
        return palette.GOOD
    if column in {"date", "off", "trace", "path", "source_frame"}:
        return palette.MUTED
    return palette.TEXT


def _trade_band_table(page: ParsedTradePage, title: str, columns: tuple[tuple[str, str], ...]) -> Table:
    table = Table(box=box.SIMPLE_HEAD, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT_MERCURY}", expand=True)
    for column, header in columns:
        if column == "row":
            table.add_column(header, justify="right", no_wrap=True, width=4)
        elif column in {"runner", "bucket_key", "source_frame"}:
            table.add_column(header, min_width=18, ratio=3, overflow="fold")
        elif column in {"off", "market_id", "selection_id", "trace", "path"}:
            table.add_column(header, min_width=12, ratio=2, overflow="fold")
        else:
            table.add_column(header, min_width=max(5, len(header)), overflow="fold")
    for row in _row_maps(page):
        table.add_row(
            *[
                Text(row.get(column, ""), style=_trade_cell_style(column, row.get(column, "")), overflow="fold", no_wrap=False)
                for column, _header in columns
            ]
        )
    if not page.rows:
        table.add_row(*[Text("no trades returned" if index == 1 else "-", style=palette.MUTED) for index, _ in enumerate(columns)])
    table.title = title
    return table


def trade_ledger_table(page: ParsedTradePage) -> Group:
    return Group(
        Text("Trade rows are split into bands to prevent truncation. Use d# to open the matching full trace.", style=palette.MUTED),
        *[_trade_band_table(page, title, columns) for title, columns in TRADE_BANDS],
    )


def _float(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.replace("$", "").replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _trace_values(row: dict[str, str]) -> dict[str, float]:
    values: dict[str, float] = {}
    parts = row.get("trace", "").split("/")
    for key, part in zip(("min", "mean", "max", "best"), parts, strict=False):
        value = _float(part)
        if value is not None:
            values[key] = value
    ticks = _float(row.get("ticks"))
    if ticks is not None:
        values["sp"] = ticks
    return values


def trace_summary(row: dict[str, str], width: int = 104) -> Text:
    values = _trace_values(row)
    if not values:
        return Text("No summary trace metrics on this row.", style=palette.ACCENT_WARN)
    low = min(-10.0, min(values.values()))
    high = max(10.0, max(values.values()))
    if high <= low:
        high = low + 1.0
    width = max(48, min(width, 140))

    def pos(value: float) -> int:
        return max(0, min(width - 1, round((value - low) / (high - low) * (width - 1))))

    markers = {
        "0": ("0", 0.0, palette.DIM),
        "SL3": ("3", -3.0, palette.ACCENT_WARN),
        "min": ("m", values.get("min"), palette.ACCENT_FAIL),
        "mean": ("a", values.get("mean"), palette.ACCENT_MERCURY),
        "max": ("x", values.get("max"), palette.GOOD),
        "best": ("b", values.get("best"), palette.ACCENT_PSEER),
        "SP": ("S", values.get("sp"), palette.TEXT),
    }
    slots: list[list[tuple[str, str]]] = [[] for _ in range(width)]
    for _label, (char, value, style) in markers.items():
        if value is None:
            continue
        slots[pos(float(value))].append((char, style))
    text = Text()
    text.append(f"scale {low:.1f} to {high:.1f} ticks\n", style=palette.DIM)
    for index, slot in enumerate(slots):
        if slot:
            char, style = slot[-1]
            text.append(char, style=style)
        else:
            text.append("|" if index % 8 == 0 else "-", style=palette.DIM)
    text.append("\n", style=palette.DIM)
    text.append("legend: m=min adverse  a=mean  x=max favourable  b=best exit  S=SP ticks  3=SL3 stop screen", style=palette.MUTED)
    return text


def detail_tables(row: dict[str, str]) -> Group:
    summary = Table.grid(expand=True)
    summary.add_column(ratio=1)
    summary.add_column(ratio=1)
    left = Table(box=box.SIMPLE, show_header=False, expand=True, border_style=palette.FRAME)
    right = Table(box=box.SIMPLE, show_header=False, expand=True, border_style=palette.FRAME)
    for table in (left, right):
        table.add_column("Metric", style=palette.ACCENT_MERCURY, no_wrap=True)
        table.add_column("Value", style=palette.TEXT, overflow="fold")
    for key in ("market_id", "selection_id", "venue", "runner", "off", "side", "dna", "bucket_key"):
        left.add_row(key, row.get(key, ""))
    for key in ("entry", "sp", "ticks", "raw_pnl_5", "paper_pnl", "cap", "touch", "d3", "d10", "spread", "path"):
        right.add_row(key, row.get(key, ""))
    summary.add_row(left, right)
    source = Text.assemble(
        ("source frame ", palette.DIM),
        (row.get("source_frame", "-"), palette.MUTED),
        ("\ntrace boundary ", palette.DIM),
        ("TRACE_FETCH_READY: use d# from the ledger to reconstruct and cache the ordered frame tape.", palette.ACCENT_WARN),
    )
    return Group(Panel(trace_summary(row), title="Summary Trace Shape", border_style=palette.ACCENT_MERCURY, box=box.ROUNDED), summary, Panel(source, title="Source / Boundary", border_style=palette.FRAME, box=box.ROUNDED))


def source_panel(page: ParsedTradePage | None, *, region: str, venue: str, bucket_key: str, limit: int, offset: int, sort: str, note: str | None = None) -> Panel:
    body = Text()
    body.append("Scope ", style=palette.DIM)
    body.append(f"{region.upper()} / {venue} / {bucket_key or 'ALL'}", style=palette.TEXT)
    body.append(" | sort ", style=palette.DIM)
    body.append(sort, style=palette.ACCENT_PSEER)
    body.append(" | limit ", style=palette.DIM)
    body.append(str(limit), style=palette.TEXT)
    body.append(" | offset ", style=palette.DIM)
    body.append(str(offset), style=palette.TEXT)
    if page is not None:
        body.append("\nRows ", style=palette.DIM)
        body.append(f"{page.start or 0}-{page.end or 0} / {page.rows_total or 0}", style=palette.TEXT)
        body.append(" | cache ", style=palette.DIM)
        body.append("hit" if page.cached else "saved", style=palette.GOOD if page.cached else palette.ACCENT_WARN)
        if page.next_command:
            body.append(" | next available", style=palette.ACCENT_MERCURY)
        if page.prev_command:
            body.append(" | prev available", style=palette.ACCENT_MERCURY)
        if page.cache_path:
            body.append("\nCache ", style=palette.DIM)
            body.append(page.cache_path, style=palette.MUTED)
        if page.source:
            body.append("\nAzure source ", style=palette.DIM)
            body.append(page.source, style=palette.MUTED)
        if page.boundary:
            body.append("\nBoundary ", style=palette.DIM)
            body.append(page.boundary, style=palette.ACCENT_WARN)
    if note:
        body.append("\n")
        body.append(note, style=palette.ACCENT_WARN)
    body.append("\nRead-only report recall. No Animal shadow, Betfair connection, live orders, service control, or cash execution.", style=palette.ACCENT_FAIL)
    return Panel(body, title="Source / Boundary", border_style=palette.FRAME, box=box.ROUNDED, padding=(0, 1))


def command_dock(detail: bool = False) -> Panel:
    if detail:
        commands = Text.assemble(
            ("Detail ", palette.DIM),
            ("n/p next-prev row  back return to ledger  q quit", palette.TEXT),
        )
    else:
        commands = Text.assemble(
            ("Open ", palette.DIM),
            ("d# or # full trace", palette.TEXT),
            ("\nPage ", palette.DIM),
            ("n next  p prev  r reload cache  rf force Azure  l <limit>  s <off|pnl|bad|trace>", palette.TEXT),
            ("\nOffline ", palette.DIM),
            ("pack cache pages  pack traces cache pages plus full trace packs", palette.ACCENT_PSEER),
            ("\nExit ", palette.DIM),
            ("back  q", palette.MUTED),
        )
    return Panel(commands, title="Command Dock", border_style=palette.ACCENT_MERCURY, box=box.ROUNDED, padding=(0, 1))


def render(
    console: Console,
    *,
    region: str,
    venue: str,
    bucket_key: str = "ALL",
    limit: int = 25,
    offset: int = 0,
    sort: str = "off",
    page: ParsedTradePage | None = None,
    detail_row: dict[str, str] | None = None,
    note: str | None = None,
) -> None:
    title = "PriceSEER Bucket Trade Review // Offline Cache"
    body: list[object] = [
        Text("BUCKET -> TRADE -> FULL TRACE", style=f"bold {palette.ACCENT_PSEER}"),
        Text("Operator review surface for venue/bucket evidence with raw DAP trace reconstruction.", style=palette.MUTED),
    ]
    if detail_row is not None:
        body.append(Text(f"Trade {detail_row.get('row', '-')} // {detail_row.get('runner', '-')}", style=f"bold {palette.ACCENT_MERCURY}"))
        body.append(detail_tables(detail_row))
        body.append(source_panel(page, region=region, venue=venue, bucket_key=bucket_key, limit=limit, offset=offset, sort=sort, note=note))
        body.append(command_dock(detail=True))
    else:
        if page is not None:
            body.append(Text(page.title, style=f"bold {palette.ACCENT_MERCURY}"))
            body.append(trade_ledger_table(page))
        else:
            body.append(Text("Loading or choose r to fetch the first cached/remote page.", style=palette.ACCENT_WARN))
        body.append(source_panel(page, region=region, venue=venue, bucket_key=bucket_key, limit=limit, offset=offset, sort=sort, note=note))
        body.append(command_dock(detail=False))
    panel = Panel(Group(*body), title=title, border_style=palette.ACCENT_MERCURY, box=box.HEAVY, padding=(0, 1))
    console.clear()
    console.print(Align.center(panel, width=_tui_width(console)))


def render_loading(console: Console, *, region: str, venue: str, bucket_key: str, limit: int, offset: int, sort: str, label: str = "Bucket Trade Fetch") -> None:
    console.clear()
    console.print(
        Align.center(
            Panel(
                Text.assemble(
                    ("Loading ", palette.DIM),
                    (f"{region.upper()} {venue}", palette.ACCENT_PSEER),
                    (" bucket ", palette.DIM),
                    (bucket_key or "ALL", palette.TEXT),
                    ("\nlimit ", palette.DIM),
                    (str(limit), palette.TEXT),
                    (" offset ", palette.DIM),
                    (str(offset), palette.TEXT),
                    (" sort ", palette.DIM),
                    (sort, palette.ACCENT_MERCURY),
                    ("\nAzure run-command can take 20-60 seconds. Cached pages open offline.", palette.MUTED),
                ),
                title=label,
                border_style=palette.ACCENT_MERCURY,
                box=box.ROUNDED,
                padding=(1, 2),
            ),
            width=_tui_width(console),
        )
    )


def _select_row(page: ParsedTradePage, selector: int) -> dict[str, str] | None:
    rows = _row_maps(page)
    if 1 <= selector <= len(rows):
        return rows[selector - 1]
    for row in rows:
        try:
            if int(row.get("row", "0")) == selector:
                return row
        except ValueError:
            continue
    return None


def _parse_command(command: str, *, limit: int, offset: int, sort: str) -> tuple[int, int, str, bool, bool, str | None]:
    parts = command.split()
    if not parts:
        return limit, offset, sort, False, False, None
    first = parts[0]
    if first in {"n", "next"}:
        return limit, offset + limit, sort, True, False, None
    if first in {"p", "prev", "previous"}:
        return limit, max(0, offset - limit), sort, True, False, None
    if first in {"r", "refresh", "reload"}:
        return limit, offset, sort, True, False, None
    if first in {"rf", "fresh", "force", "force-refresh", "azure"}:
        return limit, offset, sort, True, True, None
    if first in {"l", "limit"} and len(parts) > 1 and parts[1].isdigit():
        return int(parts[1]), 0, sort, True, False, None
    if first in {"s", "sort"} and len(parts) > 1 and parts[1] in {"off", "pnl", "bad", "trace"}:
        return limit, 0, parts[1], True, False, None
    if first == "pack":
        if len(parts) > 1 and parts[1] in {"trace", "traces", "full", "all"}:
            return limit, offset, sort, False, False, "pack-traces"
        return limit, offset, sort, False, False, "pack"
    return limit, offset, sort, False, False, None


def prefetch_bucket(
    console: Console,
    *,
    region: str,
    venue: str,
    bucket_key: str,
    limit: int,
    sort: str,
    page: ParsedTradePage | None,
    with_traces: bool = False,
) -> str:
    if page is None:
        render_loading(console, region=region, venue=venue, bucket_key=bucket_key, limit=limit, offset=0, sort=sort, label="Offline Pack Seed")
        page = fetch_trade_page(region, venue, bucket_key, limit, 0, sort)
    total = page.rows_total or 0
    if total <= 0:
        return "pack skipped: no rows in this bucket"
    cached_pages = 0
    cached_traces = 0
    failed_traces = 0
    trace_fetch = None
    trace_cache_path = None
    if with_traces:
        from .trace_forensics import fetch_trace_pack, trade_cache_path

        trace_fetch = fetch_trace_pack
        trace_cache_path = trade_cache_path
    for next_offset in range(0, total, limit):
        render_loading(console, region=region, venue=venue, bucket_key=bucket_key, limit=limit, offset=next_offset, sort=sort, label=f"Offline Pack {cached_pages + 1}")
        next_page = fetch_trade_page(region, venue, bucket_key, limit, next_offset, sort)
        cached_pages += 1
        if with_traces and trace_fetch is not None and trace_cache_path is not None:
            for row in _row_maps(next_page):
                trace_path = trace_cache_path(row)
                if trace_path.exists():
                    cached_traces += 1
                    continue
                render_loading(console, region=region, venue=venue, bucket_key=bucket_key, limit=limit, offset=next_offset, sort=sort, label=f"Trace Pack {row.get('row', '-')}")
                try:
                    trace_fetch(row)
                    cached_traces += 1
                except Exception:
                    failed_traces += 1
    if with_traces:
        return (
            f"offline pack cached {cached_pages} page(s) and {cached_traces} trace pack(s) "
            f"for {region.upper()} {venue} {bucket_key or 'ALL'}; failed traces {failed_traces}"
        )
    return f"offline pack cached {cached_pages} page(s) for {region.upper()} {venue} {bucket_key or 'ALL'}"


def prefetch_bucket_cli(
    *,
    region: str,
    venue: str,
    bucket_key: str,
    limit: int,
    sort: str,
    force_remote: bool = False,
    with_traces: bool = False,
    console: Console | None = None,
) -> int:
    console = console or Console()
    first = fetch_trade_page(region, venue, bucket_key, limit, 0, sort, force_remote=force_remote)
    total = first.rows_total or 0
    if total <= 0:
        console.print(f"no rows for {region.upper()} {venue} {bucket_key or 'ALL'}", style=palette.ACCENT_WARN)
        return 0
    console.print(f"prefetch {region.upper()} {venue} {bucket_key or 'ALL'} rows={total} limit={limit} sort={sort}", style=palette.ACCENT_MERCURY)
    pages = 0
    cached_traces = 0
    failed_traces = 0
    trace_fetch = None
    trace_cache_path = None
    if with_traces:
        from .trace_forensics import fetch_trace_pack, trade_cache_path

        trace_fetch = fetch_trace_pack
        trace_cache_path = trade_cache_path
    for next_offset in range(0, total, limit):
        page = fetch_trade_page(region, venue, bucket_key, limit, next_offset, sort, force_remote=force_remote)
        pages += 1
        console.print(
            f"cached page {pages}: rows {page.start or 0}-{page.end or 0}/{page.rows_total or 0} -> {page.cache_path}",
            style=palette.MUTED,
        )
        if with_traces and trace_fetch is not None and trace_cache_path is not None:
            for row in _row_maps(page):
                try:
                    trace = trace_fetch(row, force_remote=force_remote and not trace_cache_path(row).exists())
                    cached_traces += 1
                    console.print(
                        f"cached trace {cached_traces}: trade {row.get('row', '-')} {row.get('runner', '-')} -> {trace.cache_path}",
                        style=palette.MUTED,
                    )
                except Exception as exc:
                    failed_traces += 1
                    console.print(f"trace failed: trade {row.get('row', '-')} {row.get('runner', '-')} {exc}", style=palette.ACCENT_WARN)
    if with_traces:
        console.print(f"offline pack complete: {pages} page(s), {cached_traces} trace pack(s), {failed_traces} trace failure(s)", style=palette.GOOD)
    else:
        console.print(f"offline pack complete: {pages} page(s)", style=palette.GOOD)
    return 0


def loop(
    console: Console,
    *,
    initial_region: str = "GB",
    initial_venue: str = "Newcastle",
    initial_bucket_key: str = "ALL",
    initial_limit: int = 25,
    initial_offset: int = 0,
    initial_sort: str = "off",
) -> None:
    region = initial_region.upper()
    venue = initial_venue
    bucket_key = initial_bucket_key or "ALL"
    limit = initial_limit
    offset = initial_offset
    sort = initial_sort
    page: ParsedTradePage | None = None
    detail_row: dict[str, str] | None = None
    note: str | None = None
    try:
        path = cache_path(region, venue, bucket_key, limit, offset, sort)
        if not path.exists():
            render_loading(console, region=region, venue=venue, bucket_key=bucket_key, limit=limit, offset=offset, sort=sort)
        page = fetch_trade_page(region, venue, bucket_key, limit, offset, sort)
    except Exception as exc:
        note = f"initial load failed: {exc}"
    while True:
        render(console, region=region, venue=venue, bucket_key=bucket_key, limit=limit, offset=offset, sort=sort, page=page, detail_row=detail_row, note=note)
        note = None
        try:
            command = console.input(f"[bold {palette.ACCENT_MERCURY}]bucket-review[/] > ").strip()
        except EOFError:
            return
        command_l = command.lower()
        if command_l in {"q", "quit", "exit"}:
            return
        if command_l in {"", "b", "back"}:
            if detail_row is not None:
                detail_row = None
                continue
            return
        if detail_row is not None and command_l in {"n", "next", "p", "prev", "previous"} and page is not None:
            rows = _row_maps(page)
            if detail_row in rows:
                index = rows.index(detail_row)
                index = min(len(rows) - 1, index + 1) if command_l in {"n", "next"} else max(0, index - 1)
                detail_row = rows[index]
            continue
        if page is not None:
            detail_match = re.fullmatch(r"(?:d\s*)?(\d+)", command_l)
            if detail_match:
                selected = _select_row(page, int(detail_match.group(1)))
                if selected is None:
                    note = f"trade row not on this page: {detail_match.group(1)}"
                else:
                    try:
                        from .trace_forensics import loop as trace_forensics_loop

                        trace_forensics_loop(console, trade_row=selected)
                    except Exception as exc:
                        note = f"trace viewer failed: {exc}"
                continue
        try:
            next_limit, next_offset, next_sort, should_fetch, force_remote, action = _parse_command(command_l, limit=limit, offset=offset, sort=sort)
        except ValueError:
            note = f"invalid command: {command}"
            continue
        if action in {"pack", "pack-traces"}:
            try:
                note = prefetch_bucket(
                    console,
                    region=region,
                    venue=venue,
                    bucket_key=bucket_key,
                    limit=limit,
                    sort=sort,
                    page=page,
                    with_traces=action == "pack-traces",
                )
                page = fetch_trade_page(region, venue, bucket_key, limit, offset, sort)
            except Exception as exc:
                note = f"pack failed: {exc}"
            continue
        if not should_fetch:
            note = f"unknown command: {command}"
            continue
        limit, offset, sort = next_limit, next_offset, next_sort
        detail_row = None
        try:
            path = cache_path(region, venue, bucket_key, limit, offset, sort)
            if not path.exists() or force_remote:
                render_loading(console, region=region, venue=venue, bucket_key=bucket_key, limit=limit, offset=offset, sort=sort)
            page = fetch_trade_page(region, venue, bucket_key, limit, offset, sort, force_remote=force_remote)
        except Exception as exc:
            page = None
            note = f"load failed: {exc}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="STARGATE PriceSEER bucket trade review TUI")
    parser.add_argument("--region", default="GB", choices=("AU", "GB", "au", "gb"))
    parser.add_argument("--venue", default="Newcastle")
    parser.add_argument("--bucket", default="ALL")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--sort", default="off", choices=("off", "pnl", "bad", "trace"))
    parser.add_argument("--prefetch", action="store_true", help="cache every page for this region/venue/bucket and exit")
    parser.add_argument("--prefetch-traces", action="store_true", help="also cache full trace packs for every prefetched trade")
    parser.add_argument("--force-remote", action="store_true", help="refresh pages from Azure even if local cache exists")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console()
    if args.prefetch or args.prefetch_traces:
        return prefetch_bucket_cli(
            region=args.region,
            venue=args.venue,
            bucket_key=args.bucket,
            limit=args.limit,
            sort=args.sort,
            force_remote=args.force_remote,
            with_traces=args.prefetch_traces,
            console=console,
        )
    loop(
        console,
        initial_region=args.region,
        initial_venue=args.venue,
        initial_bucket_key=args.bucket,
        initial_limit=args.limit,
        initial_offset=args.offset,
        initial_sort=args.sort,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
