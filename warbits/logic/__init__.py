# ── warbits/logic/__init__.py ───────────────────────────────────────────────
from __future__ import annotations

from typing import TYPE_CHECKING

# flight-path helpers (new public API) ---------------------------------------
from .flight_paths import generate_path, build_flight_plan, DEFAULT_PHASES

# fire-control helpers -------------------------------------------------------
from .engagement import (
    spawn_bomb,
    spawn_bullets,
    spawn_burst,
    spawn_rocket,
    step_projectiles,
)

# global runtime state -------------------------------------------------------
from .state import RUNTIME, FlightState, RuntimeState

# aircraft helpers (lazy; avoids matplotlib import during core sim loads) -----
if TYPE_CHECKING:
    from .aircraft import (
        register_axes as register_aircraft_axes,
        reset_aircraft,
        step_aircraft,
        create_aircraft_model,
    )

_AIRCRAFT_EXPORTS = {
    "register_aircraft_axes": "register_axes",
    "reset_aircraft": "reset_aircraft",
    "step_aircraft": "step_aircraft",
    "create_aircraft_model": "create_aircraft_model",
}


def __getattr__(name: str) -> object:
    target = _AIRCRAFT_EXPORTS.get(name)
    if target is not None:
        from . import aircraft as _aircraft

        return getattr(_aircraft, target)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__: list[str] = [
    # flight paths
    "generate_path",
    "build_flight_plan",
    "DEFAULT_PHASES",
    # runtime
    "RUNTIME",
    "FlightState",
    "RuntimeState",
    # engagement
    "spawn_burst",
    "spawn_bullets",
    "spawn_rocket",
    "spawn_bomb",
    "step_projectiles",
    # aircraft
    "register_aircraft_axes",
    "reset_aircraft",
    "step_aircraft",
    "create_aircraft_model",
]
