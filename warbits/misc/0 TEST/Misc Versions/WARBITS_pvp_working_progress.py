import multiprocessing
from typing import Any, Dict, List, Optional
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D  # type: ignore
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # type: ignore


active_bullets: List[Dict[str, Any]] = []
active_rockets: List[Dict[str, Any]] = []

targets = []
target_destroyed = []

bogie_poly: Optional[Poly3DCollection]

CURRENT_VEHICLE_TYPE: str = "AIRCRAFT"
SELECTED_VEHICLE: str = "F8F1_Bearcat"

def attempt_full_cpu_usage():
    # Example placeholder
    print("Attempting to utilize all available CPU cores.")
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    pool.close()
    pool.join()

def attempt_full_gpu_usage():
    # Example placeholder
    print("Attempting to leverage GPU if possible (PyOpenGL or CUDA).")

# -------------------------------------------------------------------------
# 1. BEARCAT MASTER DATA (All referenced & expanded) -- unchanged
# -------------------------------------------------------------------------
F8F1_Bearcat_Data: Dict[str, Any] = {
    "Name": "F8F-1 Bearcat",
    "Nation": "USA",
    "Type": "Naval Fighter (Carrier-Based)",
    "BR_Realistic": 4.7,
    "Crew": 1,
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
        "Engine_Cooling_Required_sec": 50
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
        "Bombs_and_Rockets": {
            "Bomb_Hardpoints": 1,
            "1x_1000_lb_Bomb_ANM65A1": {
                "Damage_Radius_m": (15, 25),
                "Fragmentation_Radius_m": 50,
                "Weight_Effect_on_Handling": {
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
        "One of the fastest piston-engine aircraft developed near war’s end",
        "Introduced too late for WWII combat deployment",
        "Used post-war, saw limited action in Indochina War (French forces)"
    ]
}

# -------------------------------------------------------------------------
# 2. ADDITIONAL ADVANCED DATA (unchanged, for reference)
# -------------------------------------------------------------------------
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
        "Drop_300m": "High (95% hit probability vs. stationary target)",
        "Drop_600m": "Very Good (80-90%)",
        "Drop_1200m": "Moderate (50-60%)",
        "CCIP": {
            "Below_300m": "98% accuracy",
            "Between_300m_800m": "Minor corrections needed",
            "Above_1000m": "Manual lead adjustment required",
            "Deviation_Above_400mph": "Crosshair may deviate by ~3-5m"
        },
        "Wind_Effect_on_Bomb_Drop": {
            "Up_to_1000m_Altitude": "Negligible",
            "Above_1000m": "Slight leftward drift, adjust CCIP accordingly"
        }
    },
    "Real_vs_Game_Bomb_Physics": {
        "Gravity_Model": "War Thunder uses simplified gravity with weaker drag force",
        "Shockwave_Pressure_At_10m": "≈2.5 atm",
        "Blast_Radius_Scaling": "~25m lethal, ~50m partial damage"
    },
    "Dogfight_Stats": {
        "vs_FW190A": "Win ~100% if energy advantage, 75% head-on",
        "vs_P51D": "Win ~40% if same energy, 60% head-on, better turning at low speed",
        "vs_SpitfireIX": "Win ~50% if BnZ, lose ~90% in sustained turn",
        "vs_Yak3U": "Win ~60% if vertical, lose ~85% in pure turn fight",
        "Bomb_Load_Impact": "Carrying bombs reduces turn rate by ~15% and roll rate by ~8%. Dropping bombs immediately restores normal flight."
    }
}


###############################################################################
# 2. VISUAL STYLE
###############################################################################
mpl.rcParams['figure.facecolor'] = 'black'
mpl.rcParams['axes.facecolor']   = 'black'
mpl.rcParams['axes.edgecolor']   = '(0.05,0.05,0.1)'
mpl.rcParams['axes.linewidth']   = 1
mpl.rcParams['grid.color']       = "none"
mpl.rcParams['grid.alpha']       = 0
mpl.rcParams['grid.linestyle']   = ':'
mpl.rcParams['axes.grid']        = False
mpl.rcParams['figure.dpi']       = 75
mpl.rcParams['savefig.dpi']      = 120
mpl.rcParams['savefig.facecolor'] = 'black'
mpl.rcParams['savefig.edgecolor'] = 'black'
mpl.rcParams['savefig.transparent'] = True
mpl.rcParams['font.family']      = 'sans-serif'
mpl.rcParams['font.size']        = 10
mpl.rcParams['axes.labelsize']   = 10
mpl.rcParams['axes.titlesize']   = 10
mpl.rcParams['axes.titleweight'] = 'bold'
mpl.rcParams['axes.titlecolor']  = '#FF0000'
mpl.rcParams['legend.fontsize']  = 8
mpl.rcParams['legend.frameon']   = True
mpl.rcParams['legend.fancybox']  = True
mpl.rcParams['legend.framealpha']= 1
mpl.rcParams['legend.edgecolor'] = 'none'
mpl.rcParams['xtick.color']      = 'none'
mpl.rcParams['ytick.color']      = 'none'
mpl.rcParams['axes.prop_cycle']  = cycler(color=[
    "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
    "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"
])
mpl.rcParams['lines.linewidth']       = 1.0
mpl.rcParams['lines.markersize']      = 5
mpl.rcParams['lines.markeredgewidth'] = 1.3
mpl.rcParams['axes.spines.top']       = True
mpl.rcParams['axes.spines.right']     = True
mpl.rcParams['axes.spines.left']      = True
mpl.rcParams['axes.spines.bottom']    = False
mpl.rcParams['axes.xmargin']          = 0.02
mpl.rcParams['axes.ymargin']          = 0.02
mpl.rcParams['lines.antialiased']     = True
mpl.rcParams['patch.antialiased']     = True
mpl.rcParams['lines.solid_capstyle']  = 'butt'
mpl.rcParams['lines.solid_joinstyle'] = 'miter'
mpl.rcParams['lines.dash_capstyle']   = 'butt'
mpl.rcParams['lines.dash_joinstyle']  = 'miter'
mpl.rcParams['xtick.major.size']      = 10
mpl.rcParams['xtick.minor.size']      = 3
mpl.rcParams['xtick.direction']       = 'in'
mpl.rcParams['xtick.top']             = False
mpl.rcParams['ytick.left']            = True
mpl.rcParams['axes.unicode_minus']    = True
mpl.rcParams['axes.autolimit_mode']   = 'round_numbers'
mpl.rcParams['axes.axisbelow']        = True
mpl.rcParams['toolbar']               = 'None'
mpl.rcParams['figure.figsize']        = (10,8)


