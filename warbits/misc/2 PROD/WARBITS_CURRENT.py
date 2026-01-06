
###############################################################################
# SECTION 1. IMPORTS & GLOBAL STATE (Advanced Concurrency/Automation)
###############################################################################
import math
import multiprocessing
import tkinter as tk
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from cycler import cycler
from math import cos, radians, sin
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from matplotlib.text import Text
from mpl_toolkits.mplot3d import Axes3D  # type: ignore
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # type: ignore
from numpy.typing import NDArray

active_bullets: List[Dict[str, Any]] = []
active_rockets: List[Dict[str, Any]] = []
targets = []
target_destroyed = []
bogie_poly: Optional[Poly3DCollection] = None
CURRENT_VEHICLE_TYPE: str = "AIRCRAFT"
SELECTED_VEHICLE: str = "F8F1_Bearcat"

def attempt_full_cpu_usage() -> None:
    cpu_ct = multiprocessing.cpu_count()
    with multiprocessing.Pool(processes=cpu_ct):
        pass

def attempt_full_gpu_usage() -> None:
    pass

###############################################################################
# SECTION 2. VISUAL STYLE
###############################################################################
mpl.rcParams["figure.facecolor"] = "black"
mpl.rcParams["axes.facecolor"]   = "black"
mpl.rcParams["axes.edgecolor"]   = "(0.05,0.05,0.1)"
mpl.rcParams["axes.linewidth"]   = 1
mpl.rcParams["grid.color"]       = "none"
mpl.rcParams["grid.alpha"]       = 1
mpl.rcParams["grid.linestyle"]   = ":"
mpl.rcParams["axes.grid"]        = False
mpl.rcParams["figure.dpi"]       = 75
mpl.rcParams["savefig.dpi"]      = 120
mpl.rcParams["savefig.facecolor"] = "black"
mpl.rcParams["savefig.edgecolor"] = "black"
mpl.rcParams["savefig.transparent"] = True
mpl.rcParams["font.family"]      = "sans-serif"
mpl.rcParams["font.size"]        = 10
mpl.rcParams["axes.labelsize"]   = 10
mpl.rcParams["axes.titlesize"]   = 10
mpl.rcParams["axes.titleweight"] = "bold"
mpl.rcParams["axes.titlecolor"]  = "#FF0000"
mpl.rcParams["legend.fontsize"]  = 8
mpl.rcParams["legend.frameon"]   = True
mpl.rcParams["legend.fancybox"]  = True
mpl.rcParams["legend.framealpha"]= 1
mpl.rcParams["legend.edgecolor"] = "none"
mpl.rcParams["xtick.color"]      = "none"
mpl.rcParams["ytick.color"]      = "none"
mpl.rcParams["axes.prop_cycle"]  = cycler(color=[
    "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
    "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"
])
mpl.rcParams["lines.linewidth"]       = 1.0
mpl.rcParams["lines.markersize"]      = 5
mpl.rcParams["lines.markeredgewidth"] = 1.3
mpl.rcParams["axes.spines.top"]       = True
mpl.rcParams["axes.spines.right"]     = True
mpl.rcParams["axes.spines.left"]      = True
mpl.rcParams["axes.spines.bottom"]    = False
mpl.rcParams["axes.xmargin"]          = 0.02
mpl.rcParams["axes.ymargin"]          = 0.02
mpl.rcParams["lines.antialiased"]     = True
mpl.rcParams["patch.antialiased"]     = True
mpl.rcParams["lines.solid_capstyle"]  = "butt"
mpl.rcParams["lines.solid_joinstyle"] = "miter"
mpl.rcParams["lines.dash_capstyle"]   = "butt"
mpl.rcParams["lines.dash_joinstyle"]  = "miter"
mpl.rcParams["xtick.major.size"]      = 10
mpl.rcParams["xtick.minor.size"]      = 3
mpl.rcParams["xtick.direction"]       = "in"
mpl.rcParams["xtick.top"]            = False
mpl.rcParams["ytick.left"]           = True
mpl.rcParams["axes.unicode_minus"]    = True
mpl.rcParams["axes.autolimit_mode"]   = "round_numbers"
mpl.rcParams["axes.axisbelow"]        = True
mpl.rcParams["toolbar"]               = "None"
mpl.rcParams["figure.figsize"]        = (10,8)

###############################################################################
# SECTION 3. CURRENT VEHICLE & LOADOUT (Hardcoded)
###############################################################################
F8F1_Bearcat_Data: Dict[str, Any] = {
    "Name": "F8F-1 Bearcat",
    "Nation": "USA",
    "Type": "Naval Fighter (Carrier-Based)",
    "BR_Realistic": 4.7,
    "Crew": 1,

    "Dimensions": {
        "Length_m": 8.61,
        "Wingspan_m": 10.92,
        "Height_m": 3.83,
        "Wing_Area_m2": 20.5,
        "Empty_Weight_kg": 3175,
        "Loaded_Weight_kg": 4220,
    },

    "Engine": {
        "Designation": "Pratt & Whitney R-2800-34W",
        "Type": "Two-row, 18-cylinder radial, air-cooled",
        "Horsepower_HP": 2250,
        "Takeoff_Power_HP": 2800,
        "Supercharger_Stages": "Two-speed mechanical",
        "Optimal_Manifold_Pressure_psi": 54,
        "Propeller": "Hamilton St&ard Hydromatic, 3.96 m diameter",
    },

    "Performance": {
        "Max_Speed_mph_at_alt": 440,
        "Max_Speed_kmh": 708,
        "Max_Altitude_ft": 35752,
        "Max_Altitude_m": 10900,
        "Optimal_Cruise_Speed_mph": [320, 380],
        "Climb_Rate_ftmin": 4961,
        "Acceleration_Throttle_SeaLevel_mph": 330,
        "Acceleration_Throttle_SeaLevel_TimeSec": 17,
        "Acceleration_Throttle_5000ft_mph": 360,
        "Acceleration_Throttle_5000ft_TimeSec": 22,
        "Acceleration_Throttle_10000ft_mph": 385,
        "Acceleration_Throttle_10000ft_TimeSec": 28,
        "Acceleration_Throttle_15000ft_mph": 410,
        "Acceleration_Throttle_15000ft_TimeSec": 35,
        "Turn_Time_sec": 19.0,
        "Roll_Rate_degsec": 140,
        "Stall_Speed_mph": 110,
        "Engine_Overheat_Risk": "High if WEP used too long",
        "WEP_Max_Duration_sec": 120,
        "Engine_Cooling_Required_sec": 50,
        "Takeoff_Distance_ft": 630,
        "L&ing_Distance_ft": 750,
        "Rate_of_Climb_fpm_SeaLevel": 4700,
        "Time_to_20000ft_min": 7.0,
        "Combat_Flaps_Deployment_Speed_mph": 200,
        "Wing_Loading_kg_m2": 205,
        "Power_to_Weight_Ratio_hp_lb": 0.59
    },

    "Armament": {
        "Machine_Guns": {
            "Type": "4 x 12.7 mm M2 Browning",
            "Ammo_Count_PerGun": 1250,
            "Fire_Rate_rpm": 800,
            "Burst_Mass_kgsec": 4.32,
            "Muzzle_Velocity_ms": 890
        },
        "Ammo_Belt_Options": [
            "Default - Balanced mix",
            "Tracer - All tracers, easier to aim but lower damage",
            "Stealth - No tracers, surprise attacks",
            "Ground Targets - Armor-piercing for light vehicles"
        ],
        "Bombs_&_Rockets": {
            "Bomb_Hardpoints": 1,
            "1x_1000_lb_Bomb_ANM65A1": {
                "Damage_Radius_m": (15, 25),
                "Fragmentation_Radius_m": 50,
                "Weight_Effect_on_H&ling": {
                    "Reduced_Acceleration_percent": 8,
                    "Reduced_Climb_Rate_percent": 10
                },
                "Minimum_Safe_Drop_Altitude_m": 250,
                "Fuse_Time_Options_sec": [0, 3, 5, 7]
            },
            "8x_HVAR_Rockets": "General-purpose, ~60mm penetration RHA"
        }
    },

    "Game_Strategy": {
        "Preferred_Playstyles": [
            "Boom & Zoom",
            "Energy Trapping (Rope-a-Dope)",
            "Sustained Speed Fighting",
            "Defensive Rolling Scissors"
        ],
        "Key_Tips": [
            "Avoid turn fights with Spitfires / A6Ms / Yaks",
            "Maintain speed above 300 mph",
            "Use high roll rate to force overshoots",
            "If tail threat is high, break below 150m to confuse radar/AA"
        ],
        "Post_Bombing_Escape_Tactics": {
            "AA_Fire_Survival_Rates_percent": {
                200: 78,
                500: 90,
                800: 97
            },
            "Best_Maneuvers_vs_AA": "Perform S-Turns at <200m altitude",
            "Best_Maneuvers_vs_Fighters": "Split-S or rolling scissors immediately after drop"
        }
    },

    "Comparison_vs_Competitors_BR47": [
        {
            "Aircraft": "F8F-1 Bearcat",
            "Max_Speed_mph": 440,
            "Climb_Rate_ftmin": 4961,
            "Turn_Time_sec": 19,
            "Firepower": "4x 12.7 mm"
        },
        {
            "Aircraft": "F4U-1C Corsair",
            "Max_Speed_mph": 425,
            "Climb_Rate_ftmin": 4500,
            "Turn_Time_sec": 21,
            "Firepower": "4x 20mm cannons"
        },
        {
            "Aircraft": "P-51D-30 Mustang",
            "Max_Speed_mph": 437,
            "Climb_Rate_ftmin": 3800,
            "Turn_Time_sec": 22,
            "Firepower": "6x 12.7 mm"
        },
        {
            "Aircraft": "Yak-3U",
            "Max_Speed_mph": 410,
            "Climb_Rate_ftmin": 4800,
            "Turn_Time_sec": 17,
            "Firepower": "2x 20mm cannons"
        },
        {
            "Aircraft": "Spitfire LF Mk.IX",
            "Max_Speed_mph": 408,
            "Climb_Rate_ftmin": 4900,
            "Turn_Time_sec": 16,
            "Firepower": "2x 20mm + 2x .50 cal"
        }
    ],

    "Economy": {
        "Repair_Cost_RB": 3150,
        "Free_Repair_Time": "11h 42m",
        "Reward_Multipliers": {
            "RB": 2.10,
            "SB": 4.77
        }
    },

    "Historical_Notes": [
        "One of the fastest piston-engine aircraft developed near WWII’s end",
        "Entered service late 1945 but missed active WWII combat",
        "Used post-war; heavily praised for climb rate & agility",
        "Some saw action with French forces in Indochina War",
        "Renowned for short takeoff / l&ing on carriers",
        "Sometimes outperforms contemporary piston fighters in vertical maneuvers"
    ]
}

