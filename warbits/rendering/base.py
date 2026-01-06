from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ..logic.state import RuntimeState


class RendererAdapter(Protocol):
    def init_scene(self, sim_state: "RuntimeState") -> None:
        ...

    def begin_frame(self, frame_idx: int, sim_state: "RuntimeState") -> None:
        ...

    def draw_terrain(self, sim_state: "RuntimeState") -> None:
        ...

    def draw_aircraft(self, sim_state: "RuntimeState") -> None:
        ...

    def draw_projectiles(self, sim_state: "RuntimeState") -> None:
        ...

    def draw_entities(self, sim_state: "RuntimeState") -> None:
        ...

    def draw_events(self, sim_state: "RuntimeState") -> None:
        ...

    def end_frame(self, frame_idx: int, sim_state: "RuntimeState") -> None:
        ...

    def shutdown(self) -> None:
        ...


__all__ = ["RendererAdapter"]