# -------------------------------------------------------------------------
# 3. ADVANCED SIMULATION SETUP (Approach -> Strafe -> Bombing -> Escape)
# -------------------------------------------------------------------------
def plot_arrowed_3d_line(ax: Axes3D,
                         x: np.ndarray[Any, np.dtype[np.float64]],
                         y: np.ndarray[Any, np.dtype[np.float64]],
                         z: np.ndarray[Any, np.dtype[np.float64]],
                         color: str = 'blue',
                         label: str = '',
                         arrow_interval: int = 5,
                         arrow_len: int = 700) -> None:
    """Plots a 3D line with repeated arrow markers for visual clarity."""
    ax.plot(x, y, z, color=color, linewidth=2, label=label)
    for i in range(0, len(x) - 1, arrow_interval):
        ax.quiver(
            x[i], y[i], z[i],
            x[i+1] - x[i], y[i+1] - y[i], z[i+1] - z[i],
            color=color, length=arrow_len, normalize=True, arrow_length_ratio=0.3
        )

def generate_terrain(xmin: int = 0, xmax: int = 16000,
                     ymin: int = 4000, ymax: int = 10000,
                     step: int = 60, amplitude: int = 300) -> tuple[
    np.ndarray[np.float64, np.dtype[np.float64]],
    np.ndarray[np.float64, np.dtype[np.float64]],
    np.ndarray[np.float64, np.dtype[np.float64]]
]:
    """Create a simple random/noise-based terrain for advanced visuals."""
    x_vals = np.linspace(xmin, xmax, step)
    y_vals = np.linspace(ymin, ymax, step)
    X, Y = np.meshgrid(x_vals, y_vals)
    np.random.seed(42)
    Z_vals = amplitude * 0.2 * np.sin(X / 1000.0) * np.cos(Y / 1000.0)
    Z_vals += amplitude * 0.3 * np.random.rand(step, step)
    return X, Y, Z_vals

def ground_target_path(t, start_x, start_y, z0=0):
    """Circle around the center (like a moving ground vehicle)."""
    radius = 500
    angle = 2 * np.pi * t
    gx = start_x + radius * np.cos(angle)
    gy = start_y + radius * np.sin(angle)
    gz = z0
    return gx, gy, gz

def create_cube_vertices(cx, cy, cz, size=50):
    """Return 8 vertices of a cube centered at (cx, cy, cz)."""
    d = size / 2.0
    offsets = [
        (-d, -d, -d), ( d, -d, -d),
        ( d,  d, -d), (-d,  d, -d),
        (-d, -d,  d), ( d, -d,  d),
        ( d,  d,  d), (-d,  d,  d)
    ]
    verts = [(cx+ox, cy+oy, cz+oz) for (ox, oy, oz) in offsets]
    return np.array(verts)

def simulate_bomb_trajectory(x_init, y_init, z_init,
                             vx_init=0, vy_init=0, vz_init=-50,
                             dt=0.1, drag=0.0005, max_time=30.0):
    """
    Ballistic simulation with XY drag + half gravity (per War Thunder’s “feel”).
    """
    g = 9.81 * 0.5
    bomb_x = [x_init]
    bomb_y = [y_init]
    bomb_z = [z_init]
    vx, vy, vz = vx_init, vy_init, vz_init
    t = 0
    while t < max_time:
        x_new = bomb_x[-1] + vx * dt
        y_new = bomb_y[-1] + vy * dt
        z_new = bomb_z[-1] + vz * dt

        # horizontal drag
        speed_xy = np.sqrt(vx**2 + vy**2)
        drag_force = drag * (speed_xy**2)
        if speed_xy > 0.01:
            vx -= drag_force * (vx / speed_xy) * dt
            vy -= drag_force * (vy / speed_xy) * dt

        vz -= g * dt

        # ground collision
        if z_new <= 0:
            z_new = 0
            bomb_x.append(x_new)
            bomb_y.append(y_new)
            bomb_z.append(z_new)
            break

        bomb_x.append(x_new)
        bomb_y.append(y_new)
        bomb_z.append(z_new)
        t += dt

    return np.array(bomb_x), np.array(bomb_y), np.array(bomb_z)

# -------------------------------------------------------------------------
# 4. PATHS (Approach -> Strafe -> Bombing -> Escape)
# -------------------------------------------------------------------------
phases = {
    "Approach": ("blue", 60),
    "Strafe":   ("orange", 50),
    "Bombing":  ("red", 50),
    "Escape":   ("green", 60)
}

# Phase A: Approach
num_A = phases["Approach"][1]
x_approach = np.linspace(0, 6000, num_A)
y_approach = 8000 + 1000 * np.sin(x_approach / 800.0)
z_approach = np.linspace(3000, 2200, num_A)

# Phase B: Strafe
num_B = phases["Strafe"][1]
x_strafe = np.linspace(x_approach[-1], 10000, num_B)
y_strafe = np.linspace(y_approach[-1], 7000, num_B)
z_strafe = np.linspace(z_approach[-1], 200, num_B)

