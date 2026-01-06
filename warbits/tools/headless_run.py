from __future__ import annotations

import argparse
from typing import Sequence

from ..core.sim import Simulation, summarize


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Warbits simulation headless.")
    parser.add_argument("--frames", type=int, default=200, help="number of frames to step")
    parser.add_argument("--seed", type=int, default=None, help="override scenario seed")
    parser.add_argument(
        "--sample-every",
        type=int,
        default=10,
        help="store every Nth position for determinism hash",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    frames = max(0, int(args.frames))
    sample_every = max(1, int(args.sample_every))
    sim = Simulation(seed=args.seed)
    samples: list[tuple[float, float, float]] = []

    for frame in range(frames):
        sim.step(frame)
        if frame % sample_every == 0:
            samples.append(sim.runtime.flight.plane_pos)

    summary = summarize(sim.runtime, frames, samples)
    print(f"frames={summary.frames}")
    print(f"impacts={summary.impacts}")
    print(f"explosions={summary.explosions}")
    print(f"parachutes={summary.parachutes}")
    print(f"hash={summary.hash}")


if __name__ == "__main__":
    main()
