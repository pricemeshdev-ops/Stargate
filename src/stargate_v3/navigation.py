"""Static navigation model for the blank Epoch 3 gateway."""

from __future__ import annotations

from dataclasses import dataclass

from . import palette


@dataclass(frozen=True)
class Surface:
    key: str
    label: str
    summary: str
    status: str = "SHELL"
    owner: str = "Gateway"
    accent: str = palette.ACCENT


SURFACES: tuple[Surface, ...] = (
    Surface("a", "Animal Live", "Live shadow and execution-observation shell. No order submit.", owner="Animal", accent=palette.ACCENT_ANIMAL),
    Surface("ar", "Animal Reports", "Settled result ledgers, shaper reports, and state result libraries.", owner="Animal", accent=palette.ACCENT_ANIMAL),
    Surface("ps", "PriceSEER", "Modelling engine, datasets, feature weights, and research outputs.", owner="Odin", accent=palette.ACCENT_PSEER),
    Surface("pm", "PriceMESH", "Upstream truth, feed governance, and source health references.", owner="Samael", accent=palette.ACCENT_PMESH),
    Surface("b", "Blog Library", "Epoch 3 research articles and operator notes.", owner="Euclid", accent=palette.ACCENT_BLOG),
    Surface("x", "StarEye", "Read-only market replay shell and SP3-style forensics frame.", owner="Mercury", accent=palette.ACCENT),
    Surface("z", "StarMail", "Mailbox, diagnostic routing, wake/queue/monitor shell.", owner="Mercury", accent=palette.ACCENT),
    Surface("p", "Pipeline", "Blank Epoch 3 pipeline board shell.", owner="Odin", accent=palette.ACCENT),
    Surface("e2", "Epoch 2 Legacy Gateway", "Locked handoff to saved Epoch 2 STARGATE reference.", status="LOCKED", owner="Legacy", accent=palette.DIM),
)


def surface_by_key(key: str) -> Surface | None:
    normalized = key.strip().lower()
    return next((surface for surface in SURFACES if surface.key == normalized), None)