# Phase C: Bombing
num_C = phases["Bombing"][1]
x_bomb = np.linspace(x_strafe[-1], 15000, num_C)
y_bomb = np.linspace(y_strafe[-1], 7500, num_C)
z_bomb = np.linspace(z_strafe[-1], 1200, num_C)

# Phase D: Escape
num_D = phases["Escape"][1]
x_escape = np.linspace(x_bomb[-1], 7000, num_D)
y_escape = 6000 + 1500 * np.cos((x_escape - x_bomb[-1]) / 900.0)
z_escape = np.linspace(z_bomb[-1], 4000, num_D)

# Combine full flight path
flight_x = np.concatenate([x_approach, x_strafe, x_bomb, x_escape])
flight_y = np.concatenate([y_approach, y_strafe, y_bomb, y_escape])
flight_z = np.concatenate([z_approach, z_strafe, z_bomb, z_escape])
frames_total = len(flight_x)

# -------------------------------------------------------------------------
# 5. BOMB ARC
# -------------------------------------------------------------------------
plane_vx = 100
plane_vy = 0
plane_vz = -10
bomb_init_x = x_bomb[-1]
bomb_init_y = y_bomb[-1]
bomb_init_z = z_bomb[-1]

bomb_x, bomb_y, bomb_z = simulate_bomb_trajectory(
    bomb_init_x,
    bomb_init_y,
    bomb_init_z,
    vx_init=plane_vx,
    vy_init=plane_vy,
    vz_init=plane_vz,
    dt=0.05,
    drag=0.0004,
    max_time=40.0
)

# -------------------------------------------------------------------------
# 6. ENEMY (BOGIE) INTERCEPT PATH
# -------------------------------------------------------------------------
enemy_frames = frames_total
enemy_x = np.full(enemy_frames, None, dtype=float)
enemy_y = np.full(enemy_frames, None, dtype=float)
enemy_z = np.full(enemy_frames, None, dtype=float)

