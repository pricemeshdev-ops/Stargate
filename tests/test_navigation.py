from pathlib import Path

from stargate_v3.identity import (
    IDENTITY_MARK_NAME,
    ORG_IDENTITIES,
    RUNTIME_FLOW,
    RUNTIME_FLOW_INTERPRETATION,
    TOPOLOGY_STAGES,
)
from stargate_v3.navigation import ORG_SURFACE_KEYS, SURFACES, surface_by_key
from stargate_v3.report_archive import DEFAULT_REPORT_ARCHIVE_PATH, REQUIRED_STATE_MEMORY_PRIMITIVES, reports_for_node
from rich.console import Console

from stargate_v3.shells.reports import render as render_reports, render_report
from stargate_v3.shells.starmail import DRAFT_PACKETS, render as render_starmail
from stargate_v3.shells.bucket_review import parse_trade_page, render as render_bucket_review
from stargate_v3.shells.pseer_boards import render as render_pseer_boards
from stargate_v3.shells.trace_forensics import parse_trace_pack, render as render_trace_forensics
from stargate_v3.shells.venue_buckets import parse_page, render as render_venue_buckets
from stargate_v3.starmail_store import archive_packet, load_or_seed_packets, seed_packets, write_packets
from stargate_v3.app import ANIMAL_ROOT, animal_node_panel

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_core_surfaces_are_present():
    keys = {surface.key for surface in SURFACES}
    assert {"a", "ar", "ps", "pm", "b", "x", "z", "p", "e2"} <= keys


def test_epoch3_org_identities_are_present():
    owners = {identity.owner for identity in ORG_IDENTITIES}
    assert {"USER", "LUCY", "ANUBIS", "SAMAEL", "ODIN", "EUCLID", "MERCURY"} == owners
    assert {"u", "lu", "an", "sa", "od", "eu", "me"} == set(ORG_SURFACE_KEYS)
    assert all(surface_by_key(key).status == "SHELL" for key in ORG_SURFACE_KEYS)
    assert RUNTIME_FLOW == "LIVE / MESH / SEER / ORG"
    assert RUNTIME_FLOW_INTERPRETATION == "gateway shell"
    assert IDENTITY_MARK_NAME == "red inverted pentagram"


def test_epoch3_runtime_topology_owners_are_present():
    stages = {stage.label: stage for stage in TOPOLOGY_STAGES}
    assert tuple(stage.label for stage in TOPOLOGY_STAGES) == ("LIVE", "MESH", "SEER", "ORG")
    assert stages["LIVE"].owner == "ANUBIS"
    assert stages["MESH"].owner == "SAMAEL"
    assert stages["SEER"].owner == "ODIN"
    assert stages["ORG"].owner == "LUCY"


def test_epoch2_is_locked_reference():
    surface = surface_by_key("e2")
    assert surface is not None
    assert surface.status == "LOCKED"


def test_mercury_surface_is_shell_only():
    surface = surface_by_key("me")
    assert surface is not None
    assert surface.owner == "MERCURY"
    assert surface.status == "SHELL"


def test_desktop_portal_assets_are_local_shell_launchers():
    icon = REPO_ROOT / "assets" / "stargate-v3-red-inverted-pentagram.svg"
    portal = REPO_ROOT / "desktop" / "stargate-v3.desktop"
    starmail = REPO_ROOT / "desktop" / "stargate-v3-starmail.desktop"

    assert icon.exists()
    for entry, command in ((portal, "scripts/open-stargate-gateway"), (starmail, "scripts/open-starmail")):
        text = entry.read_text(encoding="utf-8")
        assert "Terminal=false" in text
        assert str(icon) in text
        assert str(REPO_ROOT / command) in text
    assert "Name=STARGATE v3 Gateway" in portal.read_text(encoding="utf-8")


def test_fixed_terminal_openers_declare_geometry():
    gateway = (REPO_ROOT / "scripts" / "open-stargate-gateway").read_text(encoding="utf-8")
    starmail = (REPO_ROOT / "scripts" / "open-starmail").read_text(encoding="utf-8")
    assert "160x44" in gateway
    assert "132x38" in starmail
    assert "gnome-terminal --geometry" in gateway
    assert "gnome-terminal --geometry" in starmail


