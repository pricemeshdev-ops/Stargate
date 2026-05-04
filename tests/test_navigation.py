from stargate_v3.navigation import SURFACES, surface_by_key


def test_core_surfaces_are_present():
    keys = {surface.key for surface in SURFACES}
    assert {"a", "ar", "ps", "pm", "b", "x", "z", "p", "e2"} <= keys


def test_epoch2_is_locked_reference():
    surface = surface_by_key("e2")
    assert surface is not None
    assert surface.status == "LOCKED"

