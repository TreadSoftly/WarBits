# Warbits Baseline (PROMPT 1)

Date: 2026-01-03

## Repo tree (top level)
- .mypy_cache/
- .pytest_cache/
- .vscode/
- profiling/
- tests/
- tools/
- warbits/
- .gitignore
- MANIFEST.in
- Move To Panda3D.txt
- pyproject.toml
- TRACKER.md

## warbits/ package tree
warbits
|-- cli
|  |-- __init__.py
|  `-- warbits_cli.py
|-- config
|  |-- __init__.py
|  |-- settings.py
|  `-- style.py
|-- data
|  |-- __init__.py
|  |-- data_summary.json
|  |-- loadouts.json
|  |-- phases.py
|  |-- README.md
|  |-- sensors.json
|  |-- terrain.json
|  |-- vehicle_specs.py
|  |-- vehicles.json
|  |-- warheads.json
|  |-- weapon_specs.py
|  `-- weapons.json
|-- datanormalized
|  |-- aircraft_performance_points_fc2.csv
|  |-- custom_loadout_meta.jsonl
|  |-- custom_loadout_options.jsonl
|  |-- ingest_warbits_excels_v1.py
|  |-- README.md
|  |-- sea_level_speed_fc1.csv
|  |-- sensors_tgp_and_sights.jsonl
|  |-- vehicle_alias_candidates.jsonl
|  |-- vehicles.jsonl
|  |-- warheads.jsonl
|  `-- weapons.jsonl
|-- dataraw
|  |-- specialialdata.xlsx
|  |-- WarThunder_FactChecker1.xlsx
|  |-- WarThunder_FactChecker2.xlsx
|  `-- WarThunder_FactChecker3.xlsx
|-- logic
|  |-- __init__.py
|  |-- ai.py
|  |-- aircraft.py
|  |-- aircraft_hits.py
|  |-- enemy_bogies.py
|  |-- enemy_ground.py
|  |-- engagement.py
|  |-- flight_paths.py
|  |-- scenario.py
|  |-- state.py
|  `-- weather.py
|-- misc
|  |-- 0 TEST/
|  |-- 1 DEMO/
|  |-- 2 PROD/
|  |-- audio/
|  `-- KeyBindings/
|-- physics
|  |-- __init__.py
|  |-- ballistics.py
|  |-- ballistics_fast.py
|  |-- bombs.py
|  |-- explosions.py
|  |-- parachute.py
|  |-- rockets.py
|  `-- terrain.py
|-- scene
|  |-- __init__.py
|  |-- animation.py
|  |-- effects.py
|  |-- models.py
|  `-- mpl_setup.py
|-- utils
|  |-- __init__.py
|  |-- concurrency.py
|  |-- hardware.py
|  |-- math_tools.py
|  |-- objects.py
|  `-- profile_report.py
|-- __init__.py
`-- __main__.py

## Key file locations
ai.py: warbits/logic/ai.py
aircraft.py: warbits/logic/aircraft.py
aircraft_hits.py: warbits/logic/aircraft_hits.py
enemy_bogies.py: warbits/logic/enemy_bogies.py
enemy_ground.py: warbits/logic/enemy_ground.py
engagement.py: warbits/logic/engagement.py
flight_paths.py: warbits/logic/flight_paths.py
scenario.py: warbits/logic/scenario.py
state.py: warbits/logic/state.py
weather.py: warbits/logic/weather.py
warbits_cli.py: warbits/cli/warbits_cli.py
settings.py: warbits/config/settings.py
style.py: warbits/config/style.py
phases.py: warbits/data/phases.py
ballistics.py: warbits/physics/ballistics.py
ballistics_fast.py: warbits/physics/ballistics_fast.py
bombs.py: warbits/physics/bombs.py
rockets.py: warbits/physics/rockets.py
terrain.py: warbits/physics/terrain.py
explosions.py: warbits/physics/explosions.py
parachute.py: warbits/physics/parachute.py
effects.py: warbits/scene/effects.py
models.py: warbits/scene/models.py
mpl_setup.py: warbits/scene/mpl_setup.py
concurrency.py: warbits/utils/concurrency.py
hardware.py: warbits/utils/hardware.py
math_tools.py: warbits/utils/math_tools.py
objects.py: warbits/utils/objects.py
profile_report.py: warbits/utils/profile_report.py

## Entrypoints
- warbits/__main__.py calls warbits.cli.warbits_cli:main
- pyproject.toml defines console script: warbits = warbits.cli.warbits_cli:main
- warbits/scene/animation.py has __main__ guard and run_animation()
- warbits/scene/__init__.py re-exports run_animation()

## Render loop (per-frame dependencies)
- warbits.scene.animation._update() drives frames via matplotlib.FuncAnimation.
- _update() calls _step_sim(), step_aircraft(), and reads RUNTIME state.
- Imported dependencies for per-frame work:
  - logic: enemy_ground, enemy_bogies, aircraft_hits, scenario, weather, flight_paths, RUNTIME
  - physics: ballistics (bullets), rockets, bombs_step/bombs_reset/bombs_schedule_release, terrain, explosions, parachute
  - config: settings (scene limits, timing, perf flags)

## Tests
Command: python -m pytest -q
Result: 3 failed, 26 passed
Failures:
- tests/test_aircraft_hits.py::TestAircraftHits::test_bomb_hit_records_impact
  - expected bombs buffer to be empty after hit; len == 1
- tests/test_enemy_ground.py::TestEnemyGround::test_check_hits_records_impact
  - expected 1 impact; got 6
- tests/test_scenario.py::TestScenario::test_schedule_bounds
  - bogie_appear_frame was 67, expected >= 90

## Config dump
- Generated via: python -m warbits config
- Output: docs/baseline_config_dump.txt

## Import/path inconsistencies
- No core inconsistencies found. State imports consistently reference warbits.logic.state.