###############################################################################
# SECTION 4. VEHICLE CONFIG (Basic placeholders)
###############################################################################
Vehicle_Config: Dict[str, Any] = {
    "vehicle": {
        "classification": "Fixed-wing Aircraft/...",
        "nation": "Country",
        "role": "Interceptor/Multirole Fighter/Bomber/CAS/...",
        "battle_rating": 0.0,
        "dimensions": {
            "length_m": 0.0,
            "wingspan_m": 0.0,
            "height_m": 0.0,
            "weight_kg": 0.0,
            "wing_area_m2": 0.0,
            "armor_thickness_front_mm": 0.0,
            "armor_thickness_side_mm": 0.0,
            "armor_thickness_rear_mm": 0.0,
            "hull_armor_thickness_mm": 0.0,
            "turret_armor_thickness_mm": 0.0,
            "composite_armor": False,
            "spall_liners": False
        },
        "performance": {
            "max_speed_kmh": 0.0,
            "cruise_speed_kmh": 0.0,
            "climb_rate_m_s": 0.0,
            "turn_time_sec": 0.0,
            "stall_speed_kmh": 0.0,
            "max_dive_speed_kmh": 0.0,
            "acceleration_0_600_kmh_sec": 0.0,
            "braking_distance_m": 0.0,
            "roll_rate_deg_s": 0.0,
            "takeoff_distance_m": 0.0,
            "l&ing_distance_m": 0.0,
            "max_g_load": 0.0,
            "engine_overheat_risk": "Low/Medium/High",
            "prop_pitch_auto": True,
            "supercharger_modes": ["Stage 1", "Stage 2"],
            "fuel_consumption_liters_per_hour": 0.0,
            "operational_ceiling_m": 0.0,
            "drag_coefficient": 0.0,
            "aerodynamic_efficiency": 0.0
        },
        "engine": {
            "type": "Engine Type",
            "horsepower": 0.0,
            "afterburner": False,
            "fuel_capacity_liters": 0.0,
            "max_range_km": 0.0,
            "supercharger_stages": 0,
            "optimal_manifold_pressure_psi": 0.0,
            "propeller_diameter_m": 0.0,
            "ignition_boosters": False,
            "cooling_system": "Air/Liquid",
            "turbofan_bypass_ratio": 0.0,
            "thrust_vectoring": False
        },
        "weapons": {
            "primary": [
                {
                    "name": "Weapon Name",
                    "type": "Machine Gun/Cannon/Missile/Rocket/Laser",
                    "caliber_mm": 0.0,
                    "ammo_count": 0,
                    "fire_rate_rpm": 0.0,
                    "muzzle_velocity_m_s": 0.0,
                    "burst_mass_kg_sec": 0.0,
                    "tracer_color": "Red/Green/Blue",
                    "ballistic_computer": False
                }
            ],
            "secondary": [
                {
                    "name": "Secondary Weapon Name",
                    "type": "Bomb/Missile/Rocket/Torpedo/Depth Charge",
                    "damage_radius_m": 0.0,
                    "penetration_mm": 0.0,
                    "blast_radius_m": 0.0,
                    "weight_kg": 0.0,
                    "fuse_time_sec": [0,3,5,7],
                    "guided": False,
                    "infrared_homing": False
                }
            ],
            "additional_guns": {
                "name": "Additional Gun Name",
                "type": "Cannon/Turret/MG/CIWS",
                "caliber_mm": 0.0,
                "fire_rate_rpm": 0.0,
                "ammo_count": 0,
                "stabilized": False
            }
        },
        "countermeasures": {
            "flares": 0,
            "chaff": 0,
            "armor_thickness_mm": 0.0,
            "smoke_screens": False,
            "active_protection_system": False,
            "radar_warning_receiver": False,
            "infrared_countermeasures": False,
            "electronic_warfare_capability": False,
            "decoy_systems": False,
            "jamming_pod": False
        },
        "navigation_systems": {
            "GPS": True,
            "INS": True,
            "radar_altimeter": False,
            "autopilot_modes": ["Navigation", "Combat", "L&ing"],
            "terrain_following": True
        },
        "bombing_parameters": {
            "bomb_fuse_time_sec": [0,3,5,7],
            "minimum_safe_drop_altitude_m": 0.0,
            "bombing_accuracy": {
                "below_300m": "High",
                "300m_800m": "Moderate",
                "above_800m": "Low"
            },
            "bomb_sight_type": "CCRP/CCIP",
            "laser_guided": False
        },
        "ballistics": {
            "bullet_drop_m_at_500m": 0.0,
            "bullet_drop_m_at_1000m": 0.0,
            "armor_penetration_mm_at_500m": 0.0,
            "armor_penetration_mm_at_1000m": 0.0,
            "ricochet_probability": "Low/Medium/High",
            "fragmentation_characteristics": "St&ard/High-Explosive"
        },
        "radar": {
            "has_radar": False,
            "tracking_range_km": 0.0,
            "radar_modes": ["Search","Track","Lock"],
            "radar_lock_time_sec": 0.0,
            "synthetic_aperture_radar": False
        },
        "economy": {
            "repair_cost": 0.0,
            "reward_multiplier": {
                "arcade": 0.0,
                "realistic": 0.0,
                "simulator": 0.0
            },
            "crew_training_cost": 0.0,
            "modification_cost": 0.0,
            "munitions_cost": 0.0
        },
        "historical_background": "Short description of vehicle history.",
        "operational_doctrine": "Typical mission types & roles for this vehicle.",
        "electronic_systems": {
            "fire_control_system": False,
            "laser_rangefinder": False,
            "targeting_computer": False,
            "infrared_tracking": False,
            "ECM_capability": False
        }
    }
}

