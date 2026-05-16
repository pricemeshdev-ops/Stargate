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

## Terminal Launch Geometry

Every ORG terminal surface must declare whether it is:

- `fixed`: designed for a specific terminal geometry
- `responsive`: designed to use the current terminal or full-screen space
- `embedded`: designed to render inside an already-open parent shell

Desktop shortcuts and launch scripts must open fixed-size TUIs at their designed geometry instead of relying on the desktop environment default terminal size.

Current fixed geometries:

| Surface | Launcher | Geometry |
| --- | --- | --- |
| STARGATE Gateway | `scripts/open-stargate-gateway` | `160x44` |
| StarMail | `scripts/open-starmail` | `132x38` |

Direct scripts such as `scripts/stargate` and `scripts/starmail` may still render inside the current terminal for development and tests.

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
