# StarMail v3 Shell Contract

Owner:

- Mercury

Authority:

- Mercury is the in-lane authority for STARGATE StarMail and attached gateway-service behavior.
- Euclid or Odin may invoke Mercury through higher directives.
- Mercury owns the lane implementation posture once invoked unless the user explicitly overrides it.

## Purpose

StarMail v3 is the local governed mail and diagnostics surface for Epoch 3.

It should support future orchestration across PriceMESH, PriceSEER, and PriceLIVE/Animal without waking agents for low-value noise.

## Priority Classes

| Class | Meaning | Wake API/agent |
| --- | --- | --- |
| WAKE | immediate current-path action required | yes |
| QUEUE | actionable but not urgent | no by default |
| MONITOR | visible but not actionable | no |
| ARCHIVE | resolved/stale/duplicate/history | no |

## Required Mail Fields

- thread id
- source system
- target owner
- priority
- status
- fault code
- current-path or historical
- created at
- updated at
- action requested
- latest disposition

## Initial State

The v3 shell is a placeholder only. No StarMail service is restarted by this repo yet.

Before service restart work begins, Mercury must provide:

- storage path
- process command
- port if any
- restart procedure
- migration plan
- rollback procedure