###############################################################################
# SECTION 5. WEAPONS CONFIG
###############################################################################
Weapons_Config: Dict[str, Any] = {
    "weapon": {
        "classification": "Machine Gun/Cannon/Missile/Rocket/Laser/Bomb/...",
        "manufacturer": "Company Name",
        "nation": "Country of Origin",
        "service_entry_year": 0,
        "decommissioned": False,
        "physical_attributes": {
            "caliber_mm": 0.0,
            "weapon_length_m": 0.0,
            "weapon_weight_kg": 0.0,
            "barrel_length_m": 0.0,
            "barrel_diameter_mm": 0.0,
            "chamber_pressure_psi": 0.0,
            "material_composition": "Alloy/Steel/Titanium/Carbon Fiber",
            "barrel_rifling": "Smoothbore/Rifled/Twist Rate",
            "heat_resistance_celsius": 0.0,
            "operating_temperature_range_celsius": [0.0, 0.0]
        },
        "firing_characteristics": {
            "fire_rate_rpm": 0.0,
            "muzzle_velocity_m_s": 0.0,
            "effective_range_m": 0.0,
            "maximum_range_m": 0.0,
            "burst_mass_kg_sec": 0.0,
            "recoil_force_kn": 0.0,
            "barrel_life_rounds": 0,
            "cooling_mechanism": "Air/Liquid/Refrigerated",
            "firing_modes": ["Single Shot","Burst","Fully Automatic"],
            "cyclic_rate_rpm": 0.0,
            "reload_time_sec": 0.0,
            "suppression_effectiveness": "Low/Medium/High"
        },
        "ammunition": {
            "types": [
                "AP","HE","HEAT","Tracer","Incendiary","Proximity Fuze","T&em Warhead"
            ],
            "round_weight_kg": 0.0,
            "explosive_mass_kg": 0.0,
            "penetration_mm": 0.0,
            "damage_radius_m": 0.0,
            "blast_radius_m": 0.0,
            "fragmentation_count": 0,
            "velocity_decay_over_distance": 0.0,
            "armor_defeat_probability": "Low/Medium/High",
            "shockwave_effect": "None/Moderate/Severe",
            "chemical_reactivity": "None/Thermite/Napalm",
            "fuse_delay_options_sec": [0.0,0.5,1.0,2.0]
        },
        "guidance_system": {
            "guided": False,
            "infrared_homing": False,
            "radar_guided": False,
            "laser_guided": False,
            "GPS_guided": False,
            "comm&_guided": False,
            "semi-active_laser_guided": False,
            "target_lock_time_sec": 0.0,
            "maneuverability_g": 0.0,
            "jamming_resistance": "Low/Medium/High",
            "multi-target_engagement": False
        },
        "warhead": {
            "type": "Conventional/Nuclear",
            "explosive_mass_kg": 0.0,
            "penetration_mm": 0.0,
            "damage_radius_m": 0.0,
            "blast_radius_m": 0.0,
            "fragmentation_count": 0,
            "proximity_fuze": False,
            "impact_fuze": True,
            "delay_fuze": False,
            "warhead_yield_kt": 0.0,
            "electromagnetic_pulse_effect": False,
            "blast_pressure_mpa": 0.0
        },
        "mounting_options": {
            "aircraft": True,
            "tank": True,
            "naval": True,
            "infantry": False,
            "fixed_mount": False,
            "turret_mount": True,
            "recoil_mechanism": "Hydraulic/Spring/Gas",
            "mounting_stability": "Low/Medium/High",
            "swivel_capability_deg": 0.0
        },
        "countermeasures": {
            "decoy_flares": False,
            "chaff": False,
            "jamming_resistance": "Low/Medium/High",
            "electronic_countermeasure_protection": False,
            "thermal_signature_reduction": False,
            "radar_absorption_material": False
        },
        "ballistics": {
            "bullet_drop_m_at_500m": 0.0,
            "bullet_drop_m_at_1000m": 0.0,
            "armor_penetration_mm_at_500m": 0.0,
            "armor_penetration_mm_at_1000m": 0.0,
            "ricochet_probability": "Low/Medium/High",
            "fragmentation_characteristics": "St&ard/High-Explosive",
            "time_to_target_sec": 0.0,
            "air_resistance_coefficient": 0.0,
            "trajectory_correction_system": False,
            "muzzle_energy_j": 0.0
        },
        "deployment_modes": [
            "Air-to-Air","Air-to-Ground","Ground-to-Air","Ground-to-Ground","Naval Warfare"
        ],
        "historical_background": "Short description of weapon history.",
        "operational_doctrine": "Typical mission types & roles for this weapon."
    }
}

###############################################################################
# SECTION 6. ADDITIONAL DATA
###############################################################################
Advanced_Bearcat_Data: dict[str, dict[int, float] | dict[str, str | dict[str, str]]] = {
    "Bullet_Drop_At_Range_m": {
        500: -0.2,
        1000: -0.9,
        1500: -2.5
    },
    "Armor_Penetration_50cal_mm": {
        500: 23,
        1000: 19,
        1500: 13
    },
    "Climb_Rate_Alt_m_s": {
        0: 25.2,
        3000: 20.5,
        6000: 17.7,
        10000: 10.6
    },
    "Bombing_Accuracy": {
        "Drop_300m": "High (95% vs. stationary)",
        "Drop_600m": "Very Good (80-90%)",
        "Drop_1200m": "Moderate (50-60%)",
        "CCIP": {
            "Below_300m": "98% accuracy",
            "Between_300m_800m": "Minor corrections",
            "Above_1000m": "Manual lead needed"
        }
    },
    "Dogfight_Stats": {
        "vs_P51D": "Win ~40% if same energy",
        "vs_SpitfireIX": "Win ~50% if BnZ"
    }
}

###############################################################################
# SECTION 7. PHASES (Map for scenario. A start to help with dynamics in scenarios)
###############################################################################
phases_info = {
    "Approach": ("blue",   60),
    "Strafe":   ("orange", 50),
    "Bombing":  ("red",    50),
    "Escape":   ("green",  60),
    "Dogfight": ("purple", 70)
}

