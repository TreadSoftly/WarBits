# Warbits Data Contract

Purpose: define canonical identifiers, required fields, units, and metadata for
all data-driven systems.

## Canonical IDs
- vehicle_id
- weapon_id
- warhead_id
- sensor_id
- loadout_id

## Minimum required fields
VehicleSpec:
- vehicle_id (string, unique)
- name (string)
- mass_kg (float)
- max_speed_mps (float)
- max_climb_mps (float)
- max_turn_rate_rad_s (float)
- sources (list of SourceMeta)

WeaponSpec:
- weapon_id (string, unique)
- name (string)
- weapon_type (enum: gun, rocket, bomb, missile)
- mass_kg (float)
- muzzle_velocity_mps (float) for guns
- warhead_id (string, optional for guns)
- sources (list of SourceMeta)

WarheadSpec:
- warhead_id (string, unique)
- name (string)
- explosive_mass_kg (float)
- fuse_type (enum: impact, proximity, timed)
- proximity_radius_m (float, optional)
- impact_delay_s (float, optional)
- sources (list of SourceMeta)

SensorSpec:
- sensor_id (string, unique)
- name (string)
- sensor_type (enum: optical, ir, radar)
- max_range_m (float)
- fov_deg (float)
- sources (list of SourceMeta)

LoadoutSpec:
- loadout_id (string, unique)
- vehicle_id (string)
- stations (list of StationSpec)
- sources (list of SourceMeta)

StationSpec:
- station_id (string or int)
- weapon_ids (list of weapon_id)
- max_mass_kg (float, optional)

## Units (required)
- distance: meters (m)
- time: seconds (s)
- mass: kilograms (kg)
- speed: meters per second (m/s)
- acceleration: meters per second squared (m/s^2)
- force: newtons (N)
- angles: radians (rad) unless explicitly marked as degrees (deg)

## Source metadata (required)
SourceMeta:
- source_name (string)
- source_path (string)
- source_hash (string, stable hash)
- ingested_at (ISO8601 string)
- schema_version (string)

## Cross-link rules
- weapon.warhead_id must exist in warheads.
- loadout.weapon_ids must exist in weapons.
- loadout.vehicle_id must exist in vehicles.
- sensors must be linked to vehicles or loadouts.
- unknown IDs are validation errors.

## Validation expectations
- Fail fast on missing required fields or invalid units.
- Fail on unresolved cross-links.
- Warn on optional fields when missing.