enemy_appear_frame = num_A + num_B + (num_C // 2)
frames_for_enemy_approach = frames_total - enemy_appear_frame
x_start_enemy = 20000
y_start_enemy = 7500
z_start_enemy = 500
x_end_enemy   = 7500
y_end_enemy   = 6500
z_end_enemy   = 3000

for i in range(enemy_appear_frame, frames_total):
    f = (i - enemy_appear_frame) / float(frames_for_enemy_approach - 1)
    enemy_x[i] = x_start_enemy + (x_end_enemy - x_start_enemy)*f
    enemy_y[i] = y_start_enemy + (y_end_enemy - y_start_enemy)*f
    enemy_z[i] = z_start_enemy + (z_end_enemy - z_start_enemy)*f

# -------------------------------------------------------------------------
# 7. CREATE FIGURE (REMOVED INVALID figsize, ADDED FULLSCREEN TOGGLE)
# -------------------------------------------------------------------------
fig = plt.figure()
manager = plt.get_current_fig_manager()
manager.full_screen_toggle()

ax_main: Axes3D = fig.add_subplot(111, projection='3d')

xmin, xmax = 0, 18500
ymin, ymax = 4000, 9300
step, amplitude = (100, 800)

ax_main.set_xlim(xmin, xmax)
ax_main.set_ylim(ymin, ymax)
ax_main.set_zlim(0, 15000)

ax_main.xaxis.pane.set_facecolor((0,0,0,0))  # type: ignore
ax_main.yaxis.pane.set_facecolor((0,0,0,0))  # type: ignore
ax_main.zaxis.pane.set_facecolor((0,0,0,0))  # type: ignore
ax_main.xaxis.pane.set_edgecolor((0,0,0,0))  # type: ignore
ax_main.yaxis.pane.set_edgecolor((0,0,0,0))  # type: ignore
ax_main.zaxis.pane.set_edgecolor((0,0,0,0))  # type: ignore

x_terr, y_terr, z_terr = generate_terrain()
ax_main.plot_surface(x_terr, y_terr, z_terr, cmap='terrain',
                     alpha=0.2, edgecolor='none')

ax_main.set_title("F8F-1 Bearcat 3D (Approach->Strafe->Bomb->Escape->Dogfight)")
ax_main.set_xlabel("X (m)")
ax_main.set_ylabel("Y (m)")
ax_main.set_zlabel("Altitude (m)")
ax_main.set_xlim(0, 16000)
ax_main.set_ylim(5000, 9000)
ax_main.set_zlim(0, 5000)
ax_main.view_init(elev=30, azim=-60)

plot_arrowed_3d_line(ax_main, x_approach, y_approach, z_approach,
                     phases["Approach"][0], "Phase A: Approach")
plot_arrowed_3d_line(ax_main, x_strafe, y_strafe, z_strafe,
                     phases["Strafe"][0], "Phase B: Strafe")
plot_arrowed_3d_line(ax_main, x_bomb, y_bomb, z_bomb,
                     phases["Bombing"][0], "Phase C: Bombing")
plot_arrowed_3d_line(ax_main, x_escape, y_escape, z_escape,
                     phases["Escape"][0], "Phase D: Escape")

ax_main.plot(bomb_x, bomb_y, bomb_z, 'r--', linewidth=2, label="Bomb Arc")

ground_target_strafe_center = (10000, 7000, 0)
ground_target_bomb_center   = (15000, 7500, 0)
ax_main.scatter(ground_target_strafe_center[0],
                ground_target_strafe_center[1],
                ground_target_strafe_center[2],
                color='brown', s=200, marker='^', label="Strafe Target")

bogie_marker_init = ax_main.scatter([], [], [], color='red', s=120,
                                    marker='o', label="Bogie")

plt.tight_layout()

# -------------------------------------------------------------------------
# 8. ANIMATION INFRASTRUCTURE
# -------------------------------------------------------------------------
bearcat_marker = ax_main.scatter([], [], [], color='cyan', s=80,
                                 marker='o', edgecolors='k')
bogie_marker   = ax_main.scatter([], [], [], color='red',  s=120,
                                 marker='o', edgecolors='w')

cube1_plots = []
cube2_plots = []

def ground_target_motion(frame, total_frames, center):
    t = frame / total_frames
    return ground_target_path(t, center[0], center[1], center[2])

def init_animation():
    bearcat_marker._offsets3d = ([], [], [])
    bogie_marker._offsets3d   = ([], [], [])
    return (bearcat_marker, bogie_marker, *cube1_plots, *cube2_plots)

def update_ground_cube(ax, frame, total_frames, center,
                       cube_plots, size=150, color='brown'):
    for p in cube_plots:
        p.remove()
    cube_plots.clear()

    gx, gy, gz = ground_target_motion(frame, total_frames, center)
    c_verts = create_cube_vertices(gx, gy, gz, size=size)

    faces = [
        [c_verts[0], c_verts[1], c_verts[2], c_verts[3]],
        [c_verts[4], c_verts[5], c_verts[6], c_verts[7]],
        [c_verts[0], c_verts[1], c_verts[5], c_verts[4]],
        [c_verts[2], c_verts[3], c_verts[7], c_verts[6]],
        [c_verts[1], c_verts[2], c_verts[6], c_verts[5]],
        [c_verts[4], c_verts[7], c_verts[3], c_verts[0]],
    ]
    col = Poly3DCollection(faces, facecolors=color, alpha=0.9)
    col.set_edgecolor('white')
    ax.add_collection3d(col)
    cube_plots.append(col)

# -------------------------------------------------------------------------
# 9. WEAPONS SIMULATIONS
# -------------------------------------------------------------------------
def simulate_bullet_trajectory(plane_pos, plane_vel, muzzle_speed=890.0,
                               dt=0.02, max_time=2.0, gravity=9.81):
    px, py, pz = plane_pos
    vx_plane, vy_plane, vz_plane = plane_vel
    vx_bullet = vx_plane + muzzle_speed
    vy_bullet = vy_plane
    vz_bullet = vz_plane

    bullet_x = [px]
    bullet_y = [py]
    bullet_z = [pz]
    t = 0
    while t < max_time:
        x_new = bullet_x[-1] + vx_bullet * dt
        y_new = bullet_y[-1] + vy_bullet * dt
        z_new = bullet_z[-1] + vz_bullet * dt
        vz_bullet -= gravity * dt
        if z_new <= 0:
            z_new = 0
            bullet_x.append(x_new)
            bullet_y.append(y_new)
            bullet_z.append(z_new)
            break
        bullet_x.append(x_new)
        bullet_y.append(y_new)
        bullet_z.append(z_new)
        t += dt
    return np.array(bullet_x), np.array(bullet_y), np.array(bullet_z)

active_bullets = []
def spawn_bullets(plane_x, plane_y, plane_z, plane_vx, plane_vy, plane_vz,
                  num_bullets=1, muzzle_speed=890):
    bullet_x, bullet_y, bullet_z = simulate_bullet_trajectory(
        (plane_x, plane_y, plane_z),
        (plane_vx, plane_vy, plane_vz),
        muzzle_speed=muzzle_speed
    )
    bullet_dict = {
        'x': bullet_x,
        'y': bullet_y,
        'z': bullet_z,
        'index': 0,
        'line': None
    }
    active_bullets.append(bullet_dict)

def simulate_rocket_trajectory(plane_pos, plane_vel, rocket_speed=320.0,
                               dt=0.05, max_time=10.0, thrust_duration=3.0):
    px, py, pz = plane_pos
    vx_plane, vy_plane, vz_plane = plane_vel
    vx_r = vx_plane + rocket_speed
    vy_r = vy_plane
    vz_r = vz_plane
    g = 9.81
    rx_list = [px]
    ry_list = [py]
    rz_list = [pz]
    t = 0
    while t < max_time:
        if t < thrust_duration:
            vx_r += 5.0 * dt  # naive forward acceleration
        vz_r -= g * dt
        x_new = rx_list[-1] + vx_r * dt
        y_new = ry_list[-1] + vy_r * dt
        z_new = rz_list[-1] + vz_r * dt
        if z_new <= 0:
            z_new = 0
            rx_list.append(x_new)
            ry_list.append(y_new)
            rz_list.append(z_new)
            break
        rx_list.append(x_new)
        ry_list.append(y_new)
        rz_list.append(z_new)
        t += dt
    return np.array(rx_list), np.array(ry_list), np.array(rz_list)

active_rockets = []
def spawn_rocket(plane_x, plane_y, plane_z, plane_vx, plane_vy, plane_vz):
    rx, ry, rz = simulate_rocket_trajectory(
        (plane_x, plane_y, plane_z),
        (plane_vx, plane_vy, plane_vz),
        rocket_speed=320.0
    )
    rocket_dict = {
        'x': rx,
        'y': ry,
        'z': rz,
        'index': 0,
        'line': None
    }
    active_rockets.append(rocket_dict)

# -------------------------------------------------------------------------
# 10. EXPLOSION ANIMATION
# -------------------------------------------------------------------------
explosion_active = False
explosion_frame = 0
explosion_max_frames = 30
explosion_poly = None
explosion_center = None

def spawn_explosion(center):
    global explosion_active, explosion_frame, explosion_center, explosion_poly
    explosion_active = True
    explosion_frame = 0
    explosion_center = center
    if explosion_poly is not None:
        explosion_poly.remove()
        explosion_poly = None

def update_explosion(ax):
    global explosion_active, explosion_frame, explosion_max_frames
    global explosion_poly, explosion_center

    if not explosion_active:
        return

    if explosion_poly is not None:
        explosion_poly.remove()
        explosion_poly = None

    fraction = explosion_frame / float(explosion_max_frames)
    radius = 10 + 90 * fraction

    theta, phi = np.mgrid[0:np.pi:15j, 0:2*np.pi:15j]
    x_sphere = radius * np.sin(theta) * np.cos(phi) + explosion_center[0]
    y_sphere = radius * np.sin(theta) * np.sin(phi) + explosion_center[1]
    z_sphere = radius * np.cos(theta) + explosion_center[2]

    explosion_poly = ax.plot_surface(
        x_sphere, y_sphere, z_sphere,
        color='orange', alpha=0.4, edgecolor='none'
    )

    explosion_frame += 1
    if explosion_frame >= explosion_max_frames:
        explosion_active = False
        if explosion_poly is not None:
            explosion_poly.remove()
            explosion_poly = None

import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

###############################################################################
# GLOBAL SIMULATION STATE (All instrument data in one place)
###############################################################################
SIM_STATE = {
    "altitude_m": 0.0,
    "speed_m_s": 0.0,
    "pitch_deg": 0.0,
    "roll_deg": 0.0,
    "yaw_deg": 0.0,
    "engine_temp_c": 150.0,
    "engine_rpm": 2600.0,
    "manifold_inhg": 45.0,
    "throttle_pct": 100.0,
    "wep_time_s": 0.0,
    "ammo_count": 4 * 1250,
    "bombs_carried": 1,
    "rockets_carried": 8,
    "overheat_warning": False
}

###############################################################################
# 11. PLOT THE 3D SCENES <ADD ALL INSTRUMENTS FOR MORE ACCURATE PANEL READINGS>
###############################################################################
fig = plt.figure(figsize=(25,19))
gs = gridspec.GridSpec(nrows=12, ncols=12, figure=fig)

# -------------------------- Main 3D Plot --------------------------
ax_main = fig.add_subplot(gs[:, 0:8], projection='3d')
xmin, xmax = 0, 18500
ymin, ymax = 4000, 9300
step, amplitude = 100, 800
ax_main.set_xlim(xmin, xmax)
ax_main.set_ylim(ymin, ymax)
ax_main.set_zlim(0, 5000)
ax_main.xaxis.pane.set_facecolor((0,0,0,0))
ax_main.yaxis.pane.set_facecolor((0,0,0,0))
ax_main.zaxis.pane.set_facecolor((0,0,0,0))
ax_main.xaxis.pane.set_edgecolor((0,0,0,0))
ax_main.yaxis.pane.set_edgecolor((0,0,0,0))
ax_main.zaxis.pane.set_edgecolor((0,0,0,0))

xt_, yt_, zt_ = generate_terrain()
ax_main.plot_surface(xt_, yt_, zt_, cmap='terrain', alpha=0.2, edgecolor='none')
ax_main.set_title("F8F-1 Bearcat 3D (Approach->Strafe->Bomb->Escape->Dogfight)")
ax_main.set_xlabel("X (m)")
ax_main.set_ylabel("Y (m)")
ax_main.set_zlabel("Altitude (m)")
ax_main.set_xlim(0,16000)
ax_main.set_ylim(5000,9000)
ax_main.set_zlim(0,5000)
ax_main.view_init(elev=30, azim=-60)

# -------------------------- HELPER: 3D BOX for Gauges --------------------------
def make_3d_box(center=(0,0,0), size=1.0):
    """Create a list-of-lists for faces of a cube, each face is 4 vertices."""
    cx, cy, cz = center
    d = size/2.0
    # 8 corners of a cube
    corners = [
        (cx-d, cy-d, cz-d), (cx+d, cy-d, cz-d),
        (cx+d, cy+d, cz-d), (cx-d, cy+d, cz-d),
        (cx-d, cy-d, cz+d), (cx+d, cy-d, cz+d),
        (cx+d, cy+d, cz+d), (cx-d, cy+d, cz+d)
    ]
    # 6 faces, each face is a list of 4 corners:
    faces = [
        [corners[0], corners[1], corners[2], corners[3]],
        [corners[4], corners[5], corners[6], corners[7]],
        [corners[0], corners[1], corners[5], corners[4]],
        [corners[2], corners[3], corners[7], corners[6]],
        [corners[1], corners[2], corners[6], corners[5]],
        [corners[4], corners[7], corners[3], corners[0]],
    ]
    return faces

def rotate_points_xyz(points, pitch_deg=0, roll_deg=0, yaw_deg=0):
    """Apply basic Euler rotations to a list of (x,y,z) points in degrees."""
    # Convert to radians
    p = np.radians(pitch_deg)
    r = np.radians(roll_deg)
    y = np.radians(yaw_deg)
    # Rotation matrices
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(p), -np.sin(p)],
                   [0, np.sin(p),  np.cos(p)]])
    Ry = np.array([[ np.cos(r), 0, np.sin(r)],
                   [0,          1, 0        ],
                   [-np.sin(r), 0, np.cos(r)]])
    Rz = np.array([[np.cos(y), -np.sin(y), 0],
                   [np.sin(y),  np.cos(y), 0],
                   [0,          0,         1]])
    # Combined rotation (order: pitch->roll->yaw, or adjust to your liking)
    R = Rz @ Ry @ Rx

    rotated = []
    for (xx, yy, zz) in points:
        vec = np.array([xx, yy, zz])
        # Apply rotation
        xyz_new = R @ vec
        rotated.append(tuple(xyz_new))
    return rotated