def test_animal_node_explicit_console_launchers_are_present():
    assert (ANIMAL_ROOT / "scripts" / "open_animal_azure_tunnel_console.sh").exists()
    assert (ANIMAL_ROOT / "scripts" / "open_animal_gateway.sh").exists()
    panel = animal_node_panel()
    assert panel.title == "Animal Node // explicit consoles"


def test_stargate_gateway_exposes_animal_server_and_trade_commands():
    app = (REPO_ROOT / "src" / "stargate_v3" / "app.py").read_text(encoding="utf-8")
    assert "as animal server console" in app
    assert "at animal trade terminal" in app
    assert "open_animal_tunnel_console" in app
    assert "ps pseer reports" in app
    assert "pb pseer boards" in app
    assert "vb venue buckets" in app
    assert "br bucket review" in app


def test_starmail_draft_packets_are_operator_facing():
    statuses = {packet.status for packet in DRAFT_PACKETS}
    owners = {packet.target_owner for packet in DRAFT_PACKETS}
    assert {"MERCURY", "LUCY", "ANUBIS"} <= owners
    assert "SHELL" not in statuses
    assert all(packet.subject for packet in DRAFT_PACKETS)


def test_starmail_local_store_seeds_and_archives(tmp_path):
    store = tmp_path / "packets.json"
    packets = load_or_seed_packets(store)
    assert store.exists()
    assert {packet.packet_id for packet in packets} >= {"M-001", "L-001", "A-001"}
    assert {packet.execution_authority for packet in packets} == {"NONE"}

    archived = archive_packet("A-001", store)
    assert archived.status == "ARCHIVED"
    reloaded = {packet.packet_id: packet for packet in load_or_seed_packets(store)}
    assert reloaded["A-001"].status == "ARCHIVED"


def test_starmail_render_does_not_create_store(tmp_path):
    store = tmp_path / "packets.json"
    console = Console(file=open("/dev/null", "w", encoding="utf-8"), force_terminal=False)
    try:
        render_starmail(console, store_path=store)
    finally:
        console.file.close()
    assert not store.exists()


def test_starmail_store_rejects_execution_authority(tmp_path):
    store = tmp_path / "packets.json"
    packet = seed_packets()[0]
    unsafe = type(packet)(**{**packet.__dict__, "execution_authority": "LIVE"})
    try:
        write_packets([unsafe], store)
    except ValueError as exc:
        assert "cannot grant execution authority" in str(exc)
    else:
        raise AssertionError("unsafe StarMail packet was accepted")


def test_report_archive_has_node_buckets_and_euclid_pseer_report():
    assert DEFAULT_REPORT_ARCHIVE_PATH.exists()
    reports = reports_for_node("pseer")
    assert len(reports) >= 1
    report_by_id = {report.report_id: report for report in reports}
    report = report_by_id["PSEER-EUCLID-E3-OPENING-BACKTEST-STATE-MEMORY-2026-05-06"]
    assert report.author == "Euclid"
    assert report.node == "PriceSEER"
    assert "State Memory" in report.title
    assert tuple(report.required_state_memory) == REQUIRED_STATE_MEMORY_PRIMITIVES
    sp3_report = report_by_id["PSEER-EUCLID-E3-SP3-RAW-STREAM-FORENSICS-2026-05-11"]
    assert sp3_report.node == "PriceSEER"
    assert "SP3 Raw Stream Forensics" in sp3_report.title
    baseline_report = report_by_id["PSEER-EUCLID-BASELINE-250-DAILY-STRATEGY-V1-2026-05-11"]
    assert baseline_report.node == "PriceSEER"
    assert "BASELINE 250" in baseline_report.title
    venue_report = report_by_id["PSEER-EUCLID-AU-GB-VENUE-DISTRIBUTION-V1-2026-05-12"]
    assert venue_report.node == "PriceSEER"
    assert "Venue Distribution" in venue_report.title
    assert "positive/flat/negative" in venue_report.summary
    pager_report = report_by_id["PSEER-EUCLID-AU-GB-FULL-VENUE-BUCKET-TABLES-V1-2026-05-12"]
    assert pager_report.node == "PriceSEER"
    assert "Full Venue Bucket Tables" in pager_report.title
    assert "positive/flat/negative" in pager_report.summary
    assert pager_report.status == "TUI_LINKED_CACHE_AWARE"
    value_report = report_by_id["PSEER-EUCLID-DAY3-MAIN-VALUE-INDEX-2026-05-14"]
    assert value_report.node == "PriceSEER"
    assert "Value Index" in value_report.title
    assert value_report.status == "ACTIVE_VALUE_CONTROL"
    registry_report = report_by_id["PSEER-EUCLID-DAY3-ANALYST-BOARD-REGISTRY-V1-2026-05-14"]
    assert registry_report.node == "PriceSEER"
    assert "Board Registry" in registry_report.title
    agent_reports = reports_for_node("agent-org")
    agent_report_by_id = {report.report_id: report for report in agent_reports}
    directive = agent_report_by_id["ORG-LUCY-30-DAY-VIABILITY-MANDATE-2026-05-11"]
    assert directive.node == "agent-org"
    assert "30-Day Viability" in directive.title
    for node in ("animal", "pricemesh", "stargate"):
        assert reports_for_node(node) == ()


