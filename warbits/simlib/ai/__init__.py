"""WarBits SmartLib - AI

This package is renderer-agnostic and sim-agnostic.
It provides deterministic building blocks for:
  - behavior trees
  - utility-based decision making
  - finite state machines
  - a lightweight GOAP planner
  - observation/track filtering

Design rules:
  - deterministic given the same seed + same call order
  - no hidden global RNG usage
  - no direct dependencies on matplotlib / panda3d / UI
"""

from .rng import DeterministicRNG, stable_hash64
from .blackboard import Blackboard
from .context import AIContext
from .behavior_tree import (
    Status,
    BehaviorTree,
    Node,
    Condition,
    Action,
    Sequence,
    Selector,
    RandomSelector,
    Parallel,
    Inverter,
    Succeeder,
    Failer,
    Repeat,
    Cooldown,
    Timeout,
)
from .utility import UtilityAction, UtilityPolicy, ScoreCurve
from .state_machine import State, Transition, StateMachine
from .goap import GoapAction, GoapPlanner, GoapState
from .tracks import Track, TrackManager, Observation

__all__ = [
    "DeterministicRNG",
    "stable_hash64",
    "Blackboard",
    "AIContext",
    "Status",
    "BehaviorTree",
    "Node",
    "Condition",
    "Action",
    "Sequence",
    "Selector",
    "RandomSelector",
    "Parallel",
    "Inverter",
    "Succeeder",
    "Failer",
    "Repeat",
    "Cooldown",
    "Timeout",
    "UtilityAction",
    "UtilityPolicy",
    "ScoreCurve",
    "State",
    "Transition",
    "StateMachine",
    "GoapAction",
    "GoapPlanner",
    "GoapState",
    "Track",
    "TrackManager",
    "Observation",
]
