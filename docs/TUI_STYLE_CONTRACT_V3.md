# STARGATE v3 TUI Style Contract

## Carry Forward From v2

Keep:

- command-first operation
- high-contrast black terminal base
- cyan STARGATE frame identity
- lane-specific accents
- compact command dock
- fixed trading-terminal widths for replay and forensic views
- explicit freshness and source labels
- no card-heavy UI or decorative layout

## Width Policy

General gateway views may center inside a maximum width of 184 columns.

Trading views must not stretch indefinitely. StarEye and trade-forensics views should preserve fixed table widths so book shape remains readable at normal terminal font size.

## Colour Semantics

| Meaning | Colour |
| --- | --- |
| Back price | cyan |
| Lay price | pink |
| favourable movement | green |
| adverse movement | red |
| warning | amber |
| hard fail | red |
| selected runner | highlighted row |
| locked legacy | dim |

## Surface Label Rule

Every surface must show:

- system
- owner
- source
- state: SHELL, LIVE, DRY_RUN, LOCKED, STALE, FAIL
- allowed actions

## Live Mutation Rule

No shell may hide a live mutation behind a normal navigation command.

Future mutating commands require:

- dry-run first
- explicit scope
- confirm token
- audit artifact