def test_report_archive_render_is_read_only_and_operator_visible(tmp_path):
    output = tmp_path / "reports.txt"
    with output.open("w", encoding="utf-8") as handle:
        console = Console(file=handle, force_terminal=False, width=160)
        render_reports(console, node_key="pseer")
    rendered = output.read_text(encoding="utf-8")
    assert "PSEER REPORTS" in rendered
    assert "Euclid" in rendered
    assert "30s/60s/120s price velocity" in rendered
    assert "STARGATE is the recall shell only" in rendered
    assert "# open report" in rendered


def test_report_archive_can_render_selected_report(tmp_path):
    output = tmp_path / "report_detail.txt"
    with output.open("w", encoding="utf-8") as handle:
        console = Console(file=handle, force_terminal=False, width=160)
        render_report(console, 2, node_key="pseer")
    rendered = output.read_text(encoding="utf-8")
    assert "Epoch 3 SP3 Raw Stream Forensics" in rendered
    assert "SP3 Objective" in rendered
    assert "Replay/model report only" in rendered


def test_venue_bucket_tui_renders_navigation_without_fetch(tmp_path):
    output = tmp_path / "venue_buckets.txt"
    with output.open("w", encoding="utf-8") as handle:
        console = Console(file=handle, force_terminal=False, width=160)
        render_venue_buckets(console)
    rendered = output.read_text(encoding="utf-8")
    assert "AU / GB VENUE BUCKET TABLES" in rendered
    assert "gb" in rendered
    assert "buckets-au" in rendered
    assert "No Animal shadow" in rendered


def test_pseer_board_branch_renders_value_index(tmp_path):
    output = tmp_path / "pseer_boards.txt"
    with output.open("w", encoding="utf-8") as handle:
        console = Console(file=handle, force_terminal=False, width=160)
        render_pseer_boards(console)
    rendered = output.read_text(encoding="utf-8")
    assert "PRICESEER BOARD INDEX" in rendered
    assert "AUD 250/day" in rendered
    assert "Complete April and December" in rendered


def test_venue_bucket_page_parser_keeps_positive_flat_negative_counts():
    sample = """
Enable succeeded:
[stdout]
Venue Distribution GB: /tmp/AU_GB_VENUE_DISTRIBUTION_SUMMARY.csv
GB Venue Totals
rows_total=38 | showing=1-2 | limit=2 | offset=0
next: gb 2 2
| venue | rows | markets | source_stake_turnover | sl3_pnl_5 | sl3_dist | raw_dist | source_dist | median_d3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ayr | 69 | 37 | $345.00 | $52.43 | 32/0/37 | 47/1/21 | 13/0/56 | $178.09 |
| Newcastle | 364 | 179 | $1,820.00 | $41.43 | 116/5/243 | 188/19/157 | 62/1/301 | $164.02 |
[stderr]
"""
    page = parse_page(sample, mode="gb", limit=2, offset=0)
    assert page.rows_total == 38
    assert page.next_command == "gb 2 2"
    assert page.columns[5] == "sl3_dist"
    assert page.rows[0][5] == "32/0/37"
    assert page.rows[1][7] == "62/1/301"