# -------------------------- 1) Flight Instruments (Attitude, etc.) --------------------------
ax_instrument_flight = fig.add_subplot(gs[0:3, 8:12], projection='3d')
ax_instrument_flight.set_title("Flight Instruments")

def update_flight_instruments(ax_instrument_flight, frame_idx):
    ax_instrument_flight.clear()
    ax_instrument_flight.set_title("Flight Instruments")
    ax_instrument_flight.set_axis_off()

    # Example: Draw a 3D box “Attitude Cube” that rotates with pitch/roll
    center = (0,0,0)
    faces = make_3d_box(center, size=1.0)
    # Now rotate the box according to SIM_STATE['pitch_deg'] and SIM_STATE['roll_deg']
    pitch = SIM_STATE["pitch_deg"]
    roll  = SIM_STATE["roll_deg"]
    yaw   = SIM_STATE["yaw_deg"]   # if you want heading
    new_faces = []
    for face in faces:
        rotated_face = rotate_points_xyz(face, pitch, roll, yaw)
        new_faces.append(rotated_face)
    poly = Poly3DCollection(new_faces, alpha=0.4, facecolors='blue')
    poly.set_edgecolor('white')
    ax_instrument_flight.add_collection3d(poly)

    # Adjust the 3D view area
    ax_instrument_flight.set_xlim(-2,2)
    ax_instrument_flight.set_ylim(-2,2)
    ax_instrument_flight.set_zlim(-2,2)

