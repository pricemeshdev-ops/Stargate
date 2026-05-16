# E3I-0001 Report And TUI Contract

Owner: Mercury / STARGATE

Data authority: PriceLIVE / Animal

Research authority: Euclid

Execution authority: Anubis / Animal gated process

Lucy gate: required before promotion beyond paper/shadow reporting

Mode: terminal reporting and shell design contract

## Purpose

This contract parses Euclid's E3I-0001 handoff into the report structure Mercury must use in the STARGATE shell and the Animal trade execution terminal.

The launch surface is not a generic dashboard. It is an operator-grade terminal view for watching whether live-computable states recover the Epoch 2 `R2P1E5` / `R2P2E5` clean-trade family.

## Reference Lineage

Mercury must carry forward:

- `STARGATE/docs/TUI_STYLE_CONTRACT_V3.md`
- `STARGATE/docs/SP3_TRADE_FORENSICS_TEMPLATE_V3.md`
- `STARGATE/docs/templates/animal_report.md`
- `agent-org/knowledge/stargate-engineering/PRICEORG_TUI_STANDARD.md`
- `agent-org/knowledge/stargate-engineering/EPOCH2_TUI_REFERENCE_BANK.md`

Patterns inherited from Epoch 2:

- command-first terminal operation
- black terminal base with cyan STARGATE frame identity
- fixed-width forensic tables
- source, owner, state, freshness, and certification labels
- visible command dock
- compact panes over card-heavy dashboards
- post-event SP labels kept out of decision-time panes

## Canonical Report Source

Animal emits the source evidence. Mercury displays it.

Primary local command:

```text
npm run animalctl -- e3i-report --json --scan-limit 50000
```

Readable fallback commands:

```text
npm run animalctl -- e3i-report --scan-limit 50000
npm run animalctl -- animal-results --all --limit 120
npm run animalctl -- animal-shape --event-id <id>
npm run animalctl -- animal-shape --market-id <market_id>
```

Telemetry source:

```text
/snapshot
/events
```

Mercury must not treat STARGATE as data truth. If Animal telemetry is stale, missing, delayed, uncertified, or blocked, the TUI must show that state directly.

## Authority Header

The Animal terminal and STARGATE shell must expose:

```text
SHELL_OWNER Mercury/STARGATE
DATA_AUTHORITY PriceLIVE/Animal
INTERPRETATION_AUTHORITY Euclid/PriceSEER for research labels, Anubis for execution safety
CANONICAL_SOURCE Azure SSE telemetry + Animal event spine
EVIDENCE_SOURCE /events + /snapshot + animalctl e3i-report
EXECUTION_AUTHORITY NONE in paper/shadow reporting mode
CERTIFICATION NOT_CERTIFIED until Lucy/Anubis gate passes
ALLOWED read telemetry, save packet, open read-only ledgers
BLOCKED orders, Betfair login, secret inspection, service control
```

## E3I Event Vocabulary

Mercury must use the same event levels in every shell:

| Level | Animal Event | Meaning |
| --- | --- | --- |
| `STATE_OBSERVED` | `shadow.animal_signal_fire` and `shadow.animal_signal_abstain` | decision-time state evidence |
| `ENTRY_CANDIDATE` | `shadow.animal_signal_fire` | state crossed the E3I threshold |
| `SELECTED_ENTRY` | `shadow.animal_trade_entry` | market-throttled paper/shadow selected entry |
| `BLOCKED_ENTRY` | `shadow.animal_trade_blocked` | candidate rejected by selector, safety, or state rule |
| `SETTLED_LABEL` | `shadow.animal_trade_settled` | post-event SP outcome label |

Do not label every true state as an entry. Candidate and selected entry are separate concepts.

## Required TUI Panes

### 1. Header / Gate Strip

Show policy id, mode, source class, stream owner, key class, telemetry status, execution status, certification, and blocked actions.

Required labels:

```text
policy E3I-0001_R2P1P2E5_ENTRY_PATH_SHADOW
mode paper_shadow_reporting
source live|delayed|unknown
exec NONE|STALE|HOLD|DANGER
cert NOT_CERTIFIED
```

### 2. Schedule / Market Surface

Shows Flumine or producer schedule:

```text
#  market_id  geo  venue  off  t-off  runners  status
```

This pane is for choosing inspection targets. It is not an order surface.

### 3. Active Participation

Shows selected entries and blocked candidates, not every raw state row.

Minimum columns:

```text
# time event side DNA runner t-off entry stake d3 SP/PnL state
```

Event codes:

```text
A_FIRE    candidate
A_ENTRY   selected paper/shadow entry
A_BLOCK   blocked candidate
A_SETTLED post-event SP label
```

### 4. Latest Participant Detail

Shows one selected or blocked row:

```text
event id
market / runner / venue / off
side / entry
DNA P/F/C/D
fill mode and depth
book back/lay/spread
capacity touch/D3/D10
contract hash / snapshot hash / no-order proof
state key and scores
reason or block reason
```