###############################################################################
# SECTION 8. AIR ASSAULT - FLIGHT PATHS (Hardcoded for now. Need free flight & dynamic)
###############################################################################
def generate_path(
    start: Tuple[float, float, float],
    end:   Tuple[float, float, float],
    num_points: int,
    curve: str = ""
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    x0, y0, z0 = start
    x1, y1, z1 = end
    t_vals = np.linspace(0, 1, num_points, dtype=np.float64)

    x_arr = x0 + (x1 - x0) * t_vals
    y_arr = y0 + (y1 - y0) * t_vals
    z_arr = z0 + (z1 - z0) * t_vals

    if curve == "strafe_dive":
        # Sharper negative sinusoidal approach
        z_arr = z0 - (z0 - z1) * np.sin(t_vals * np.pi / 2)
    elif curve == "escape_climb":
        # Some wave climb
        z_arr += 500 * np.sin(2 * np.pi * t_vals)
    elif curve == "dogfight_maneuver":
        # A more complicated x,y,z pattern
        x_arr += 400 * np.sin(4 * np.pi * t_vals)
        y_arr += 300 * np.cos(2 * np.pi * t_vals)
        z_arr += 200 * np.sin(3 * np.pi * t_vals)

    return x_arr, y_arr, z_arr

phases_info = {
    "Approach": ("blue",   60),
    "Strafe":   ("orange", 50),
    # Reduce bombing frames to 40 => plane moves faster in that phase
    "Bombing":  ("red",    40),
    "Escape":   ("green",  60),
    "Dogfight": ("purple", 70)
}

A_start = (0, 6000, 3000)
A_end   = (6000, 7500, 2200)
numA = phases_info["Approach"][1]
xA,yA,zA = generate_path(A_start,A_end,numA)

B_start = A_end
B_end   = (10000,7000,400)
numB = phases_info["Strafe"][1]
xB,yB,zB = generate_path(B_start,B_end,numB,curve="strafe_dive")

C_start = B_end
# Raise the bombing end altitude from 400 → 1200 for a longer bomb drop
C_end   = (15000, 7500, 650)
numC = phases_info["Bombing"][1]
xC,yC,zC = generate_path(C_start,C_end,numC)

D_start = C_end
D_end   = (7000, 6000, 4000)
numD = phases_info["Escape"][1]
xD,yD,zD = generate_path(D_start,D_end,numD,curve="escape_climb")

E_start = D_end
E_end   = (5000, 6500, 3500)
numE = phases_info["Dogfight"][1]
xE,yE,zE = generate_path(E_start,E_end,numE,curve="dogfight_maneuver")

# Victory extension
Victory_start = E_end
Victory_mid   = (E_end[0]+2000, E_end[1], E_end[2]+1000)
Victory_end   = A_start

numV1 = 80
xV1,yV1,zV1 = generate_path(Victory_start, Victory_mid, numV1, curve="escape_climb")
numV2 = 120
xV2,yV2,zV2 = generate_path(Victory_mid, Victory_end, numV2, curve="dogfight_maneuver")

xVictory = np.concatenate([xV1, xV2])
yVictory = np.concatenate([yV1, yV2])
zVictory = np.concatenate([zV1, zV2])

flight_x = np.concatenate([xA, xB, xC, xD, xE, xVictory])
flight_y = np.concatenate([yA, yB, yC, yD, yE, yVictory])
flight_z = np.concatenate([zA, zB, zC, zD, zE, zVictory])
frames_total = len(flight_x)

idxA_end = numA
idxB_end = idxA_end + numB
idxC_end = idxB_end + numC
idxD_end = idxC_end + numD
idxE_end = idxD_end + numE
phase_slices = {
    "Approach": (0, idxA_end),
    "Strafe":   (idxA_end, idxB_end),
    "Bombing":  (idxB_end, idxC_end),
    "Escape":   (idxC_end, idxD_end),
    "Dogfight": (idxD_end, idxE_end)
}

# # ###############################################################################
# SECTION 9 Marked Path Of Scenario (Turn on or off)
# # #  <THIS NEEDS TO BE DYNAMIC, MORE AESTHETIC, BETTER FEATURES FOR WHAT THIS IS>
# # # (Toggle off/on with #s or highlight all & press Ctrl+/)
# # ###############################################################################
# phase_positions = {
#     "Approach": (xA,yA,zA),
#     "Strafe":   (xB,yB,zB),
#     "Bombing":  (xC,yC,zC),
#     "Escape":   (xD,yD,zD),
#     "Dogfight": (xE,yE,zE)
# }

# phase_quivers: Dict[str, Sequence[Line3DCollection]] = {pname:[] for pname in phase_positions}
# arrow_len=400

# def create_phase_quivers(ax: Axes3D, xarr: NDArray[np.float64], yarr: NDArray[np.float64], zarr: NDArray[np.float64], color: str) -> List[Line3DCollection]:
#     quivs: List[Line3DCollection] = []
#     interval=3
#     for i in range(0,len(xarr)-1,interval):
#         dx = xarr[i+1]-xarr[i]
#         dy = yarr[i+1]-yarr[i]
#         dz = zarr[i+1]-zarr[i]
#         q: Line3DCollection = ax.quiver( #type: ignore
#             xarr[i], yarr[i], zarr[i],
#             dx, dy, dz,
#             length=arrow_len, normalize=True,
#             color=color, arrow_length_ratio=0.3
#         ) #type: ignore
#         quivs.append(q)
#     return quivs

# fig = plt.figure(figsize=(20, 14)) #type: ignore
# ax_main: Axes3D = fig.add_subplot(111, projection='3d') #type: ignore

# for pname,(col,num_pts) in phases_info.items():
#     xP,yP,zP = phase_positions[pname]
#     phase_quivers[pname] = create_phase_quivers(ax_main, xP,yP,zP, col)

###############################################################################
# SECTION 10. GENERATE TERRAIN <NEEDS TO AUTO RECOGNIZE AND FILL FULL SCREEN>
###############################################################################
def generate_terrain(
    xmin: int = 0,
    xmax: int = 18500,
    ymin: int = 4000,
    ymax: int = 9300,
    step: int = 300,
    amplitude: int = 600
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    x_vals = np.linspace(xmin, xmax, step)
    y_vals = np.linspace(ymin, ymax, step)
    x, y = np.meshgrid(x_vals, y_vals)
    np.random.seed(42)
    z = amplitude * 0.4 * np.sin(x / 1500) * np.cos(y / 1500)
    z += amplitude * 0.4 * np.random.rand(step, step)
    return x, y, z

###############################################################################
# SECTION 11. PLOT 3D SCENES (FULL SCREEN AUTO-DETECT VERSION)
###############################################################################
# 1) Detect the system's screen resolution via tkinter:
root = tk.Tk()
screen_width = root.winfo_screenwidth()   # e.g. 1920
screen_height = root.winfo_screenheight() # e.g. 1080
root.destroy()

# 2) Pick a reasonable DPI (dots-per-inch). 100 or 96 is typical.
dpi = 100

# 3) Convert pixel dims => inches for figure creation
figsize_w = screen_width / dpi
figsize_h = screen_height / dpi

# 4) Create the figure to fill nearly the entire screen in "inches"
fig = plt.figure(figsize=(figsize_w, figsize_h), dpi=dpi)  # type: ignore

ax_main: Axes3D = fig.add_subplot(111, projection='3d')  # type: ignore

# Optionally: Attempt to maximize the window at runtime
manager = plt.get_current_fig_manager()  # type: ignore
try:
    # Try advanced "maximize" logic by backend
    backend_name = mpl.get_backend().lower()
    if 'tkagg' in backend_name:
        # For TkAgg on Windows: manager.window.state('zoomed')
        # For TkAgg on Linux: manager.resize(*manager.window.maxsize())
        # We'll pick a generic fallback:
        manager.window.state('zoomed')  # type: ignore
    elif 'wx' in backend_name:
        manager.frame.Maximize(True)  # type: ignore
    elif 'qt' in backend_name:
        manager.window.showMaximized()  # type: ignore
    else:
        # Fallback: full_screen_toggle or do nothing
        manager.full_screen_toggle()  # type: ignore
except Exception as e:
    print(f"[WARN] Could not maximize figure window automatically: {e}")

# Now set your axes limits
xmin, xmax = 0, 18500
ymin, ymax = 4000, 9300
step, amplitude = (100, 800)

ax_main.set_xlim(xmin, xmax)  # type: ignore
ax_main.set_ylim(ymin, ymax)  # type: ignore
ax_main.set_zlim(0, 15000)    # type: ignore

# Hide axis "pane" backgrounds (since stubs aren’t always defined, we ignore warnings)
ax_main.xaxis.pane.set_facecolor((0,0,0,0))  # type: ignore
ax_main.yaxis.pane.set_facecolor((0,0,0,0))  # type: ignore
ax_main.zaxis.pane.set_facecolor((0,0,0,0))  # type: ignore
ax_main.xaxis.pane.set_edgecolor((0,0,0,0))  # type: ignore
ax_main.yaxis.pane.set_edgecolor((0,0,0,0))  # type: ignore
ax_main.zaxis.pane.set_edgecolor((0,0,0,0))  # type: ignore

# Generate & plot the terrain
x_terr, y_terr, z_terr = generate_terrain()  # same function from your code
ax_main.plot_surface(x_terr, y_terr, z_terr, cmap='terrain', alpha=0.2, edgecolor='none')  # type: ignore

ax_main.set_title("F8F-1 Bearcat 3D (Approach->Strafe->Bomb->Escape->Dogfight)")  # type: ignore
ax_main.set_xlabel("X (m)")  # type: ignore
ax_main.set_ylabel("Y (m)")  # type: ignore
ax_main.set_zlabel("Altitude (m)")  # type: ignore

# Zoom out or in to a suitable viewpoint
ax_main.set_xlim(0, 16000)   # type: ignore
ax_main.set_ylim(5000, 9000) # type: ignore
ax_main.set_zlim(0, 5000)    # type: ignore
ax_main.view_init(elev=30, azim=-60)  # type: ignore

# Tidy up layout so everything fits
plt.tight_layout()  # type: ignore

###############################################################################
# SECTION 12. GROUND ASSAULT <NEEDS DYNAMIC AIM, SHOOT/SHOT, HIT/MISS &/OR DESTROYED>
###############################################################################
def create_aaa_geometry(cx: float, cy: float, cz: float,
                        size_base: float = 120, height_base: float = 70,
                        size_turret: float = 90, turret_angle_deg: float = 30) -> List[List[Tuple[float, float, float]]]:
    angle_r = radians(turret_angle_deg)

    b=size_base/2
    base_bottom=cz
    base_top=cz+height_base

    base_verts = [
        (cx-b,cy-b,base_bottom),
        (cx+b,cy-b,base_bottom),
        (cx+b,cy+b,base_bottom),
        (cx-b,cy+b,base_bottom),
    ]
    base_verts_top=[
        (cx-b,cy-b,base_top),
        (cx+b,cy-b,base_top),
        (cx+b,cy+b,base_top),
        (cx-b,cy+b,base_top),
    ]
    base_faces = [
        [base_verts[0],base_verts[1],base_verts[2],base_verts[3]],
        [base_verts_top[0],base_verts_top[1],base_verts_top[2],base_verts_top[3]],
        [base_verts[0],base_verts[1],base_verts_top[1],base_verts_top[0]],
        [base_verts[1],base_verts[2],base_verts_top[2],base_verts_top[1]],
        [base_verts[2],base_verts[3],base_verts_top[3],base_verts_top[2]],
        [base_verts[3],base_verts[0],base_verts_top[0],base_verts_top[3]],
    ]

    turret_z_bottom = base_top
    turret_z_top    = base_top + 30
    half_t = size_turret/2

    def rotX(x_: float, y_: float) -> Tuple[float, float]:
        dx_ = x_ - cx
        dy_ = y_ - cy
        xr_ = dx_*cos(angle_r) - dy_*sin(angle_r)
        yr_ = dx_*sin(angle_r) + dy_*cos(angle_r)
        return (cx + xr_, cy + yr_)

    t_verts_bot_raw = [
        (cx-half_t, cy-half_t, turret_z_bottom),
        (cx+half_t, cy-half_t, turret_z_bottom),
        (cx+half_t, cy+half_t, turret_z_bottom),
        (cx-half_t, cy+half_t, turret_z_bottom),
    ]
    turret_verts_bot: List[Tuple[float, float, float]] = []
    for (xx,yy,zz) in t_verts_bot_raw:
        rx, ry = rotX(xx,yy)
        turret_verts_bot.append((rx,ry,zz))

    t_verts_top_raw = [
        (cx-half_t, cy-half_t, turret_z_top),
        (cx+half_t, cy-half_t, turret_z_top),
        (cx+half_t, cy+half_t, turret_z_top),
        (cx-half_t, cy+half_t, turret_z_top),
    ]
    turret_verts_top: List[Tuple[float, float, float]] = []
    for (xx,yy,zz) in t_verts_top_raw:
        rx, ry = rotX(xx,yy)
        turret_verts_top.append((rx,ry,zz))

    turret_faces = [
        [turret_verts_bot[0],turret_verts_bot[1],turret_verts_bot[2],turret_verts_bot[3]],
        [turret_verts_top[0],turret_verts_top[1],turret_verts_top[2],turret_verts_top[3]],
        [turret_verts_bot[0],turret_verts_bot[1],turret_verts_top[1],turret_verts_top[0]],
        [turret_verts_bot[1],turret_verts_bot[2],turret_verts_top[2],turret_verts_top[1]],
        [turret_verts_bot[2],turret_verts_bot[3],turret_verts_top[3],turret_verts_top[2]],
        [turret_verts_bot[3],turret_verts_bot[0],turret_verts_top[0],turret_verts_top[3]],
    ]

    return base_faces + turret_faces

def ground_aaa_position(frame: int, center_x: float, center_y: float, radius: float = 600) -> Tuple[float, float, float]:
    t = (frame % 200) / 200.0
    angle = 2 * math.pi * t
    gx = center_x + radius * math.cos(angle)
    gy = center_y + radius * math.sin(angle)
    gz = 0
    return gx, gy, gz

###############################################################################
# SECTION 13. LOCKON & ENGAGEMENTS <ADD GROUND & LOCKON TARGET TO BLINK COLORS DYNAMIC>
###############################################################################
bogie_x = np.full(frames_total, np.nan)
bogie_y = np.full(frames_total, np.nan)
bogie_z = np.full(frames_total, np.nan)

# We define the point in time (frame) at which a 'bogie' (enemy or unknown) appears.
bogie_appear = idxD_end - 20  # near the end of the Escape phase, so we see a new threat
bx_start = 20000
by_start = 7500
bz_start = 500

# Initialize the bogie_x/y/z with NaNs until we reach bogie_appear frame
for f in range(frames_total):
    if f < bogie_appear:
        continue
    # Once we hit the bogie_appear frame, place the bogie at a certain location
    if f == bogie_appear:
        bogie_x[f] = bx_start
        bogie_y[f] = by_start
        bogie_z[f] = bz_start
    else:
        # After it appears, it attempts to close in on the player's plane, or it moves relative to plane
        px_ = flight_x[f]
        py_ = flight_y[f]
        pz_ = flight_z[f]
        dx_ = px_ - bogie_x[f - 1]
        dy_ = py_ - bogie_y[f - 1]
        dz_ = pz_ - bogie_z[f - 1]
        # We move the bogie 20% of the vector from its last position to the plane's current position
        bogie_x[f] = bogie_x[f - 1] + 0.2 * dx_
        bogie_y[f] = bogie_y[f - 1] + 0.2 * dy_
        bogie_z[f] = bogie_z[f - 1] + 0.2 * dz_

bogie_is_hit = False
bogie_hit_frame = None
###############################################################################
# SECTION 14. EXPLOSION + PARACHUTE < IM NOT SEEING THE VISUAL FOR THIS HAPPENING>
###############################################################################
explosion_active = False
explosion_frame = 0
explosion_max_frames = 30
explosion_poly = None
explosion_center = (0.0, 0.0, 0.0)

def spawn_explosion(center: Tuple[float, float, float]):
    global explosion_active, explosion_frame, explosion_center, explosion_poly
    explosion_active = True
    explosion_frame = 0
    explosion_center = center
    if explosion_poly:
        # remove any existing explosion geometry
        explosion_poly.remove()
        explosion_poly = None

parachute_poly = None
parachute_active = False
parachute_frame = 0
parachute_center = (0.0, 0.0, 0.0)

def spawn_parachute(center: Tuple[float, float, float]):
    global parachute_active, parachute_frame, parachute_center
    parachute_active = True
    parachute_frame = 0
    parachute_center = center

###############################################################################
# SECTION 15. ALL 3D MODELS (Current Hardcoded are Bearcat, Bogie. Add all others))
###############################################################################
def create_bearcat_model(
    position: Tuple[float, float, float],
    direction: Tuple[float, float, float],
    scale: float = 120,
    color: str = 'blue'
) -> Poly3DCollection:
    _, _, _ = position
    dx, dy, dz = direction
    mag = math.sqrt(dx * dx + dy * dy + dz * dz)
    if mag < 1e-6:
        dx, dy, dz = 1.0, 0.0, 0.0
        mag = 1.0
    dx /= mag
    dy /= mag
    dz /= mag

    scale_fac = scale

    # 2D silhouette from top view (nose, wings, tail) to create a rough shape
    nose = np.array([1.5, 0.0]) * scale_fac
    left_wing  = np.array([0.0, -0.8]) * scale_fac
    right_wing = np.array([0.0,  0.8]) * scale_fac
    tail       = np.array([-1.3, 0.0]) * scale_fac
    thickness = 0.15 * scale_fac

    top_pts: list[list[float]] = [
        [nose[0],  nose[1],  thickness],
        [right_wing[0], right_wing[1], thickness],
        [tail[0],  tail[1],  thickness],
        [left_wing[0], left_wing[1], thickness],
    ]
    bottom_pts: list[list[float]] = [
        [nose[0],  nose[1],  -thickness],
        [right_wing[0], right_wing[1], -thickness],
        [tail[0],  tail[1],  -thickness],
        [left_wing[0], left_wing[1], -thickness],
    ]

    # Construct faces for a basic 3D poly
    faces: List[List[Tuple[float, float, float]]] = []
    faces.append([(top_pts[0][0], top_pts[0][1], top_pts[0][2]),
                (top_pts[1][0], top_pts[1][1], top_pts[1][2]),
                (top_pts[2][0], top_pts[2][1], top_pts[2][2]),
                (top_pts[3][0], top_pts[3][1], top_pts[3][2])])
    faces.append([(bottom_pts[0][0], bottom_pts[0][1], bottom_pts[0][2]),
                (bottom_pts[1][0], bottom_pts[1][1], bottom_pts[1][2]),
                (bottom_pts[2][0], bottom_pts[2][1], bottom_pts[2][2]),
                (bottom_pts[3][0], bottom_pts[3][1], bottom_pts[3][2])])
    for i in range(4):
        i2 = (i + 1) % 4
        faces.append([
            (top_pts[i][0], top_pts[i][1], top_pts[i][2]),
            (top_pts[i2][0], top_pts[i2][1], top_pts[i2][2]),
            (bottom_pts[i2][0], bottom_pts[i2][1], bottom_pts[i2][2]),
            (bottom_pts[i][0], bottom_pts[i][1], bottom_pts[i][2])
        ])

    forward = np.array([dx, dy, dz])
    up_guess = np.array([0.0, 0.0, 1.0])
    side = np.cross(forward, up_guess)
    side_mag = np.linalg.norm(side)
    if side_mag < 1e-6:
        side = np.cross(forward, [1.0, 0.0, 0.0])
        side_mag = np.linalg.norm(side)
    side /= side_mag
    up = np.cross(side, forward)

    R = np.vstack([forward, side, up]).T  # 3x3 rotation matrix

    def transform_local(pt: Tuple[float, float, float]) -> NDArray[np.float64]:
        local = np.array(pt)
        return position + R.dot(local)

    face_world: List[List[Tuple[float, float, float]]] = []
    for f in faces:
        face_w: List[Tuple[float, float, float]] = []
        for v_ in f:
            transformed = transform_local(v_)
            face_w.append(tuple(transformed))
        face_world.append(face_w)

    poly: Poly3DCollection = Poly3DCollection(face_world, facecolor=color, alpha=1.0)
    poly.set_edgecolor((0, 0, 0, 1)) #type: ignore # black edge
    return poly

###############################################################################
# SECTION 16. BULLETS, BOMBS, ROCKETS, COUNTERMEASURES <Dynamic engagement ammo>
###############################################################################
def clamp_xyz_arrays(
    x_: NDArray[np.float64],
    y_: NDArray[np.float64],
    z_: NDArray[np.float64]
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:

    min_len = min(len(x_), len(y_), len(z_))
    return (x_[:min_len], y_[:min_len], z_[:min_len])

def simulate_bullet_trajectory(
    plane_pos: Tuple[float, float, float],
    plane_vel: Tuple[float, float, float],
    muzzle_speed: float = 11200.0,
    dt: float = 0.02,
    max_time: float = 0.5,
    gravity: float = 9.81
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:

    px, py, pz = plane_pos
    vx_p, vy_p, vz_p = plane_vel

    spd_plane_3d = math.sqrt(vx_p**2 + vy_p**2 + vz_p**2)
    if spd_plane_3d < 1e-6:
        dx_, dy_, dz_ = (1.0, 0.0, 0.0)
    else:
        dx_, dy_, dz_ = (vx_p / spd_plane_3d, vy_p / spd_plane_3d, vz_p / spd_plane_3d)

    bullet_speed = spd_plane_3d + muzzle_speed
    vx_ = bullet_speed * dx_
    vy_ = bullet_speed * dy_
    vz_ = bullet_speed * dz_

    bx, by, bz = [px], [py], [pz]
    t = 0.0
    while t < max_time:
        x_new = bx[-1] + vx_ * dt
        y_new = by[-1] + vy_ * dt
        z_new = bz[-1] + vz_ * dt
        vz_ -= gravity * dt

        if z_new <= 0.0:
            z_new = 0.0
            bx.append(x_new)
            by.append(y_new)
            bz.append(z_new)
            break

        bx.append(x_new)
        by.append(y_new)
        bz.append(z_new)
        t += dt

    return clamp_xyz_arrays(np.array(bx), np.array(by), np.array(bz))

def spawn_bullets(
    px: float,
    py: float,
    pz: float,
    vx: float,
    vy: float,
    vz: float,
    muzzle_speed: float = 1200.0,
    num_bullets: int = 8
) -> None:

    for _ in range(num_bullets):
        bx_, by_, bz_ = simulate_bullet_trajectory(
            (px, py, pz),
            (vx, vy, vz),
            muzzle_speed=muzzle_speed
        )
        active_bullets.append({
            'x': bx_,
            'y': by_,
            'z': bz_,
            'index': 0,
            'scatter': None
        })

def simulate_rocket_trajectory(
    plane_pos: Tuple[float, float, float],
    plane_vel: Tuple[float, float, float],
    rocket_speed: float = 12800.0,
    dt: float = 0.05,
    max_time: float = 1.0,
    thrust_dur: float = 2.0
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:

    px, py, pz = plane_pos
    vx_p, vy_p, vz_p = plane_vel
    spd_3d = math.sqrt(vx_p**2 + vy_p**2 + vz_p**2)
    if spd_3d < 1e-6:
        dx_, dy_, dz_ = (1.0, 0.0, 0.0)
    else:
        dx_, dy_, dz_ = (vx_p / spd_3d, vy_p / spd_3d, vz_p / spd_3d)

    vx_r = (spd_3d + rocket_speed) * dx_
    vy_r = (spd_3d + rocket_speed) * dy_
    vz_r = (spd_3d + rocket_speed) * dz_

    rx, ry, rz = [px], [py], [pz]
    g = 9.81
    t = 0.0
    while t < max_time:
        if t < thrust_dur:
            vx_r += 15.0 * dt * dx_
            vy_r += 15.0 * dt * dy_
            vz_r += 15.0 * dt * dz_

        nx = rx[-1] + vx_r * dt
        ny = ry[-1] + vy_r * dt
        nz = rz[-1] + vz_r * dt
        vz_r -= g * dt

        if nz <= 0.0:
            nz = 0.0
            rx.append(nx)
            ry.append(ny)
            rz.append(nz)
            break

        rx.append(nx)
        ry.append(ny)
        rz.append(nz)
        t += dt

    return clamp_xyz_arrays(np.array(rx), np.array(ry), np.array(rz))

def spawn_rocket(
    px: float,
    py: float,
    pz: float,
    vx: float,
    vy: float,
    vz: float
) -> None:

    rx_, ry_, rz_ = simulate_rocket_trajectory((px, py, pz), (vx, vy, vz))
    active_rockets.append({
        'x': rx_,
        'y': ry_,
        'z': rz_,
        'index': 0,
        'scatter': None
    })

###############################################################################
# SECTION 17. BOMB <Add the bullets and rockets and countermeasures here as well>
###############################################################################
TARGET_POSITION = (12000, 7250, 0.0)  # A ground target or central point
TARGET_RADIUS   = 80.0               # direct hit threshold if bomb ends near target

bomb_s, bomb_e = phase_slices["Bombing"]
bomb_drop_frame = bomb_s + 5  # <= Force drop early in the Bombing phase

bomb_x: NDArray[np.float64] = np.array([], dtype=np.float64)
bomb_y: NDArray[np.float64] = np.array([], dtype=np.float64)
bomb_z: NDArray[np.float64] = np.array([], dtype=np.float64)

bomb_marker = None
bomb_explosion_triggered = False
bomb_impact_point: Optional[Tuple[float, float, float]] = None
bomb_outcome_text  = ""

def simulate_bomb_trajectory(
    x_init: float,
    y_init: float,
    z_init: float,
    vx_init: float,
    vy_init: float,
    vz_init: float = 0.0,
    dt: float = 0.5,
    drag_coefficient: float = 0.001,  # Lower drag => faster, increase for more realistic slow-down
    max_time: float = 30.0             # 30s max flight
) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:

    g = 9.81  # Gravitational acceleration in m/s^2
    bx = [x_init]
    by = [y_init]
    bz = [z_init]

    vx = vx_init
    vy = vy_init
    vz = vz_init

    t = 0.0
    while t < max_time:
        # Update position based on velocity
        x_new = bx[-1] + vx * dt
        y_new = by[-1] + vy * dt
        z_new = bz[-1] + vz * dt

        # Calculate the speed of the bomb
        speed = math.sqrt(vx*vx + vy*vy + vz*vz)

        # Apply drag force
        if speed > 1e-6:
            drag_force = drag_coefficient * (speed**2)
            drag_x = drag_force * (vx / speed)
            drag_y = drag_force * (vy / speed)
            drag_z = drag_force * (vz / speed)
            vx -= drag_x * dt
            vy -= drag_y * dt
            vz -= drag_z * dt

        # Apply gravity (pull downward)
        vz -= g * dt

        # If bomb hits the ground, stop it
        if z_new <= 0.0:
            bx.append(x_new)
            by.append(y_new)
            bz.append(0.0)  # Bomb hits the ground
            break

        bx.append(x_new)
        by.append(y_new)
        bz.append(z_new)
        t += dt

    return (
        np.array(bx, dtype=np.float64),
        np.array(by, dtype=np.float64),
        np.array(bz, dtype=np.float64)
    )

###############################################################################
# SECTION 18. ANIMATION UTILS
###############################################################################
def update_explosion():
    global explosion_active, explosion_frame, explosion_poly
    if not explosion_active:
        return
    if explosion_poly:
        explosion_poly.remove()
        explosion_poly = None

    frac = explosion_frame / float(explosion_max_frames)
    r_ = 20.0 + 120.0 * frac
    th, ph = np.mgrid[0:np.pi:15j, 0:2*np.pi:15j]
    xs_ = r_ * np.sin(th) * np.cos(ph) + explosion_center[0]
    ys_ = r_ * np.sin(th) * np.sin(ph) + explosion_center[1]
    zs_ = r_ * np.cos(th) + explosion_center[2]

    explosion_poly = ax_main.plot_surface(xs_, ys_, zs_, color='white',  # type: ignore
                                        alpha=1, edgecolor='orange')  # type: ignore
    explosion_frame += 1
    if explosion_frame >= explosion_max_frames:
        explosion_active = False
        if explosion_poly:
            explosion_poly.remove()
            explosion_poly = None

def update_parachute():
    global parachute_active, parachute_frame, parachute_poly
    if not parachute_active:
        return
    if parachute_poly:
        parachute_poly.remove()
        parachute_poly = None

    t_ = parachute_frame
    dx_ = parachute_center[0] + 10.0 * math.sin(0.1 * t_)
    dy_ = parachute_center[1] + 10.0 * math.cos(0.1 * t_)
    dz_ = parachute_center[2] - 3.0 * t_
    if dz_ < 0:
        dz_ = 0

    sz_ = 50
    h_ = sz_ / 2
    corners_ = [
        (dx_ - h_, dy_ - h_, dz_ + 20),
        (dx_ + h_, dy_ - h_, dz_ + 20),
        (dx_ + h_, dy_ + h_, dz_ + 20),
        (dx_ - h_, dy_ + h_, dz_ + 20),
    ]
    faces_ = [[corners_[0], corners_[1], corners_[2], corners_[3]]]
    p_ = Poly3DCollection(faces_, facecolors='white', alpha=0.8)
    p_.set_edgecolor('red')  # type: ignore
    ax_main.add_collection3d(p_)  # type: ignore
    parachute_poly = p_

    parachute_frame += 1
    if dz_ <= 0:
        parachute_active = True
        if parachute_poly:
            parachute_poly.remove()
            parachute_poly = None

###############################################################################
# SECTION 19. INIT + UPDATE (FINAL FIXED VERSION, with Bomb Logic Updated)
###############################################################################
def safe_remove_poly(poly_obj: Optional[Poly3DCollection]) -> None:
    if poly_obj is not None:
        try:
            poly_obj.remove()
        except Exception:
            pass

bearcat_poly: Optional[Poly3DCollection] = None
bogie_poly: Optional[Poly3DCollection] = None
lockon_line: Optional[Line2D] = None
lockon_line_radius = 300.0
lockon_line_shrink = 3.0
target_destroyed_text: Optional[Text] = None
bogie_is_hit = False
bogie_hit_frame: Optional[int] = None

def init_animation() -> tuple[()]:
    return ()

def update_animation(frame: int) -> tuple[()]:
    global bearcat_poly, bogie_poly
    global bomb_marker, bomb_explosion_triggered
    global bomb_x, bomb_y, bomb_z
    global bogie_is_hit, bogie_hit_frame
    global lockon_line, lockon_line_radius
    global target_destroyed_text
    global explosion_active
    global bomb_impact_point, bomb_outcome_text
    global bomb_drop_frame
    global lockon_line
    global target_destroyed_text

    # 1) Remove old Bearcat model
    safe_remove_poly(bearcat_poly)
    bearcat_poly = None

    # 2) Determine plane's current position
    if frame < frames_total:
        bcx = flight_x[frame]
        bcy = flight_y[frame]
        bcz = flight_z[frame]
    else:
        bcx = bcy = bcz = 0.0

    # 3) Plane velocity from last frame => used for bullets, rockets, bomb
    dt_frame = 0.08
    if frame > 0:
        dx_ = flight_x[frame] - flight_x[frame - 1]
        dy_ = flight_y[frame] - flight_y[frame - 1]
        dz_ = flight_z[frame] - flight_z[frame - 1]
        vx_ = dx_ / dt_frame
        vy_ = dy_ / dt_frame
        vz_ = dz_ / dt_frame
    else:
        vx_ = vy_ = vz_ = 0.0

    # 4) Redraw the Bearcat
    bearcat_poly = create_bearcat_model(
        (bcx, bcy, bcz),
        (vx_, vy_, vz_),
        scale=80,
        color='white'
    )
    ax_main.add_collection3d(bearcat_poly)  # type: ignore

    # 5) Bomb logic: Drop the bomb if 'frame' matches bomb_drop_frame
    if frame == bomb_drop_frame:
        # Generate bomb trajectory
        bomb_x, bomb_y, bomb_z = simulate_bomb_trajectory(
            x_init=bcx,
            y_init=bcy,
            z_init=bcz,
            vx_init=vx_,
            vy_init=vy_,
            vz_init=vz_,
            dt=0.50,
            drag_coefficient=0.001,
            max_time=30.0
        )
        bomb_explosion_triggered = False
        bomb_outcome_text = ""

    # Remove the old bomb marker if it exists
    if bomb_marker:
        bomb_marker.remove()

    # Now figure out the index in the bomb arrays to draw
    bomb_marker_local = None
    bomb_frame_idx = frame - bomb_drop_frame
    if 0 <= bomb_frame_idx < len(bomb_x):
        bx_ = bomb_x[bomb_frame_idx]
        by_ = bomb_y[bomb_frame_idx]
        bz_ = bomb_z[bomb_frame_idx]
        alt = bz_

        blink_speed = max(1, 10 - int(alt / 100))  # Adjust blink speed based on altitude
        cycle_position = (frame // blink_speed) % 4  # Cycle through 4 colors

        if cycle_position == 0:
            color = 'white'
        elif cycle_position == 1:
            color = 'red'
        elif cycle_position == 2:
            color = 'yellow'
        else:
            color = 'orange'

        if alt > 0:
            bomb_marker_local = ax_main.scatter([bx_], [by_], [bz_], color=color, s=50, marker='o')  # type: ignore
        elif alt <= 0 and not bomb_explosion_triggered:
            bomb_explosion_triggered = True
            spawn_explosion((bx_, by_, 0.0))  # Trigger explosion when bomb hits the ground

    bomb_marker = bomb_marker_local

    # If we triggered an explosion, display the text
    if bomb_explosion_triggered and bomb_outcome_text:
        ax_main.text(  # type: ignore
            TARGET_POSITION[0],
            TARGET_POSITION[1],
            20.0,
            bomb_outcome_text,
            color='yellow',
            fontsize=11
        )  # type: ignore
        bomb_outcome_text = ""

    # 6) Fallback if we exit the Bombing phase but never saw an impact
    bomb_s, bomb_e = phase_slices["Bombing"]
    if frame == (bomb_e + 5) and not bomb_explosion_triggered and len(bomb_x) > 0:
        bomb_explosion_triggered = True
        last_bx = bomb_x[-1]
        last_by = bomb_y[-1]
        spawn_explosion((last_bx, last_by, 0.0))
        dist2target = math.hypot(last_bx - TARGET_POSITION[0],
                                last_by - TARGET_POSITION[1])
        if dist2target <= TARGET_RADIUS:
            bomb_outcome_text = f"Bomb (fallback) HIT (dist={dist2target:.1f}m)"
        else:
            bomb_outcome_text = f"Bomb (fallback) MISS ~{dist2target:.1f}m"
        ax_main.text(  # type: ignore
            TARGET_POSITION[0],
            TARGET_POSITION[1],
            20.0,
            bomb_outcome_text,
            color='yellow',
            fontsize=11
        )  # type: ignore
        bomb_outcome_text = ""

    safe_remove_poly(bogie_poly)
    bogie_poly = None

    # Bogie logic
    safe_remove_poly(bogie_poly)
    bogie_poly = None
    if frame < frames_total and bogie_is_hit and bogie_hit_frame is not None:
        if not np.isnan(bogie_x[frame]):
            f_since_hit = frame - bogie_hit_frame
            if f_since_hit < 0:
                f_since_hit = 0
            old_x = bogie_x[bogie_hit_frame]
            old_y = bogie_y[bogie_hit_frame]
            old_z = bogie_z[bogie_hit_frame]
            angle_ = 0.3 * f_since_hit
            radius_ = 40.0 + 5.0 * f_since_hit
            nx_ = old_x + radius_ * math.cos(angle_)
            ny_ = old_y + radius_ * math.sin(angle_)
            nz_ = old_z - 20.0 * f_since_hit
            if nz_ < 0.0:
                nz_ = 0.0
            bogie_x[frame] = nx_
            bogie_y[frame] = ny_
            bogie_z[frame] = nz_
            if nz_ <= 0.0 and not explosion_active:
                spawn_explosion((nx_, ny_, 0.0))
                spawn_parachute((nx_, ny_, 0.0))

    if frame < frames_total:
        btx = bogie_x[frame]
        bty = bogie_y[frame]
        btz = bogie_z[frame]
        if frame > 0 and not np.isnan(bogie_x[frame - 1]):
            vx_b = bogie_x[frame] - bogie_x[frame - 1]
            vy_b = bogie_y[frame] - bogie_y[frame - 1]
            vz_b = bogie_z[frame] - bogie_z[frame - 1]
        else:
            vx_b = vy_b = vz_b = 0.0
        if not np.isnan(btx):
            bogie_poly = create_bearcat_model(
                (btx, bty, btz),
                (vx_b, vy_b, vz_b),
                scale=100,
                color='pink'
            )
            ax_main.add_collection3d(bogie_poly)  # type: ignore

    # Strafe logic
    strafe_s, strafe_e = phase_slices["Strafe"]
    if lockon_line:
        lockon_line.remove()
        lockon_line = None  # type: ignore
    if strafe_s <= frame < strafe_e:
        if lockon_line_radius > 0.0:
            a_ = np.linspace(0, 2 * math.pi, 36)
            center_ = (10000, 7000, 0)
            xx_ = center_[0] + lockon_line_radius * np.cos(a_)
            yy_ = center_[1] + lockon_line_radius * np.sin(a_)
            zz_ = np.full_like(xx_, 10.0)
            lockon_line = ax_main.plot(xx_, yy_, zz_, color='yellow', linewidth=1.5)[0]  # type: ignore
            lockon_line_radius = max(lockon_line_radius - lockon_line_shrink, 0.0)
        else:
            lockon_line_radius = 300.0
        if frame == strafe_e:
            if target_destroyed_text:
                target_destroyed_text.remove()
            target_destroyed_text = ax_main.text(  # type: ignore
                10000, 7000, 100,
                "Target Destroyed",
                color='red',
                fontsize=16
            )
        if (frame % 10 == 0) and (frame > 0):
            spawn_bullets(
                px=bcx, py=bcy, pz=bcz,
                vx=vx_, vy=vy_, vz=vz_,
                muzzle_speed=19900.0,
                num_bullets=8
            )

    # Bombing => rocket as an example
    bomb_s, bomb_e = phase_slices["Bombing"]
    mid_bomb = bomb_s + (bomb_e - bomb_s) // 2
    # If we want to fire rockets in the middle of the bomb run
    if frame in {mid_bomb, mid_bomb + 5} and frame > 0:
        spawn_rocket(bcx, bcy, bcz, vx_, vy_, vz_)

    # Dogfight logic
    dog_s, dog_e = phase_slices["Dogfight"]
    if dog_s <= frame < dog_e:
        if (frame % 10 == 0) and (frame > 0):
            spawn_bullets(
                px=bcx, py=bcy, pz=bcz,
                vx=vx_, vy=vy_, vz=vz_,
                muzzle_speed=19900.0,
                num_bullets=8
            )
        if (frame % 10 == 0) and (frame > 0) and not bogie_is_hit:
            bx_ = bogie_x[frame]
            by_ = bogie_y[frame]
            bz_ = bogie_z[frame]
            if not np.isnan(bx_):
                vx_b2 = bogie_x[frame] - bogie_x[frame - 1]
                vy_b2 = bogie_y[frame] - bogie_y[frame - 1]
                vz_b2 = bogie_z[frame] - bogie_z[frame - 1]
                spawn_bullets(
                    px=bx_, py=by_, pz=bz_,
                    vx=vx_b2, vy=vy_b2, vz=vz_b2,
                    muzzle_speed=19900.0,
                    num_bullets=8
                )
        half_dog = dog_s + (dog_e - dog_s)//2
        if frame == half_dog and not bogie_is_hit:
            bogie_is_hit = True
            bogie_hit_frame = frame

    # Update bullets
    done_bullets: List[Dict[str, Any]] = []
    for bullet in active_bullets:
        if bullet['index'] < len(bullet['x']) - 1:
            bullet['index'] += 2
            if bullet['index'] >= len(bullet['x']):
                bullet['index'] = len(bullet['x']) - 1
            idx_ = bullet['index']
            if bullet['scatter'] is None:
                sc_ = ax_main.scatter([], [], [], color='yellow', marker='.', s=20)  # type: ignore
                bullet['scatter'] = sc_
            bx_ = bullet['x'][idx_]
            by_ = bullet['y'][idx_]
            bz_ = bullet['z'][idx_]
            bullet['scatter']._offsets3d = (  # type: ignore
                np.array([bx_]),
                np.array([by_]),
                np.array([bz_])
            )
        else:
            if bullet['scatter']:
                bullet['scatter'].remove()
            bullet['scatter'] = None
            done_bullets.append(bullet)
    for b_ in done_bullets:
        active_bullets.remove(b_)

# Update rockets
    done_rockets: List[Dict[str, Any]] = []
    for rocket in active_rockets:
        if rocket['index'] < len(rocket['x']) - 1:
            rocket['index'] += 1
            idx_ = rocket['index']

            if rocket['scatter'] is None:
                sc_: Line3DCollection = ax_main.scatter([], [], [], color='magenta', marker='^', s=30)  # type: ignore
                rocket['scatter'] = sc_

            # Get the current position of the rocket
            rx_ = rocket['x'][idx_]
            ry_ = rocket['y'][idx_]
            rz_ = rocket['z'][idx_]

            # Fast cycling of colors based on the frame number
            cycle_speed = 5  # Adjust this number to control how fast the colors cycle
            cycle_position = (frame // cycle_speed) % 4  # Cycle through 4 colors

            # Set the color based on the cycle position
            if cycle_position == 0:
                color = 'magenta'
            elif cycle_position == 1:
                color = 'cyan'
            elif cycle_position == 2:
                color = 'blue'
            else:
                color = 'pink'

            # Update the rocket scatter point with the new color
            rocket['scatter']._offsets3d = (np.array([rx_]), np.array([ry_]), np.array([rz_]))
            rocket['scatter'].set_color(color)  # type: ignore # Change the color of the rocket

        else:
            if rocket['scatter']:
                rocket['scatter'].remove()
            rocket['scatter'] = None
            done_rockets.append(rocket)

    # Remove rockets that are done
    for rk_ in done_rockets:
        active_rockets.remove(rk_)

    # Explosion and parachute updates
    update_explosion()
    update_parachute()

    # AAA geometry updates
    for c_ in list(ax_main.collections):
        if getattr(c_, '_aaa_flag', False):
            c_.remove()

    gx1, gy1, gz1 = ground_aaa_position(frame, 10000, 7000, 700)
    if frame < frames_total:
        ax_ = flight_x[frame] - gx1
        ay_ = flight_y[frame] - gy1
        angle_aaa = math.degrees(math.atan2(ay_, ax_))
    else:
        angle_aaa = 0.0
    faces1 = create_aaa_geometry(gx1, gy1, gz1, size_base=180, height_base=100, size_turret=90, turret_angle_deg=angle_aaa)
    col1 = Poly3DCollection(faces1, facecolor='red', alpha=1.0)
    col1.set_edgecolor('black')  # type: ignore
    setattr(col1, '_aaa_flag', True)
    ax_main.add_collection3d(col1)  # type: ignore

    gx2, gy2, gz2 = ground_aaa_position(frame + 30, 15000, 7500, 900)
    if frame < frames_total:
        ax2_ = flight_x[frame] - gx2
        ay_ = flight_y[frame] - gy2
        angle_aaa2 = math.degrees(math.atan2(ay_, ax2_))
    else:
        angle_aaa2 = 0.0
    faces2 = create_aaa_geometry(gx2, gy2, gz2, size_base=200, height_base=100, size_turret=90, turret_angle_deg=angle_aaa2)
    col2 = Poly3DCollection(faces2, facecolor='red', alpha=1.0)
    col2.set_edgecolor('black')  # type: ignore
    setattr(col2, '_aaa_flag', True)
    ax_main.add_collection3d(col2)  # type: ignore

    return ()

###############################################################################
# SECTION 20. RUN (REPEAT ENABLED)
###############################################################################
anim = FuncAnimation(
    fig,
    update_animation,
    init_func=init_animation,
    frames=frames_total,
    interval=30,
    blit=False,
    repeat=True
)

plt.show()  # type: ignore