# -------------------------- 2) Engine / Power Instruments --------------------------
ax_instrument_engine = fig.add_subplot(gs[3:5, 8:10], projection='3d')
ax_instrument_engine.set_title("Engine Status")

def update_engine_instruments(ax_instrument_engine, frame_idx):
    ax_instrument_engine.clear()
    ax_instrument_engine.set_title("Engine Status")
    ax_instrument_engine.set_axis_off()

    # Example: Draw a rotating “needle” to represent engine RPM
    # We'll place a "needle" along x-axis, rotate it up for higher RPM
    rpm = SIM_STATE["engine_rpm"]
    # Suppose min=0, max=3000 => angle up to ~ 90 deg
    angle = np.clip((rpm / 3000.0)*90.0, 0, 90)
    # Build a short rod as a face
    rod_length = 1.5
    rod_face = [
        (0,0,0), (rod_length, 0, 0),
        (rod_length,0,0.1), (0,0,0.1)
    ]
    # Convert to 3D face list
    # We'll do a single face => minimal shape
    rotated_rod = rotate_points_xyz(rod_face, pitch_deg=angle, roll_deg=0, yaw_deg=0)
    rod_poly = [rotated_rod]
    poly = Poly3DCollection(rod_poly, alpha=0.6, facecolors='yellow')
    poly.set_edgecolor('black')
    ax_instrument_engine.add_collection3d(poly)

    ax_instrument_engine.set_xlim(-2,2)
    ax_instrument_engine.set_ylim(-2,2)
    ax_instrument_engine.set_zlim(-2,2)

# -------------------------- 3) Weapons / Ammo Instruments --------------------------
ax_instrument_weapons = fig.add_subplot(gs[3:5, 10:12], projection='3d')
ax_instrument_weapons.set_title("Weapons Readout")

def update_weapons_instruments(ax_instrument_weapons, frame_idx):
    ax_instrument_weapons.clear()
    ax_instrument_weapons.set_title("Weapons Readout")
    ax_instrument_weapons.set_axis_off()

    bombs = SIM_STATE["bombs_carried"]
    rockets = SIM_STATE["rockets_carried"]
    ammo = SIM_STATE["ammo_count"]

    # Example: show a 3D “stack” of ammo boxes
    # Each box is 1 in Y, so total = ammo/100 if you like
    boxes = int(ammo/200)  # each box = 200 rounds
    y_offset = 0
    for i in range(boxes):
        faces = make_3d_box(center=(0,y_offset,0), size=0.4)
        c = Poly3DCollection(faces, alpha=0.4, facecolors='green')
        c.set_edgecolor('white')
        ax_instrument_weapons.add_collection3d(c)
        y_offset += 0.5

    # Possibly draw bombs as big cubes, rockets as smaller cubes, etc.
    # For demonstration, place 1 bomb if bombs>0
    if bombs>0:
        bomb_faces = make_3d_box(center=(1,0,0), size=0.5)
        bc = Poly3DCollection(bomb_faces, alpha=0.5, facecolors='red')
        bc.set_edgecolor('black')
        ax_instrument_weapons.add_collection3d(bc)

    # For rockets, place them in a line
    for i in range(rockets):
        rocket_faces = make_3d_box(center=(-1, i*0.3, 0), size=0.2)
        rc = Poly3DCollection(rocket_faces, alpha=0.5, facecolors='gray')
        rc.set_edgecolor('white')
        ax_instrument_weapons.add_collection3d(rc)

    ax_instrument_weapons.set_xlim(-2,2)
    ax_instrument_weapons.set_ylim(-2,4)
    ax_instrument_weapons.set_zlim(-1,2)

# -------------------------- 4) Ground Vehicle Instruments --------------------------
ax_instrument_ground = fig.add_subplot(gs[5:7, 8:10], projection='3d')
ax_instrument_ground.set_title("Ground Vehicle")
def update_ground_instruments(ax_instrument_ground, frame_idx):
    ax_instrument_ground.clear()
    ax_instrument_ground.set_title("Ground Vehicle")
    ax_instrument_ground.set_axis_off()

    # If using a tank, you might have a 3D tank turret shape rotating
    # For now, placeholder
    boxfaces = make_3d_box(center=(0,0,0), size=1.0)
    col = Poly3DCollection(boxfaces, alpha=0.3, facecolors='brown')
    col.set_edgecolor('white')
    ax_instrument_ground.add_collection3d(col)

    ax_instrument_ground.set_xlim(-2,2)
    ax_instrument_ground.set_ylim(-2,2)
    ax_instrument_ground.set_zlim(-2,2)

