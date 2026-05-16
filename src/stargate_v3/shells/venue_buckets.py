"""STARGATE TUI for PriceSEER AU/GB venue bucket tables."""

from __future__ import annotations

import argparse
import re
import subprocess
import time
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
VIEWER_SCRIPT = ORG_ROOT / "PriceSEER" / "scripts" / "show_venue_distribution_azure.sh"
CACHE_DIR = STARGATE_ROOT / "runtime" / "cache" / "venue_buckets"


@dataclass(frozen=True)
class VenueMode:
    key: str
    label: str
    scope: str
    purpose: str


@dataclass(frozen=True)
class ParsedPage:
    title: str
    rows_total: int | None
    start: int | None
    end: int | None
    limit: int
    offset: int
    next_command: str | None
    prev_command: str | None
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    raw: str
    cached: bool = False
    cache_path: str | None = None


MODES: tuple[VenueMode, ...] = (
    VenueMode("gb", "GB Venue Totals", "GB BACK T300_390", "whole-venue positive/flat/negative triage"),
    VenueMode("au", "AU Venue Totals", "AU BACK R2P1/R2P2 T180/T300", "whole-venue capacity and quality triage"),
    VenueMode("best-gb", "GB Best Bucket Per Venue", "GB BACK T300_390", "best venue bucket before subtraction"),
    VenueMode("best-au", "AU Best Bucket Per Venue", "AU BACK R2P1/R2P2", "best venue bucket before operator labels"),
    VenueMode("buckets-gb", "GB All Venue Buckets", "GB BACK T300_390", "detailed inclusion/exclusion bucket table"),
    VenueMode("buckets-au", "AU All Venue Buckets", "AU BACK R2P1/R2P2", "detailed metro/non-metro bucket table"),
)

MODE_KEYS = {mode.key for mode in MODES}

HEADER_ALIASES = {
    "venue": "Venue",
    "bucket_key": "Bucket",
    "rows": "Fires",
    "markets": "Mkts",
    "source_stake_turnover": "Stake",
    "sl3_pnl_5": "SL3 P/L",
    "sl3_dist": "SL3 Wins/Flat/Losses",
    "raw_dist": "Raw SP Wins/Flat/Losses",
    "source_dist": "Source Wins/Flat/Losses",
    "sl3_gross_pos": "SL3 Gross Wins",
    "sl3_gross_neg": "SL3 Gross Losses",
    "sl3_avg_win": "SL3 Avg Win",
    "sl3_avg_loss": "SL3 Avg Loss",
    "median_d3": "D3",
    "median_d10": "D10",
    "false_stopped_winner_rate": "False Stop",
    "best_bucket_key": "Best Bucket",
    "best_rows": "Best Fires",
    "best_sl3_pnl_5": "Best P/L",
    "best_sl3_dist": "Best Wins/Flat/Losses",
    "best_median_d3": "Best D3",
    "best_median_d10": "Best D10",
    "best_false_stopped_winner_rate": "Best False",
}

BAND_COLUMNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Execution / P/L",
        (
            "venue",
            "rows",
            "markets",
            "source_stake_turnover",
            "sl3_pnl_5",
        ),
    ),
    (
        "Bucket Identity",
        (
            "venue",
            "bucket_key",
            "best_bucket_key",
        ),
    ),
    (
        "Best Bucket P/L",
        (
            "venue",
            "best_rows",
            "best_sl3_pnl_5",
            "best_sl3_dist",
        ),
    ),
    (
        "Outcome Counts",
        (
            "venue",
            "sl3_dist",
            "raw_dist",
            "source_dist",
        ),
    ),
    (
        "SL3 Win / Loss Dollars",
        (
            "venue",
            "sl3_gross_pos",
            "sl3_gross_neg",
            "sl3_avg_win",
            "sl3_avg_loss",
        ),
    ),
    (
        "Capacity / Stop Profile",
        (
            "venue",
            "median_d3",
            "median_d10",
            "false_stopped_winner_rate",
            "best_median_d3",
            "best_median_d10",
            "best_false_stopped_winner_rate",
        ),
    ),
)


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


def cache_path(mode: str, limit: int, offset: int) -> Path:
    safe_mode = mode.replace("/", "_")
    return CACHE_DIR / f"{safe_mode}__limit-{limit}__offset-{offset}.txt"


