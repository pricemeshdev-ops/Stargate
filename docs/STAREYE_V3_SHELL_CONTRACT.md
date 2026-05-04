# StarEye v3 Shell Contract

Owner:

- Mercury for shell behavior
- source repo owner for data adapter

## Purpose

StarEye v3 is a read-only market replay and trade-forensics shell.

It must default to the book replay view, not the event console.

## Required Views

| Key | View |
| --- | --- |
| 1 / b | book replay |
| 2 | selected ladder |
| 3 / e | event console |
| 4 | flow / volume |
| 5 | model overlay |

## Book View Requirements

Always visible at normal font size:

- replay state strip
- runner book
- selected runner ladder
- compact event tape
- command dock

## Navigation Requirements

- `q` from an inspection view returns to book replay
- `q` from book replay exits StarEye
- mouse wheel may move frames in single-view forensic pages when implemented
- replay must not snap the terminal to the bottom on every frame

## Non-Execution Rule

StarEye is read-only. It must not place orders or expose order-entry controls.