# -------------------------- 5) Naval Systems Instruments --------------------------
ax_instrument_naval = fig.add_subplot(gs[5:7, 10:12], projection='3d')
ax_instrument_naval.set_title("Naval Systems")
def update_naval_instruments(ax_instrument_naval, frame_idx):
    ax_instrument_naval.clear()
    ax_instrument_naval.set_title("Naval Systems")
    ax_instrument_naval.set_axis_off()
    # Possibly show rudder angle, throttle, depth charges, etc.
    # Placeholder
    rudder_box = make_3d_box(center=(0,0,0), size=1.0)
    col = Poly3DCollection(rudder_box, alpha=0.3, facecolors='blue')
    col.set_edgecolor('white')
    ax_instrument_naval.add_collection3d(col)

    ax_instrument_naval.set_xlim(-2,2)
    ax_instrument_naval.set_ylim(-2,2)
    ax_instrument_naval.set_zlim(-2,2)

# -------------------------- 6) Helicopter Instruments --------------------------
ax_instrument_rotor = fig.add_subplot(gs[7:9, 8:10], projection='3d')
ax_instrument_rotor.set_title("Helicopter")
def update_rotor_instruments(ax_instrument_rotor, frame_idx):
    ax_instrument_rotor.clear()
    ax_instrument_rotor.set_title("Helicopter")
    ax_instrument_rotor.set_axis_off()
    # Possibly show main rotor pitch, tail rotor deflection, etc.
    # Placeholder
    rotor = make_3d_box(center=(0,0,0), size=1.0)
    col = Poly3DCollection(rotor, alpha=0.3, facecolors='purple')
    col.set_edgecolor('white')
    ax_instrument_rotor.add_collection3d(col)

    ax_instrument_rotor.set_xlim(-2,2)
    ax_instrument_rotor.set_ylim(-2,2)
    ax_instrument_rotor.set_zlim(-2,2)

# -------------------------- 7) Advanced Nav (GPS, INS, Radar) --------------------------
ax_instrument_nav = fig.add_subplot(gs[7:9, 10:12], projection='3d')
ax_instrument_nav.set_title("Advanced Nav")
def update_nav_instruments(ax_instrument_nav, frame_idx):
    ax_instrument_nav.clear()
    ax_instrument_nav.set_title("Advanced Nav")
    ax_instrument_nav.set_axis_off()
    # Possibly show rotating radar sweep, GPS map in 3D, etc.
    # Placeholder
    nav_box = make_3d_box(center=(0,0,0), size=1.0)
    col = Poly3DCollection(nav_box, alpha=0.3, facecolors='green')
    col.set_edgecolor('white')
    ax_instrument_nav.add_collection3d(col)

    ax_instrument_nav.set_xlim(-2,2)
    ax_instrument_nav.set_ylim(-2,2)
    ax_instrument_nav.set_zlim(-2,2)

# -------------------------- 8) Real-Time Controls (Cockpit Overlay) --------------------------
ax_instrument_controls = fig.add_subplot(gs[9:12, 8:12])
ax_instrument_controls.set_title("Real-Time Controls")
ax_instrument_controls.set_facecolor('black')

def cockpit_control_overlay(ax_instrument_controls, frame_idx):
    """
    Master overlay with text readouts from SIM_STATE + correct dt scoping.
    """
    # We'll define dt at the top so we never get 'unbound' errors:
    dt = 0.08  # approximate sim-time per frame

    # For demonstration, let's imagine we do more advanced logic updating SIM_STATE
    # e.g. if throttle changes, engine_rpm changes, etc.
    # The final draws:
    ax_instrument_controls.clear()
    ax_instrument_controls.set_title("")
    ax_instrument_controls.set_axis_off()

    # Build lines from SIM_STATE
    alt_ft = SIM_STATE["altitude_m"] * 3.28084
    speed_mph = SIM_STATE["speed_m_s"] * 2.23694

    data_lines = []
    data_lines.append(f"Frame: {frame_idx}")
    data_lines.append(f"Altitude: {alt_ft:,.0f} ft (~{SIM_STATE['altitude_m']:,.0f} m)")
    data_lines.append(f"Speed: {speed_mph:5.1f} mph")
    data_lines.append(f"Pitch: {SIM_STATE['pitch_deg']:.1f}°, Roll: {SIM_STATE['roll_deg']:.1f}°")
    data_lines.append(f"Throttle: {SIM_STATE['throttle_pct']:.0f}%")
    if SIM_STATE["throttle_pct"] > 100:
        data_lines.append(f"WEP: ACTIVE ({SIM_STATE['wep_time_s']:.1f}s)")
    else:
        data_lines.append("WEP: OFF")
    data_lines.append(f"Engine Temp: {SIM_STATE['engine_temp_c']:.1f} C{' (OVERHEAT!)' if SIM_STATE['overheat_warning'] else ''}")
    data_lines.append(f"RPM: {SIM_STATE['engine_rpm']:.0f}, Manifold: {SIM_STATE['manifold_inhg']:.1f}\"Hg")
    data_lines.append(f"Ammo: {SIM_STATE['ammo_count']} rds")
    data_lines.append(f"Bombs: {SIM_STATE['bombs_carried']}  Rockets: {SIM_STATE['rockets_carried']}")

    ax_instrument_controls.text(
        0.95, 0.05,
        "\n".join(data_lines),
        color='red',
        fontsize=10,
        ha='right',
        va='bottom',
        transform=ax_instrument_controls.transAxes
    )

