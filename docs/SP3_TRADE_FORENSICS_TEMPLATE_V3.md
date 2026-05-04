# SP3 Trade Forensics Template for STARGATE v3

## Purpose

This template preserves the useful SP3 trade-forensics shape without binding STARGATE v3 to Epoch 2 runtime logic.

It is a view contract for future Animal/PriceSEER/StarEye integration.

## Required Header

```text
TRADE FORENSICS
market <market_id> | venue <venue> | off <off_time> | side <BACK/LAY>
runner <runner_name> | selection <selection_id>
state <dna/state> | status <SHELL/LIVE/SETTLED>
```

## Required Execution Signature

```text
entry <price> | SP <sp> | side <BACK/LAY> | DNA <state_code>
clips <n> | volume <stake_or_liability> | p/l <measured> | trace <frames>
```

## Required Price Path Bands

The chart must preserve:

- fire marker
- SP/off marker
- favourable direction
- adverse direction
- clip markers
- hold/action markers
- visible valid-frame strip

For default rendering, coloured path boxes should be visible without requiring terminal text selection.

## Required Frame Tape Columns

Minimum frame tape:

| Column | Meaning |
| --- | --- |
| time | frame timestamp |
| t+fire | relative to selected fire |
| t-off | relative to off |
| price | frame price |
| ltp | last traded price |
| favtk | favourite tick relationship |
| rank | runner rank |
| spr | spread |
| touch | touch liquidity |
| d3 | depth 3 |
| d10 | depth 10 |
| dir | direction score |
| cap | capacity score |
| sig | signal score |
| action | FIRE/HOLD/ABSTAIN |
| dna | state code |
| state | expanded state name |

## Required Interpretation Blocks

Each forensics view should include:

- what fired
- what abstained
- best fill
- worst fill
- selected runner rank versus favourite/second favourite
- same-market competing candidates
- why this row was selected or rejected

## Non-Execution Rule

This is a replay and evidence surface. It must not submit orders.