SP and P/L may appear only when the event is settled or explicitly post-event.

### 5. Priority Slice Board

The report shell must show Euclid's launch slices:

```text
P0 GB_LAY_P1P2_F1F2_DRIFT_CORE
P1 AU_BACK_P2_F1F2_STEAM_CORE
P2 AU_BACK_P1_EXCLUSION_WATCH
P3 AU_LAY_CONTROL_WATCH
P4 GB_BACK_CONTROL_WATCH
P9 OTHER_OBSERVE
```

Minimum columns:

```text
priority slice candidate selected blocked settled markets runners volume pnl hit latest
```

This is a diagnostic board. It must not claim edge or profitability without PriceSEER evidence.

### 6. Runtime / Counters

Show fast telemetry:

```text
stream age
market stream
order stream
auth
Flumine status
schedule active count
transaction guard
unknown orders
no-order proof
max selected entries per market
capacity harvest mode
```

Transaction charge and failed-transaction counters must remain visible before any live promotion.

### 7. Result / SP Tracker

Shows post-event labels:

```text
market venue runner side DNA clip stake entry SP ticks P/L result state
```

This pane is outcome evidence, not decision evidence.

### 8. Forensic Drilldown

`animal-shape --event-id <id>` and `animal-shape --market-id <market>` keep the SP3-style forensic shape:

- execution signature
- clip table
- frame tape
- market participants
- blocked competitors
- SP outcome labels

### 9. Betfair Links And Optional Exchange Graph Overlay

Mercury should not rebuild Betfair's graph as the first implementation. The fastest useful operator path is direct read-only links from the terminal to the official Betfair market and runner graph, while the Animal terminal remains the evidence authority for paper/shadow state and decisions.

Phase 1 direct links:

```text
exchange market page: https://www.betfair.com.au/exchange/plus/horse-racing/market/<market_id>
runner graph page:    https://graphs.betfair.com.au/<market_id>/<selection_id>/0
```

The terminal should expose these as read-only operator commands when `market_id` and `selection_id` are known:

```text
open Betfair market
open Betfair runner graph
```

The link surface must not scrape Betfair, automate betting UI actions, submit orders, inspect browser state, or imply Betfair is the PRICEORG evidence source. Betfair links are human inspection aids only.

Animal remains the canonical source for:

```text
state observed
abstain reason
candidate / selected / blocked / settled event
paper/shadow entry label
frame count and source freshness
SP/P&L outcome label after settlement
```

Phase 2, only if needed, may add an internal graph overlay. That pane is for operator forensics and live paper/shadow observation, not order entry.

Required surfaces:

```text
price / volume over time
runner selector
current ladder by price
available to back
available to lay
traded volume by price
paper/shadow event overlay
```

Overlay markers:

```text
STATE_OBSERVED
ENTRY_CANDIDATE
SELECTED_ENTRY
BLOCKED_ENTRY
SETTLED_LABEL
```

The overlay must show Animal's paper/shadow side, entry price, simulated stake or capacity depth, state key, signal/capacity/direction scores, and event id. SP, settlement, and P/L may appear only after the event is settled and must be visually marked as post-event.

Decision-time graph panes must not include hindsight fields. The operator must be able to compare "what Animal knew then" against "what happened later" without mixing the two.

Data authority remains Animal:

```text
/events
/snapshot
animalctl e3i-report
animalctl animal-shape --event-id <id>
animalctl animal-shape --market-id <market_id>
```

This is a future Mercury / STARGATE development item. It must not add cash execution authority, Betfair login, secret access, service control, or order controls.

## Command Dock

Visible commands:

```text
q quit
r reconnect/refresh telemetry
p save telemetry packet
m/m# market ledger
s/s# result trace
j/k select
1-9 select row
```

Rules:

- every listed command must work or show a clear blocker
- no hidden mouse-only commands
- no order, Betfair login, secret, start service, stop service, arm, or halt command in this read-only terminal
- future mutating commands require dry-run, explicit scope, confirm token, audit artifact, and Lucy/Anubis gate

## Layout Gate

Default target: full-screen terminal at approximately `180x50`.

Required snapshot coverage before any larger rewrite:

```text
80x24
120x40
180x50
missing telemetry
stale telemetry
live stream connected
blocked candidate
selected entry
settled SP label
exchange graph and paper/shadow overlay
```

## PASS / FAIL

PASS:

```text
Mercury uses the Epoch 2 terminal grammar.
The same E3I report fields drive STARGATE and the Animal terminal.
The priority slice board is visible.
Candidate, selected, blocked, and settled labels are distinct.
SP/P&L are post-event labels only.
Blocked actions are visible.
No live execution authority is implied.
```

FAIL:

```text
The screen becomes a generic dashboard.
The command dock lists commands that do not work.
Every true state is shown as a selected entry.
STARGATE is treated as data truth.
SP or P/L appears as a decision-time feature.
The surface hides transaction guard or no-order proof.
The exchange graph mixes decision-time evidence with settlement hindsight.
Any order or service-control action appears without a gate.
```