def parse_page(
    text: str,
    *,
    mode: str,
    limit: int,
    offset: int,
    cached: bool = False,
    path: Path | None = None,
) -> ParsedPage:
    clean = _clean_azure_output(text)
    lines = clean.splitlines()
    title = lines[0].strip() if lines else f"{mode} venue bucket page"
    rows_total: int | None = None
    start: int | None = None
    end: int | None = None
    next_command: str | None = None
    prev_command: str | None = None
    columns: tuple[str, ...] = ()
    rows: list[tuple[str, ...]] = []

    for line in lines:
        if line.startswith("rows_total="):
            match = re.search(r"rows_total=(\d+).*showing=(\d+)-(\d+).*limit=(\d+).*offset=(\d+)", line)
            if match:
                rows_total = int(match.group(1))
                start = int(match.group(2))
                end = int(match.group(3))
                limit = int(match.group(4))
                offset = int(match.group(5))
        elif line.startswith("next:"):
            next_command = line.split(":", 1)[1].strip()
        elif line.startswith("prev:"):
            prev_command = line.split(":", 1)[1].strip()

    for index, line in enumerate(lines):
        if line.startswith("| ") and " | " in line:
            maybe_cols = _split_markdown_row(line)
            if maybe_cols and maybe_cols[0] in {"venue", "Venue"}:
                columns = maybe_cols
                for row_line in lines[index + 2 :]:
                    if not row_line.startswith("| "):
                        break
                    row = _split_markdown_row(row_line)
                    if len(row) == len(columns):
                        rows.append(row)
                break

    return ParsedPage(
        title=title,
        rows_total=rows_total,
        start=start,
        end=end,
        limit=limit,
        offset=offset,
        next_command=next_command,
        prev_command=prev_command,
        columns=columns,
        rows=tuple(rows),
        raw=clean,
        cached=cached,
        cache_path=str(path) if path is not None else None,
    )


def fetch_page(mode: str, limit: int, offset: int, *, force_remote: bool = False) -> ParsedPage:
    if mode not in MODE_KEYS:
        raise ValueError(f"unknown mode: {mode}")
    if not VIEWER_SCRIPT.exists():
        raise FileNotFoundError(f"missing viewer script: {VIEWER_SCRIPT}")
    path = cache_path(mode, limit, offset)
    if path.exists() and not force_remote:
        return parse_page(path.read_text(encoding="utf-8", errors="replace"), mode=mode, limit=limit, offset=offset, cached=True, path=path)
    result: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, 19):
        result = subprocess.run(
            [str(VIEWER_SCRIPT), mode, str(limit), str(offset)],
            cwd=ORG_ROOT,
            capture_output=True,
            text=True,
            timeout=240,
            check=False,
        )
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        if result.returncode == 0:
            break
        if "Run command extension execution is in progress" in output or "Conflict" in output:
            time.sleep(10)
            continue
        break
    if result is None:
        raise RuntimeError("viewer did not run")
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if result.returncode != 0:
        if path.exists():
            return parse_page(path.read_text(encoding="utf-8", errors="replace"), mode=mode, limit=limit, offset=offset, cached=True, path=path)
        raise RuntimeError(output.strip() or f"viewer exited {result.returncode}")
    clean = _clean_azure_output(output)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(clean + "\n", encoding="utf-8")
    return parse_page(clean, mode=mode, limit=limit, offset=offset, cached=False, path=path)


def mode_table() -> Table:
    table = Table(box=box.ROUNDED, border_style=palette.FRAME, header_style=f"bold {palette.ACCENT_MERCURY}", expand=True)
    table.add_column("Command", width=12)
    table.add_column("View", min_width=24)
    table.add_column("Scope", min_width=28)
    table.add_column("Use", min_width=44)
    for mode in MODES:
        table.add_row(
            Text(mode.key, style=f"bold {palette.ACCENT_PSEER}"),
            Text(mode.label, style=palette.TEXT),
            Text(mode.scope, style=palette.MUTED),
            Text(mode.purpose, style=palette.MUTED),
        )
    return table


