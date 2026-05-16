"""Build local offline caches for STARGATE report/table review."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from .. import palette
from ..report_archive import reports_for_node
from .venue_buckets import MODE_KEYS, cache_path as venue_cache_path, fetch_page

STARGATE_ROOT = Path(__file__).resolve().parents[3]
ORG_ROOT = STARGATE_ROOT.parent
PACK_ROOT = STARGATE_ROOT / "runtime" / "cache" / "flight_pack"


def _load_json_list(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def cache_reports(console: Console, *, node: str = "pseer") -> list[dict[str, str]]:
    report_root = PACK_ROOT / "reports" / node
    report_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []
    for report in reports_for_node(node):
        source = Path(report.source_path)
        target = report_root / f"{report.report_id}.md"
        status = "missing"
        if source.exists():
            shutil.copy2(source, target)
            status = "cached"
        manifest.append(
            {
                "id": report.report_id,
                "title": report.title,
                "status": status,
                "source": str(source),
                "cache": str(target),
                "boundary": report.boundary,
            }
        )
        console.print(f"report {status}: {report.title}", style=palette.MUTED if status == "cached" else palette.ACCENT_WARN)
    (report_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def cache_venue_tables(console: Console, *, limit: int = 20, force_remote: bool = False) -> list[dict[str, object]]:
    table_root = PACK_ROOT / "venue_tables"
    table_root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    for mode in sorted(MODE_KEYS):
        first = fetch_page(mode, limit, 0, force_remote=force_remote)
        total = first.rows_total or 0
        pages = 0
        for offset in range(0, total, limit):
            path = venue_cache_path(mode, limit, offset)
            page = fetch_page(mode, limit, offset, force_remote=force_remote)
            pages += 1
            console.print(
                f"table {mode}: rows {page.start or 0}-{page.end or 0}/{page.rows_total or 0} -> {path}",
                style=palette.MUTED,
            )
        manifest.append({"mode": mode, "rows": total, "pages": pages, "limit": limit})
    (table_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def write_manifest(*, reports: list[dict[str, str]], tables: list[dict[str, object]]) -> Path:
    PACK_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root": str(PACK_ROOT),
        "reports": reports,
        "venue_tables": tables,
        "boundaries": [
            "Read-only offline recall cache.",
            "No Animal shadow, Betfair connection, live orders, service control, or cash execution.",
            "Trade trace packs are raw-DAP reconstructions cached under STARGATE/runtime/cache/trade_trace_forensics when opened or packed.",
        ],
    }
    path = PACK_ROOT / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cache STARGATE reports and tables for offline flight review.")
    parser.add_argument("--reports-only", action="store_true", help="cache report markdown only")
    parser.add_argument("--tables-only", action="store_true", help="cache venue/table pages only")
    parser.add_argument("--limit", type=int, default=20, help="venue table rows per cached page")
    parser.add_argument("--force-remote", action="store_true", help="refresh table pages from Azure")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console()
    PACK_ROOT.mkdir(parents=True, exist_ok=True)
    reports: list[dict[str, object]] = []
    tables: list[dict[str, object]] = []
    if not args.tables_only:
        reports = cache_reports(console)
    else:
        reports = _load_json_list(PACK_ROOT / "reports" / "pseer" / "manifest.json")
    if not args.reports_only:
        tables = cache_venue_tables(console, limit=args.limit, force_remote=args.force_remote)
    else:
        tables = _load_json_list(PACK_ROOT / "venue_tables" / "manifest.json")
    manifest = write_manifest(reports=reports, tables=tables)
    console.print(f"flight pack manifest: {manifest}", style=palette.GOOD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