# -------------------------- 9) Single call to update all instruments --------------------------
def update_all_instruments(frame_idx):
    # 1) Possibly recalc or update SIM_STATE from your main flight logic here
    # e.g. SIM_STATE['pitch_deg'] = ...
    # e.g. SIM_STATE['engine_temp_c'] = ...
    # e.g. handle dt/time in WEP, etc.

    # 2) Then draw each instrument:
    update_flight_instruments(ax_instrument_flight, frame_idx)
    update_engine_instruments(ax_instrument_engine, frame_idx)
    update_weapons_instruments(ax_instrument_weapons, frame_idx)
    update_ground_instruments(ax_instrument_ground, frame_idx)
    update_naval_instruments(ax_instrument_naval, frame_idx)
    update_rotor_instruments(ax_instrument_rotor, frame_idx)
    update_nav_instruments(ax_instrument_nav, frame_idx)
    cockpit_control_overlay(ax_instrument_controls, frame_idx)

    # Return an empty list or a list of artists if using blit
    return []

plt.tight_layout()


# -------------------------------------------------------------------------
# 12. MAIN UPDATE FUNCTION (ORIGINAL)
# -------------------------------------------------------------------------
def update_animation(frame):
    # Update Bearcat position
    if frame < frames_total:
        bx = flight_x[frame]
        by = flight_y[frame]
        bz = flight_z[frame]
        bearcat_marker._offsets3d = ([bx], [by], [bz])
    else:
        bx, by, bz = flight_x[-1], flight_y[-1], flight_z[-1]

    # Update bogie
    if enemy_x[frame] is not None:
        ex = enemy_x[frame]
        ey = enemy_y[frame]
        ez = enemy_z[frame]
        bogie_marker._offsets3d = ([ex], [ey], [ez])
    else:
        bogie_marker._offsets3d = ([], [], [])

    update_ground_cube(ax_main, frame, frames_total,
                       ground_target_strafe_center, cube1_plots,
                       size=150, color='brown')
    update_ground_cube(ax_main, frame, frames_total,
                       ground_target_bomb_center,   cube2_plots,
                       size=150, color='black')

    # Strafe Phase bullets
    strafe_start = num_A
    strafe_end   = num_A + num_B
    if strafe_start <= frame < strafe_end:
        if frame % 5 == 0:
            if frame > 0:
                vx_plane = flight_x[frame] - flight_x[frame - 1]
                vy_plane = flight_y[frame] - flight_y[frame - 1]
                vz_plane = flight_z[frame] - flight_z[frame - 1]
            else:
                vx_plane = vy_plane = vz_plane = 0
            spawn_bullets(bx, by, bz, vx_plane, vy_plane, vz_plane, num_bullets=1)

    # Bombing Phase rockets
    bomb_start = strafe_end
    bomb_end   = strafe_end + num_C
    mid_bomb_frame = bomb_start + (num_C // 2)
    if frame == mid_bomb_frame or frame == (mid_bomb_frame + 5):
        if frame > 0:
            vx_plane = flight_x[frame] - flight_x[frame - 1]
            vy_plane = flight_y[frame] - flight_y[frame - 1]
            vz_plane = flight_z[frame] - flight_z[frame - 1]
        else:
            vx_plane = vy_plane = vz_plane = 0
        spawn_rocket(bx, by, bz, vx_plane, vy_plane, vz_plane)

    # Update bullets
    for bullet in active_bullets:
        if bullet['index'] < len(bullet['x']) - 1:
            bullet['index'] += 1
            idx = bullet['index']
            if bullet['line'] is None:
                bullet_line, = ax_main.plot([], [], [], color='yellow', linewidth=2)
                bullet['line'] = bullet_line
            bx_ = bullet['x'][:idx]
            by_ = bullet['y'][:idx]
            bz_ = bullet['z'][:idx]
            bullet['line'].set_data_3d(bx_, by_, bz_)
        else:
            if bullet['line'] is not None:
                bullet['line'].remove()
                bullet['line'] = None
    active_bullets[:] = [b for b in active_bullets if b['index'] < len(b['x']) - 1]

    # Update rockets
    for rocket in active_rockets:
        if rocket['index'] < len(rocket['x']) - 1:
            rocket['index'] += 1
            idx = rocket['index']
            if rocket['line'] is None:
                rocket_line, = ax_main.plot([], [], [], color='magenta', linewidth=2)
                rocket['line'] = rocket_line
            rx_ = rocket['x'][:idx]
            ry_ = rocket['y'][:idx]
            rz_ = rocket['z'][:idx]
            rocket['line'].set_data_3d(rx_, ry_, rz_)
        else:
            if rocket['line'] is not None:
                rocket['line'].remove()
                rocket['line'] = None
    active_rockets[:] = [r for r in active_rockets if r['index'] < len(r['x']) - 1]

    # Check bomb impact => Explosion
    if frame == bomb_end + 5:
        bomb_impact_point = (bomb_x[-1], bomb_y[-1], 0)
        spawn_explosion(bomb_impact_point)

    update_explosion(ax_main)

    # Return artists for matplotlib
    return (
        bearcat_marker,
        bogie_marker,
        *cube1_plots,
        *cube2_plots,
        *(b['line'] for b in active_bullets if b['line'] is not None),
        *(r['line'] for r in active_rockets if r['line'] is not None)
    )

# -------------------------------------------------------------------------
# 13. WRAP THE UPDATE TO INCLUDE COCKPIT OVERLAY
# -------------------------------------------------------------------------
original_update_animation = update_animation

def update_animation_with_cockpit(frame):
    returned_artists = original_update_animation(frame)
    cockpit_control_overlay(ax_ctrl, frame)
    return returned_artists

# -------------------------------------------------------------------------
# 14. ANIMATE
# -------------------------------------------------------------------------
anim = FuncAnimation(
    fig,
    update_animation_with_cockpit,
    init_func=init_animation,
    frames=frames_total,
    interval=80,
    blit=False
)

plt.show()
