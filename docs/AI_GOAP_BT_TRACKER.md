# AI GOAP + BT Integration Tracker

This tracker defines "100% done" for GOAP + Behavior Tree integration.

Phase 1 - Domain + API foundations
- [ ] Canonical import paths exist: `warbits.simlib.ai.goap` and `warbits.simlib.ai.behavior_tree`.
- [ ] A single low-level command model exists for AI output (no random dicts everywhere).
- [ ] A world-facts builder exists that converts (sensors + unit state + mission directive)
      -> GOAP facts deterministically.

Phase 2 - GOAP for AAA
- [ ] GOAP domain defined for AAA: actions + goals + costs + preconditions/effects.
- [ ] Planner tie-breaking is deterministic (stable sort, no unordered sets/dicts).
- [ ] Replan policy is budgeted (e.g., replan every N frames or on invalidation).

Phase 3 - Behavior Trees for AAA action execution
- [ ] Each GOAP action has a matching BT subtree executor.
- [ ] BT produces continuous control outputs (slew rate, fire bursts), not teleportation.
- [ ] BT has timeouts and failure reasons that trigger replans.

Phase 4 - Integrated AAA brain in live sim
- [ ] Enemy ground units are not omniscient; they act from tracks and mission goals.
- [ ] Headless run produces stable deterministic AI decision logs.

Phase 5 - Bogies (optional after AAA is stable)
- [ ] GOAP goals for bogies (intercept / extend / evade / reattack).
- [ ] BT executors drive autopilot/waypoints (not direct position teleport).
- [ ] Golden headless scenario hash remains stable.