def test_venue_bucket_tui_split_bands_keep_values_readable(tmp_path):
    sample = """
Venue Distribution GB: /tmp/AU_GB_VENUE_DISTRIBUTION_SUMMARY.csv
GB Venue Totals
rows_total=38 | showing=1-2 | limit=2 | offset=0
next: gb 2 2
| venue | rows | markets | source_stake_turnover | sl3_pnl_5 | sl3_dist | raw_dist | source_dist | sl3_gross_pos | sl3_gross_neg | sl3_avg_win | sl3_avg_loss | median_d3 | median_d10 | false_stopped_winner_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Newcastle | 364 | 179 | $1,820.00 | $41.43 | 116/5/243 | 188/19/157 | 62/1/301 | $135.72 | $-94.29 | 1.170024 | -0.388023 | $164.02 | $405.12 | 19.8% |
"""
    page = parse_page(sample, mode="gb", limit=2, offset=0)
    output = tmp_path / "venue_bucket_page.txt"
    with output.open("w", encoding="utf-8") as handle:
        console = Console(file=handle, force_terminal=False, width=120)
        render_venue_buckets(console, page=page)
    rendered = output.read_text(encoding="utf-8")
    assert "Rows are split into bands" in rendered
    assert "wins / flat / losses" in rendered
    assert "SL3 Gross Wins" in rendered
    assert "Newcastle" in rendered
    assert "$1,820.00" in rendered
    assert "188/19/157" in rendered
    assert "$405.12" in rendered


def test_bucket_review_trade_page_parser_preserves_trace_ready_fields():
    sample = """
Enable succeeded:
[stdout]
Bucket Trade Review GB Newcastle ALL
source=/srv/priceseer/data/reports/epoch3_recalibration_v1/run_epoch3_baseline250_win_20260511T100000Z/baseline_250_signal_trades.csv
boundary=TRACE_FETCH_READY; detail rows can be reconstructed from raw DAP source_frame_part when cached locally
rows_total=364 | showing=1-2 | limit=2 | offset=0 | sort=off
next: trades GB Newcastle ALL 2 2 off
| row | date | market_id | selection_id | venue | runner | off | side | dna | bucket_key | time_band | entry | sp | ticks | raw_pnl_5 | paper_pnl | trace | cap | touch | d3 | d10 | spread | path | source_frame | entry_ts | frame_index | seconds_to_off |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-03-31 | 1.257000 | 123 | Newcastle | Runner One | 2026-03-31 14:00:00Z | BACK | P1F1C5D3 | Sat/Saturday/T300_390/R2P1/F1/P1/CAP_DEEP/DIR_EDGE | T300_390 | 4.4 | 3.45 | 15 | $1.38 | $5.00 | -2/1.37/15/4 | 220 | 55 | 178 | 405 | 2 | STEAM_HELD_TO_SP | PRO/2026/Mar/31/file.bz2 | 2026-03-31T13:55:00Z | 42 | 300 |
[stderr]
"""
    page = parse_trade_page(sample, region="GB", venue="Newcastle", bucket_key="ALL", limit=2, offset=0, sort="off")
    assert page.rows_total == 364
    assert page.next_command == "trades GB Newcastle ALL 2 2 off"
    assert page.boundary.startswith("TRACE_FETCH_READY")
    assert page.rows[0][9] == "Sat/Saturday/T300_390/R2P1/F1/P1/CAP_DEEP/DIR_EDGE"
    assert "entry_ts" in page.columns


