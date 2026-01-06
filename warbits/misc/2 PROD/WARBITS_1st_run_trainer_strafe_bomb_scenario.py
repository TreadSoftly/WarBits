import random

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

# F8F-1 Bearcat data without .50 cal or climb-rate specifics
F8F1_Bearcat = {
    "Name": "F8F-1 Bearcat",
    "Nation": "USA",
    "Type": "Naval Fighter (Carrier-Based)",
    "BR_Realistic": 4.7,
    "Crew": 1,
    "Performance": {
        "Engine": "Pratt & Whitney R-2800-34W",
        "Horsepower": 2100,
        "Max_Speed_mph_alt": 440,
        "Max_Speed_Sea_Level_mph": 384,
        "Max_Speed_kmh": 708,
        "Altitude_Based_Speeds": {
            "Sea_Level_0ft": 384,
            "5000ft": 360,
            "10000ft": 385,
            "14000ft": 440
        },
        "Acceleration_Throttle_SeaLevel_mph": 335,
        "Acceleration_Throttle_5000ft_mph": 362,
        "Acceleration_Throttle_10000ft_mph": 388,
        "Turn_Time_sec_flaps_up": 19.0,
        "Turn_Time_sec_combat_flaps": 17.8,
        "Roll_Rate_deg_s": 140,
        "Stall_Speed_mph": 108,
        "Wing_Loading_lb_ft2": 58.2,
        "Drag_Coefficients": {
            "Flaps_Down_Multiplier": 1.18,
            "Gear_Down_Multiplier": 1.22,
            "Damage_Multipliers": [1.08, 1.4]
        },
        "G_Limits": {
            "Symmetrical": 8,
            "Rolling_Snap": 5
        },
        "RealTime_G_Force_Calculations": True,
        "Snap_Roll_Limit_Simulation": True,
        "High_AoA_Stall_Behavior": True
    },
    "Armament": {
        # Entirely removing .50 cal machine gun details
        "Bombs_and_Rockets": {
            "Bomb_Hardpoints": 1,
            "Bomb_Type": "AN-M65A1 1000 lb GP",
            "Bomb_Refinements": {
                "Direct_Impact_Lethal_m": 20,
                "Fragmentation_Spread_m": 55,
                "Pressure_Wave_Simulation": True
            },
            "Altitude_Based_Ballistic_Corrections": True,
            "Bomb_Drop_Accuracy": {
                "500m": "95%",
                "1200m": "50-60%",
                "3000m+": "30-40%"
            },
            "8x_HVAR_Rockets": {
                "Max_Range_m": 2400,
                "Penetration_mm": 60,
                "Deviation_at_1000m_percent": 2.5
            }
        }
    },
    "Advanced_Visual_Upgrades": {
        "Dynamic_Heatmaps_for_Explosions": True,
        "Debris_Scattering_Physics": True,
        "Wind_Resistance_for_Bomb_Drop": True,
        "Cloud_Obstruction_for_Ambush": True,
        "Strafe_Bomb_Animation_Sequences": True
        # Removed RealTime_BulletDrop_Tracking
    },
    "Dogfight_AI_Metrics": {
        "Enemy_Refinements": {
            "FW190A": {
                "Win_Rate": 95,
                "Avoid_Sustained_Turns": True
            },
            "P51D": {
                "Win_Rate": 65,
                "Use_Superior_Turn": True
            },
            "Spitfire_MkIX": {
                "Win_Rate": 50,
                "Best_in_Energy_Fight": True
            },
            "Yak3U": {
                "Win_Rate": 55,
                "Avoid_Prolonged_Fights": True
            }
        },
        "Evasive_Maneuvers": [
            "Rolling_Scissors",
            "High_G_Barrel_Roll",
            "Energy_Trap",
            "Jink_Maneuvers"
        ]
    }
}

Environment = {
    "Wind_Speed_m_s_range": [0, 15],
    "Turbulence_Threshold_m_s": 5,
    "Ground_AA_Threats": {
        "Flak_Accuracy_percent": 75,
        "Shell_Velocity_m_s": 850
    },
    "Damage_Model": {
        "Critical_Hits": {
            "Engine": 85,
            "Wing_Root": 65,
            "Cockpit": 90
        },
        "Control_Surfaces_Effectiveness_Loss_percent": {
            "Ailerons": 40,
            "Elevator": 50,
            "Rudder": 60
        },
        "Fire_Risk": {
            "Fuel_Tank": 80,
            "Engine": 65
        }
    }
}

def plot_line_with_arrows(ax, x, y, z, clr, lbl, arrow_int=5, arrow_len=700):
    ax.plot(x, y, z, color=clr, linewidth=2, label=lbl)
    for i in range(0, len(x)-1, arrow_int):
        ax.quiver(
            x[i], y[i], z[i],
            x[i+1]-x[i], y[i+1]-y[i], z[i+1]-z[i],
            color=clr, length=arrow_len, normalize=True, arrow_length_ratio=0.3
        )

phases = {
    "Approach": ("blue", 50),
    "Strafe": ("orange", 40),
    "Bombing": ("red", 40),
    "Escape": ("green", 50),
    "Dogfight": ("purple", 40)
}

# Generate each phase path
na = phases["Approach"][1]
xa = np.linspace(0, 6000, na)
ya = np.sin(xa / 1000) * 800 + 8000
za = np.linspace(3000, 2000, na)

nb = phases["Strafe"][1]
xb = np.linspace(xa[-1], 10000, nb)
yb = np.linspace(ya[-1], 7000, nb)
zb = np.linspace(za[-1], 150, nb)