def _present_columns(page: ParsedPage, columns: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(column for column in columns if column in page.columns)


def _table_band(page: ParsedPage, title: str, columns: tuple[str, ...]) -> Table:
    table = Table(
        box=box.ROUNDED,
        border_style=palette.ACCENT_PSEER,
        header_style=f"bold {palette.ACCENT_PSEER}",
        expand=True,
        show_lines=False,
    )
    row_maps = []
    for row_number, row in enumerate(page.rows, start=1):
        row_map = dict(zip(page.columns, row, strict=False))
        row_map["__row_number"] = str((page.offset or 0) + row_number)
        row_maps.append(row_map)
    table.add_column("#", justify="right", width=4, no_wrap=True)
    for column in columns:
        header = HEADER_ALIASES.get(column, column)
        if column in {"venue"}:
            table.add_column(header, min_width=12, overflow="fold")
        elif column in {"bucket_key", "best_bucket_key"}:
            table.add_column(header, min_width=30, ratio=4, overflow="fold")
        else:
            table.add_column(header, min_width=max(7, len(header)), overflow="fold")
    for row_map in row_maps:
        cells = [Text(row_map["__row_number"], style=palette.ACCENT_MERCURY)]
        for index, column in enumerate(columns):
            value = row_map.get(column, "")
            style = palette.TEXT if index < 2 else palette.MUTED
            cells.append(Text(value, style=style, overflow="fold", no_wrap=False))
        table.add_row(*cells)
    table.title = title
    return table


def page_tables(page: ParsedPage) -> Group | Text:
    if not page.columns:
        return Text(page.raw or "No table returned.", style=palette.ACCENT_FAIL)

    used: set[str] = set()
    bands: list[Table] = []
    for title, requested_columns in BAND_COLUMNS:
        columns = _present_columns(page, requested_columns)
        if columns and not (len(columns) == 1 and columns[0] == "venue"):
            used.update(columns)
            bands.append(_table_band(page, title, columns))
    remaining = tuple(column for column in page.columns if column not in used)
    if remaining:
        bands.append(_table_band(page, "Other Fields", remaining))
    return Group(
        Text("Rows are split into bands to prevent truncation. Use n/p to page more rows.", style=palette.MUTED),
        Text(
            "Counts read as wins / flat / losses. Example 32/0/37 means 32 positive trades, 0 flat trades, 37 negative trades. "
            "SL3 is the approximate -3 tick protection screen; Raw SP is entry-to-SP green-up; Source is the original result-settlement/paper basis.",
            style=palette.ACCENT_WARN,
        ),
        *bands,
    )


def source_panel(page: ParsedPage | None, *, mode: str, limit: int, offset: int, note: str | None = None) -> Panel:
    body = Text()
    body.append("Source ", style=palette.DIM)
    body.append(str(VIEWER_SCRIPT), style=palette.MUTED)
    body.append("\nMode ", style=palette.DIM)
    body.append(mode, style=palette.ACCENT_PSEER)
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
            body.append(" | next ", style=palette.DIM)
            body.append(page.next_command, style=palette.ACCENT_MERCURY)
        if page.prev_command:
            body.append(" | prev ", style=palette.DIM)
            body.append(page.prev_command, style=palette.ACCENT_MERCURY)
    if note:
        body.append("\n")
        body.append(note, style=palette.ACCENT_WARN)
    if page is not None and page.cache_path:
        body.append("\nCache ", style=palette.DIM)
        body.append(page.cache_path, style=palette.MUTED)
    body.append("\nRead-only Azure report recall. No Animal shadow, Betfair connection, live orders, service control, or cash execution.", style=palette.ACCENT_FAIL)
    return Panel(body, title="Source / Boundary", border_style=palette.FRAME, box=box.ROUNDED, padding=(0, 1))


def command_dock() -> Panel:
    return Panel(
        Text.assemble(
            ("Views ", palette.DIM),
            ("gb  au  best-gb  best-au  buckets-gb  buckets-au", palette.TEXT),
            ("\nOpen ", palette.DIM),
            ("t# trade ledger for row", palette.ACCENT_PSEER),
            ("\nPage ", palette.DIM),
            ("n next  p prev  r reload cache  rf force Azure  l <limit>  <mode> <limit> <offset>", palette.TEXT),
            ("\nExit ", palette.DIM),
            ("back  q", palette.MUTED),
        ),
        title="Command Dock",
        border_style=palette.ACCENT_MERCURY,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def render(
    console: Console,
    *,
    mode: str = "gb",
    limit: int = 20,
    offset: int = 0,
    page: ParsedPage | None = None,
    note: str | None = None,
) -> None:
    body: list[object] = [
        Text("AU / GB VENUE BUCKET TABLES", style=f"bold {palette.ACCENT_PSEER}"),
        Text("Full positive / flat / negative venue and bucket review for operator triage.", style=palette.MUTED),
        mode_table(),
    ]
    if page is not None:
        body.append(Text(page.title, style=f"bold {palette.ACCENT_MERCURY}"))
        body.append(page_tables(page))
    else:
        body.append(Text("Choose a view command to load the first page.", style=palette.ACCENT_WARN))
    body.extend([source_panel(page, mode=mode, limit=limit, offset=offset, note=note), command_dock()])
    panel = Panel(
        Group(*body),
        title="PriceSEER Venue Buckets // TUI",
        border_style=palette.ACCENT_MERCURY,
        box=box.HEAVY,
        padding=(0, 1),
    )
    console.clear()
    console.print(Align.center(panel, width=_tui_width(console)))


def render_loading(console: Console, *, mode: str, limit: int, offset: int) -> None:
    console.clear()
    console.print(
        Align.center(
            Panel(
                Text.assemble(
                    ("Loading ", palette.DIM),
                    (mode, palette.ACCENT_PSEER),
                    (" limit ", palette.DIM),
                    (str(limit), palette.TEXT),
                    (" offset ", palette.DIM),
                    (str(offset), palette.TEXT),
                    ("\nAzure run-command can take 20-60 seconds. This is read-only report recall.", palette.MUTED),
                ),
                title="Venue Bucket Fetch",
                border_style=palette.ACCENT_MERCURY,
                box=box.ROUNDED,
                padding=(1, 2),
            ),
            width=_tui_width(console),
        )
    )


def _parse_command(command: str, *, mode: str, limit: int, offset: int) -> tuple[str, int, int, bool, bool]:
    parts = command.split()
    if not parts:
        return mode, limit, offset, False, False
    first = parts[0]
    if first in MODE_KEYS:
        new_limit = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else limit
        new_offset = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        return first, new_limit, new_offset, True, False
    if first in {"n", "next"}:
        return mode, limit, offset + limit, True, False
    if first in {"p", "prev", "previous"}:
        return mode, limit, max(0, offset - limit), True, False
    if first in {"r", "refresh", "reload"}:
        return mode, limit, offset, True, False
    if first in {"rf", "fresh", "force", "force-refresh", "azure"}:
        return mode, limit, offset, True, True
    if first in {"l", "limit"} and len(parts) > 1 and parts[1].isdigit():
        return mode, int(parts[1]), 0, True, False
    return mode, limit, offset, False, False


def _review_region(mode: str) -> str:
    return "AU" if mode.endswith("-au") or mode == "au" else "GB"


def _trade_review_target(page: ParsedPage, row_number: int) -> tuple[str, str] | None:
    if row_number < 1 or row_number > len(page.rows):
        return None
    row = dict(zip(page.columns, page.rows[row_number - 1], strict=False))
    venue = row.get("venue", "").strip()
    bucket_key = (row.get("bucket_key") or row.get("best_bucket_key") or "ALL").strip() or "ALL"
    if not venue:
        return None
    return venue, bucket_key


def loop(console: Console, *, initial_mode: str = "gb", initial_limit: int = 20, initial_offset: int = 0) -> None:
    mode = initial_mode if initial_mode in MODE_KEYS else "gb"
    limit = initial_limit
    offset = initial_offset
    page: ParsedPage | None = None
    note: str | None = "Choose a view, or press r to load the default GB venue totals. Pages are cached locally after first load."
    while True:
        render(console, mode=mode, limit=limit, offset=offset, page=page, note=note)
        note = None
        try:
            command = console.input(f"[bold {palette.ACCENT_MERCURY}]venue-buckets[/] > ").strip().lower()
        except EOFError:
            return
        if command in {"", "b", "back", "q", "quit", "exit"}:
            return
        trade_match = re.fullmatch(r"(?:t|trade)\s*(\d+)", command)
        if trade_match and page is not None:
            target = _trade_review_target(page, int(trade_match.group(1)))
            if target is None:
                note = f"trade row not on this page: {trade_match.group(1)}"
                continue
            from .bucket_review import loop as bucket_review_loop

            venue, bucket_key = target
            bucket_review_loop(console, initial_region=_review_region(mode), initial_venue=venue, initial_bucket_key=bucket_key)
            continue
        try:
            next_mode, next_limit, next_offset, should_fetch, force_remote = _parse_command(command, mode=mode, limit=limit, offset=offset)
        except ValueError:
            note = f"invalid command: {command}"
            continue
        if not should_fetch:
            note = f"unknown command: {command}"
            continue
        mode, limit, offset = next_mode, next_limit, next_offset
        try:
            path = cache_path(mode, limit, offset)
            if not path.exists() or force_remote:
                render_loading(console, mode=mode, limit=limit, offset=offset)
            page = fetch_page(mode, limit, offset, force_remote=force_remote)
        except Exception as exc:
            page = None
            note = f"load failed: {exc}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="STARGATE PriceSEER venue bucket TUI")
    parser.add_argument("--mode", default="gb", choices=sorted(MODE_KEYS))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--offset", type=int, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console()
    loop(console, initial_mode=args.mode, initial_limit=args.limit, initial_offset=args.offset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
