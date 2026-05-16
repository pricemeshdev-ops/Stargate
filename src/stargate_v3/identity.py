"""STARGATE v3 identity and org topology constants."""

from __future__ import annotations

from dataclasses import dataclass

from . import palette

RUNTIME_FLOW = "LIVE / MESH / SEER / ORG"
RUNTIME_FLOW_INTERPRETATION = "gateway shell"
IDENTITY_MARK_NAME = "red inverted pentagram"

PENTAGRAM_MARK = (
    "      /\\      ",
    "  ___/  \\___  ",
    "  \\        /  ",
    "   \\  /\\  /   ",
    "    \\/  \\/    ",
)


@dataclass(frozen=True)
class OrgIdentity:
    key: str
    label: str
    owner: str
    role: str
    status: str = "SHELL"
    accent: str = palette.ACCENT


@dataclass(frozen=True)
class TopologyStage:
    key: str
    label: str
    owner: str
    contract: str
    accent: str = palette.ACCENT


TOPOLOGY_STAGES: tuple[TopologyStage, ...] = (
    TopologyStage("live", "LIVE", "ANUBIS", "PriceLIVE / Animal", accent=palette.ACCENT_ANIMAL),
    TopologyStage("mesh", "MESH", "SAMAEL", "PriceMESH", accent=palette.ACCENT_PMESH),
    TopologyStage("seer", "SEER", "ODIN", "PriceSEER", accent=palette.ACCENT_PSEER),
    TopologyStage("org", "ORG", "LUCY", "PRICEORG", accent=palette.ACCENT_LUCY),
)


ORG_IDENTITIES: tuple[OrgIdentity, ...] = (
    OrgIdentity("u", "USER", "USER", "Operator", accent=palette.ACCENT_USER),
    OrgIdentity("lu", "LUCY", "LUCY", "ORG", accent=palette.ACCENT_LUCY),
    OrgIdentity("an", "ANUBIS", "ANUBIS", "LIVE", accent=palette.ACCENT_ANIMAL),
    OrgIdentity("sa", "SAMAEL", "SAMAEL", "MESH", accent=palette.ACCENT_PMESH),
    OrgIdentity("od", "ODIN", "ODIN", "SEER", accent=palette.ACCENT_PSEER),
    OrgIdentity("eu", "EUCLID", "EUCLID", "Research", accent=palette.ACCENT_EUCLID),
    OrgIdentity("me", "MERCURY", "MERCURY", "Gateway", accent=palette.ACCENT_MERCURY),
)


def org_identity_by_key(key: str) -> OrgIdentity | None:
    normalized = key.strip().lower()
    return next((identity for identity in ORG_IDENTITIES if identity.key == normalized), None)
