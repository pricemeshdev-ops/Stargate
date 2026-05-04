# STARGATE v3.0

Blank Epoch 3 local gateway boilerplate for the AA Stargate launcher.

Canonical local path:

- `/home/user/AA-SG-LAUNCHER/STARGATE`

GitHub target:

- `git@github-stargate:pricemeshdev-ops/Stargate.git`

## Purpose

STARGATE v3.0 is the local user shell for whole-organisation orchestration telemetry across PriceMESH, PriceSEER, and PriceLIVE/Animal.

It is intentionally blank at launch: no live data access, no runtime mutation, no order execution, and no production service control.

It provides repo-ready templates and TUI placeholders for:

- Main Gateway
- StarMail
- StarEye
- Pipeline
- Animal Live
- Animal Reports
- PriceSEER
- PriceMESH
- Blog Library
- Epoch 2 Legacy Gateway handoff

## Organisation Role

The operator should be able to enter one local CLI and see or route the whole organisation:

- PriceMESH: upstream truth, feed state, runtime publication, and source governance
- PriceSEER: modelling, datasets, research reports, and supervisor signoff surfaces
- PriceLIVE/Animal: live shadow telemetry, result ledgers, and future live-key observation
- StarMail: governed mail, diagnostics, wake/queue/monitor routing, and agent coordination
- StarEye: read-only market replay and trade-forensics inspection
- Pipeline: cross-system board-truth telemetry
- Blog Library: research narrative and doctrine history

STARGATE is the local shell that glues these surfaces together for the user. It is not the authority of record for PriceMESH, PriceSEER, or PriceLIVE data.

## Boundary

The existing Epoch 2 STARGATE library remains saved and locked at:

- `/home/user/PriceSEER`

Do not mutate that checkout from this repo. Use it as a reference only.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
stargate
```

Direct shells:

```bash
stargate-starmail
stargate-stareye
stargate-pipeline
```

## Design Posture

The shell keeps the v2 visual grammar:

- command-first TUI
- cyan framed panels
- section accents
- concise command dock
- fixed-width terminal composition for trading views
- no hidden live side effects

Mercury is the in-lane authority for STARGATE and its attached services. Higher directives may invoke Mercury, but Mercury owns the gateway lane once invoked: StarMail, diagnostics, shell behavior, service templates, and future restart procedures.