nc = phases["Bombing"][1]
xc = np.linspace(xb[-1], 15000, nc)
yc = np.linspace(yb[-1], 7500, nc)
zc = np.linspace(zb[-1], 1200, nc)

nd = phases["Escape"][1]
xd = np.linspace(xc[-1], 7000, nd)
yd = np.cos(xd / 1000) * 2000 + 6000
zd = np.linspace(zc[-1], 4000, nd)

ne = phases["Dogfight"][1]
xe = np.linspace(xd[-1], 8000, ne)
ye = np.linspace(yd[-1], 4500, ne)
ze = np.linspace(zd[-1], 3800, ne)

ground_strafe = (10000, 7000, 0)
ground_bomb = (15000, 7500, 0)
enemy_pos = (8000, 4500, 3800)

# Simple parabolic bomb trajectory
def bomb_trajectory(distance):
    return max(0, 1200 - 0.001 * distance**2)

bpoints = 30
xx = np.linspace(xc[-1], ground_bomb[0], bpoints)
yy = np.linspace(yc[-1], ground_bomb[1], bpoints)
bombz = []
for i in range(bpoints):
    dist = xx[i] - xc[-1]
    bombz.append(bomb_trajectory(dist))

scenarios = [
    "Ground_Target_Destroyed",
    "Bomb_Hit_Directly",
    "Bomb_Hit_Near_Miss",
    "Dogfight_Engaged",
    "Bearcat_Damaged",
    "Multiple_Enemies",
    "Enemy_Fighter_Killed",
    "Enemy_Fighter_Escapes"
]
picked_scenario = random.choice(scenarios)

# --- MAIN VISUAL SIMULATION (no .50 cal / climb subplots) ---
fig = plt.figure()  # Remove the invalid figsize=(full screen)

# Toggle actual full screen (depends on your environment/backend)
manager = plt.get_current_fig_manager()
manager.full_screen_toggle()

ax_main = fig.add_subplot(111, projection='3d')

# Plot the path phases
plot_line_with_arrows(ax_main, xa, ya, za, phases["Approach"][0], "Phase A: Approach")
plot_line_with_arrows(ax_main, xb, yb, zb, phases["Strafe"][0], "Phase B: Strafe")
plot_line_with_arrows(ax_main, xc, yc, zc, phases["Bombing"][0], "Phase C: Bombing")
plot_line_with_arrows(ax_main, xd, yd, zd, phases["Escape"][0], "Phase D: Escape")
plot_line_with_arrows(ax_main, xe, ye, ze, phases["Dogfight"][0], "Phase E: Dogfight")

# Plot bomb trajectory (red dashed line)
ax_main.plot(xx, yy, bombz, 'r--', linewidth=2)

# Markers for ground targets & enemy position
ax_main.scatter(*ground_strafe, color='brown', s=100, marker='^')
ax_main.scatter(*ground_bomb, color='black', s=120, marker='X')
ax_main.scatter(*enemy_pos, color='red', s=120, marker='o')

# Optional bomb-hit zone visualization
th, ph = np.mgrid[0:np.pi:15j, 0:2*np.pi:15j]
rb = 25
xb_ = rb * np.sin(th) * np.cos(ph) + ground_bomb[0]
yb_ = rb * np.sin(th) * np.sin(ph) + ground_bomb[1]
zb_ = rb * np.cos(th) + ground_bomb[2]
ax_main.plot_surface(xb_, yb_, zb_, color='yellow', alpha=0.25, edgecolor='none')

ax_main.set_title("F8F-1 Bearcat Advanced Flight Trainer Scenario: " + picked_scenario)
ax_main.set_xlabel("X (m)")
ax_main.set_ylabel("Y (m)")
ax_main.set_zlabel("Z (m)")
ax_main.view_init(elev=30, azim=-60)
ax_main.legend()

# Combine all phases for the flight animation
fx = np.concatenate([xa, xb, xc, xd, xe])
fy = np.concatenate([ya, yb, yc, yd, ye])
fz = np.concatenate([za, zb, zc, zd, ze])

# Marker for the animated position
marker = ax_main.scatter([], [], [], color='cyan', s=80, marker='o', edgecolors='k')

def init_anim():
    marker._offsets3d = ([], [], [])
    return (marker,)

def update_anim(f):
    marker._offsets3d = ([fx[f]], [fy[f]], [fz[f]])
    return (marker,)

anim = FuncAnimation(fig, update_anim, init_func=init_anim, frames=len(fx), interval=100, blit=False)

plt.show()

# Print scenario outcome
print("SCENARIO RESULT:", picked_scenario)
if picked_scenario == "Ground_Target_Destroyed":
    print("Direct bomb hit on ground target.")
elif picked_scenario == "Bomb_Hit_Directly":
    print("Bomb landed directly on target. Maximum damage.")
elif picked_scenario == "Bomb_Hit_Near_Miss":
    print("Bomb missed by ~20m. Moderate damage.")
elif picked_scenario == "Dogfight_Engaged":
    print("Engaged by enemy fighter. Dogfight underway.")
elif picked_scenario == "Bearcat_Damaged":
    print("Bearcat sustained minor damage.")
elif picked_scenario == "Multiple_Enemies":
    print("Two enemy fighters engage. Consider retreat.")
elif picked_scenario == "Enemy_Fighter_Killed":
    print("Enemy fighter shot down.")
elif picked_scenario == "Enemy_Fighter_Escapes":
    print("Enemy escaped.")
    print("Enemy escaped.")
