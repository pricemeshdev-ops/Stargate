# Pipeline v3 Shell Contract

## Purpose

Pipeline v3 is the cross-organisation board-truth telemetry shell.

It should eventually present PriceMESH, PriceSEER, PriceLIVE/Animal, and StarMail state from one operator surface.

## Board Truth Rule

Health labels certify board freshness and accuracy, not business success.

Recommended labels:

- CERTIFIED
- WARN
- STALE
- FAIL
- SHELL
- LOCKED

## Required Columns

Minimum:

- system/lane
- phase
- input
- processing
- processing age band
- pass
- fault
- fail
- fail age band
- truth

## Initial State

All rows are shell placeholders. No live source is attached.

## Future Source Rule

Every live row must declare:

- source repo
- source artifact or API
- timestamp field
- owner
- freshness threshold
- failure semantics