def test_bucket_review_renders_trace_ready_detail_copy(tmp_path):
    sample = """
Bucket Trade Review GB Newcastle ALL
source=/srv/priceseer/data/reports/epoch3_recalibration_v1/run_epoch3_baseline250_win_20260511T100000Z/baseline_250_signal_trades.csv
boundary=TRACE_FETCH_READY; detail rows can be reconstructed from raw DAP source_frame_part when cached locally
rows_total=1 | showing=1-1 | limit=1 | offset=0 | sort=off
| row | date | market_id | selection_id | venue | runner | off | side | dna | bucket_key | time_band | entry | sp | ticks | raw_pnl_5 | paper_pnl | trace | cap | touch | d3 | d10 | spread | path | source_frame | entry_ts | frame_index | seconds_to_off |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-03-31 | 1.257000 | 123 | Newcastle | Runner One | 2026-03-31 14:00:00Z | BACK | P1F1C5D3 | ALL | T300_390 | 4.4 | 3.45 | 15 | $1.38 | $5.00 | -2/1.37/15/4 | 220 | 55 | 178 | 405 | 2 | STEAM_HELD_TO_SP | PRO/2026/Mar/31/file.bz2 | 2026-03-31T13:55:00Z | 42 | 300 |
"""
    page = parse_trade_page(sample, region="GB", venue="Newcastle", bucket_key="ALL", limit=1, offset=0, sort="off")
    detail_row = dict(zip(page.columns, page.rows[0], strict=False))
    output = tmp_path / "bucket_review_detail.txt"
    with output.open("w", encoding="utf-8") as handle:
        console = Console(file=handle, force_terminal=False, width=160)
        render_bucket_review(console, region="GB", venue="Newcastle", bucket_key="ALL", page=page, detail_row=detail_row)
    rendered = output.read_text(encoding="utf-8")
    assert "Summary Trace Shape" in rendered
    assert "TRACE_FETCH_READY" in rendered
    assert "reconstruct and cache" in rendered


def test_trace_forensics_parser_and_renderer_show_full_frame_tape(tmp_path):
    sample = """
PSEER Trade Trace Forensics
boundary=FULL_FRAME_TAPE_FROM_RAW_DAP; read-only historical raw stream reconstruction; no execution authority
source_archive=/srv/priceseer/data/archive/betfair/dap/pro_thoroughbreds/raw/2026_03_ProThoroughbreds.tar
source_member=PRO/2026/Mar/31/35429426/1.256008863.bz2
raw_messages=128 | market_updates=128 | frame_interval_ms=500
trade={"entry_price": 4.4, "entry_ts": "2026-03-31T13:55:00Z", "market_id": "1.257000", "market_time": "2026-03-31T14:00:00Z", "max_adverse_ticks": -2.0, "max_favourable_ticks": 15.0, "runner": "Runner One", "selection_id": "123", "side": "BACK", "sp_final": 3.45, "sp_ticks": 15, "venue": "Newcastle"}
rows_total=2 | showing=1-2 | window=-180/+390s | max_frames=320
| frame | ts | t_fire | t_off | price | best_back | best_lay | ltp | fav_ticks | spread | touch | d3 | d10 | own_d3 | valid | clip | action | market_status | runner_status | market_total_matched | runner_total_matched | price_source | frame_ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2026-03-31T13:54:55Z | -5 | 305 | 4.50 | 4.40 | 4.50 | 4.40 | -2 | 2 | 40 | 120 | 300 | 90 | Y | - | PRE | OPEN | ACTIVE | 120000 | 4000 | contra_touch | PRO/2026/Mar/31/file.bz2#pt=1 |
| 1 | 2026-03-31T13:55:00Z | 0 | 300 | 4.40 | 4.30 | 4.40 | 4.30 | 0 | 2 | 55 | 178 | 405 | 80 | Y | E | ENTER_BACK | OPEN | ACTIVE | 121000 | 4100 | contra_touch | PRO/2026/Mar/31/file.bz2#pt=2 |
"""
    pack = parse_trace_pack(sample)
    assert pack.boundary.startswith("FULL_FRAME_TAPE_FROM_RAW_DAP")
    assert pack.trade["runner"] == "Runner One"
    assert pack.rows[1][16] == "ENTER_BACK"
    source_row = {
        "row": "1",
        "market_id": "1.257000",
        "selection_id": "123",
        "side": "BACK",
        "entry": "4.4",
        "sp": "3.45",
        "entry_ts": "2026-03-31T13:55:00Z",
        "runner": "Runner One",
        "venue": "Newcastle",
    }
    output = tmp_path / "trace_forensics.txt"
    with output.open("w", encoding="utf-8") as handle:
        console = Console(file=handle, force_terminal=False, width=180)
        render_trace_forensics(console, source_row=source_row, pack=pack)
    rendered = output.read_text(encoding="utf-8")
    assert "SP3 TRADE TRACE FORENSICS" in rendered
    assert "Execution Frame Tape" in rendered
    assert "ENTER_BACK" in rendered
    assert "FULL_FRAME_TAPE_FROM_RAW_DAP" in rendered
