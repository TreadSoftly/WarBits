import math
from typing import Any, Dict, List, Optional, Tuple  # type: ignore

import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler
from matplotlib.animation import \
    FuncAnimation  # to help linters see this is a 3D axis
from mpl_toolkits.mplot3d import Axes3D  # type: ignore
from mpl_toolkits.mplot3d.art3d import \
    Poly3DCollection  # type: ignore  # for 3D polygon collections
from numpy.typing import NDArray  # type: ignore

active_bullets: List[Dict[str, Any]] = []
active_rockets: List[Dict[str, Any]] = []
targets = []
target_destroyed = []

###############################################################################
# 0. VISUAL STYLE
###############################################################################
# figure.facecolor
plt.rcParams['figure.facecolor'] = "black"  # HPC combos: "white","none","#111111"
# axes.facecolor
plt.rcParams['axes.facecolor']   = 'black'  # IFR ops: "#303030","none","white"
# axes.edgecolor
plt.rcParams['axes.edgecolor']   = 'none'    # HPC highlight: "#FF0000","none"
# axes.linewidth
plt.rcParams['axes.linewidth']   = 1        # VR emphasize: 5, HPC big:10
# grid.color
plt.rcParams['grid.color']       = "none"     # IFR lines:"#444444", stealth:"none"
# grid.alpha
plt.rcParams['grid.alpha']       = 0          # partial 0.5 or invisible=0
# grid.linestyle
plt.rcParams['grid.linestyle']   = ':'        # IFR dotted=':', HPC='--'
# axes.grid
plt.rcParams['axes.grid']        = False      # IFR=True, minimal=False
# figure.dpi
plt.rcParams['figure.dpi']       = 75        # HPC max=600+, VR=300+
# savefig.dpi
plt.rcParams['savefig.dpi']      = 200        # HPC or doc=600+, quick=100
# font.size
plt.rcParams['font.size']        = 10         # VR=24+, HPC small=6
# axes.labelsize
plt.rcParams['axes.labelsize']   = 10         # HPC=14+, minimal=8
# axes.titlesize
plt.rcParams['axes.titlesize']   = 10         # VR=20+, HPC doc=14
# axes.titleweight
plt.rcParams['axes.titleweight'] = 'heavy'     # HPC flight='heavy'
# axes.titlecolor
plt.rcParams['axes.titlecolor']  = '#FF0000'  # IFR='white', HPC alert='#FF0000'
# legend.fontsize
plt.rcParams['legend.fontsize']  = 8          # HPC large=14, VR=20
# legend.frameon
plt.rcParams['legend.frameon']   = True       # minimal=False
# legend.fancybox
plt.rcParams['legend.fancybox']  = True       # corners: True=rounded, False=sharp
# legend.framealpha
plt.rcParams['legend.framealpha']= 0       # HPC=1, hidden=0
# legend.edgecolor
plt.rcParams['legend.edgecolor'] = 'none'  # HPC highlight='white'
# xtick.color
plt.rcParams['xtick.color']      = 'none'    # HPC bright='#FF9900'
# ytick.color
plt.rcParams['ytick.color']      = 'none'    # HPC bright='#FF9900'
# axes.prop_cycle
plt.rcParams['axes.prop_cycle']  = cycler(color=[
    "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
    "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"
])  # HPC can expand with 20+ colors
# lines.linewidth
plt.rcParams['lines.linewidth']       = 1.0  # HPC thick=8, AR=15
# lines.markersize
plt.rcParams['lines.markersize']      = 5    # VR=10, HPC=2
# lines.markeredgewidth
plt.rcParams['lines.markeredgewidth'] = 1  # HPC bullet=4

# axes.spines.top
plt.rcParams['axes.spines.top']       = False # minimal=False
# axes.spines.right
plt.rcParams['axes.spines.right']     = False # IFR bounding=True
# axes.spines.left
plt.rcParams['axes.spines.left']      = False # minimal=False
# axes.spines.bottom
plt.rcParams['axes.spines.bottom']    = False # standard=True
# margins/layout
plt.rcParams['axes.xmargin']         = 0.02  # HPC wide=0.1
plt.rcParams['axes.ymargin']         = 0.02  # HPC tight=0
# axes.zmargin (if 3D)
# figure.autolayout=True (avoid label cut)
# figure.constrained_layout.use = True # for multi-subplot HPC
# antialiasing
plt.rcParams['lines.antialiased']    = True
plt.rcParams['patch.antialiased']    = True
# text.antialiased can be toggled
# line cap/join styles
plt.rcParams['lines.solid_capstyle']   = 'butt'   # alt: 'round','projecting'
plt.rcParams['lines.solid_joinstyle']  = 'miter'  # alt: 'round','bevel'
plt.rcParams['lines.dash_capstyle']    = 'butt'
plt.rcParams['lines.dash_joinstyle']   = 'miter'
# tick params
plt.rcParams['xtick.major.size']  = 10   # HPC big=10
plt.rcParams['xtick.minor.size']  = 3
plt.rcParams['xtick.direction']   = 'in' # alt:'out','inout'
plt.rcParams['xtick.top']         = True
plt.rcParams['ytick.left']        = True
# unicode/symbol
plt.rcParams['axes.unicode_minus'] = True
# autolimit
plt.rcParams['axes.autolimit_mode'] = 'round_numbers'
# polar/3D
plt.rcParams['axes.axisbelow'] = True
# interactive/toolbars
plt.rcParams['toolbar'] = 'None'  # HPC might disable
# advanced figure scaling
# Increase figure size for better visibility
plt.rcParams['figure.figsize'] = (30, 22)  # Wider and taller plot for better area coverage
plt.rcParams['figure.dpi'] = 150  # Increase resolution for detail



###############################################################################
# 1. BEARCAT MASTER DATA (unchanged from your version)
###############################################################################
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

###############################################################################
# 2. ADDITIONAL ADVANCED DATA (unchanged, for reference)
###############################################################################
Advanced_Bearcat_Data: Dict[str, Any] = {
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
# 3. PHASES: Now we add Dogfight as well
#    Approach -> Strafe -> Bombing -> Escape -> Dogfight
###############################################################################
phases_info = {
    "Approach": ("blue",   60),
    "Strafe":   ("orange", 50),
    "Bombing":  ("red",    50),
    "Escape":   ("green",  60),
    "Dogfight": ("purple", 70)  # New phase
}

###############################################################################
# 4. GENERATE FLIGHT PATHS for each phase
###############################################################################
def generate_path(start: Tuple[float, float, float], end: Tuple[float, float, float], num_points: int, curve: Optional[str] = None) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Simple param generation + optional sinusoidal or wave shape."""
    x0,y0,z0 = start
    x1,y1,z1 = end
    t_vals = np.linspace(0,1,num_points)
    x_arr = x0 + (x1-x0)*t_vals
    y_arr = y0 + (y1-y0)*t_vals
    z_arr = z0 + (z1-z0)*t_vals
    if curve=="strafe_dive":
        # let z do a steeper mid drop
        z_arr = z0 - (z0-z1)*np.sin(t_vals*np.pi/2)
    elif curve=="escape_climb":
        z_arr += 500*np.sin(2*np.pi*t_vals)
    elif curve=="dogfight_maneuver":
        x_arr += 400*np.sin(4*np.pi*t_vals)
        y_arr += 300*np.cos(2*np.pi*t_vals)
        z_arr += 200*np.sin(3*np.pi*t_vals)
    return x_arr,y_arr,z_arr

# We'll define start/end for each phase
# Approach
A_start = (0,     8000, 3000)
A_end   = (6000,  7500, 2200)
numA = phases_info["Approach"][1]
xA,yA,zA = generate_path(A_start,A_end,numA)

# Strafe
B_start = A_end
B_end   = (10000,7000,200)
numB = phases_info["Strafe"][1]
xB,yB,zB = generate_path(B_start,B_end,numB,curve="strafe_dive")

# Bombing
C_start = B_end
C_end   = (15000,7500,1200)
numC = phases_info["Bombing"][1]
xC,yC,zC = generate_path(C_start,C_end,numC)

# Escape
D_start = C_end
D_end   = (7000,6000,4000)
numD = phases_info["Escape"][1]
xD,yD,zD = generate_path(D_start,D_end,numD,curve="escape_climb")

# Dogfight
E_start = D_end
E_end   = (5000,6500,3500)
numE = phases_info["Dogfight"][1]
xE,yE,zE = generate_path(E_start,E_end,numE,curve="dogfight_maneuver")

# Concatenate
flight_x = np.concatenate([xA,xB,xC,xD,xE])
flight_y = np.concatenate([yA,yB,yC,yD,yE])
flight_z = np.concatenate([zA,zB,zC,zD,zE])
frames_total = len(flight_x)

# Phase slices
idxA_end = numA
idxB_end = idxA_end + numB
idxC_end = idxB_end + numC
idxD_end = idxC_end + numD
idxE_end = idxD_end + numE
phase_slices = {
    "Approach": (0,       idxA_end),
    "Strafe":   (idxA_end, idxB_end),
    "Bombing":  (idxB_end, idxC_end),
    "Escape":   (idxC_end, idxD_end),
    "Dogfight": (idxD_end, idxE_end)
}

###############################################################################
# 5. GENERATE TERRAIN
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

fig = plt.figure(figsize=(20, 14)) # type: ignore
ax_main: Axes3D = fig.add_subplot(111, projection='3d') # type: ignore

# Define xmin and xmax
xmin, xmax = 0, 18500
ymin, ymax = 4000, 9300
step, amplitude = (100, 800)

# # Generate terrain data
# x_terr, y_terr, z_terr = generate_terrain(xmin, xmax, ymin, ymax, step, amplitude)

# Make region bigger
ax_main.set_xlim(xmin, xmax)  # type: ignore
ax_main.set_ylim(ymin, ymax)  # type: ignore
ax_main.set_zlim(0, 15000)    # type: ignore

# Because stubs don’t define .pane on XAxis, YAxis, etc., we ignore:
ax_main.xaxis.pane.set_facecolor((0,0,0,0))  # type: ignore
ax_main.yaxis.pane.set_facecolor((0,0,0,0))  # type: ignore
ax_main.zaxis.pane.set_facecolor((0,0,0,0))  # type: ignore
ax_main.xaxis.pane.set_edgecolor((0,0,0,0))  # type: ignore
ax_main.yaxis.pane.set_edgecolor((0,0,0,0))  # type: ignore
ax_main.zaxis.pane.set_edgecolor((0,0,0,0))  # type: ignore

# Plot terrain surface
x_terr, y_terr, z_terr = generate_terrain()
ax_main.plot_surface(x_terr, y_terr, z_terr, cmap='terrain', alpha=0.2, edgecolor='none')  # type: ignore
ax_main.set_title("F8F-1 Bearcat 3D (Approach->Strafe->Bomb->Escape->Dogfight)")  # type: ignore
ax_main.set_xlabel("X (m)")  # type: ignore
ax_main.set_ylabel("Y (m)")  # type: ignore
ax_main.set_zlabel("Altitude (m)")  # type: ignore
ax_main.set_xlim(0, 16000)  # type: ignore
ax_main.set_ylim(5000, 9000)  # type: ignore
ax_main.set_zlim(0, 5000)  # type: ignore
ax_main.view_init(elev=30, azim=-60)  # type: ignore

plt.tight_layout()

###############################################################################
# 6. FLASHING ARROWS (No Solid Lines)
###############################################################################
phase_positions = {
    "Approach": (xA,yA,zA),
    "Strafe":   (xB,yB,zB),
    "Bombing":  (xC,yC,zC),
    "Escape":   (xD,yD,zD),
    "Dogfight": (xE,yE,zE)
}

phase_quivers: Dict[str, List[Any]] = {pname:[] for pname in phase_positions}
arrow_len=400

def create_phase_quivers(ax: Axes3D, xarr: NDArray[np.float64], yarr: NDArray[np.float64], zarr: NDArray[np.float64], color: str) -> List[Any]:
    quivers: List[Any] = []
    interval = 3
    for i in range(0, len(xarr) - 1, interval):
        dx = xarr[i + 1] - xarr[i]
        dy = yarr[i + 1] - yarr[i]
        dz = zarr[i + 1] - zarr[i]
        q = ax.quiver(xarr[i], yarr[i], zarr[i], dx, dy, dz, # type: ignore
                      length=arrow_len, normalize=True,
                      color=color, arrow_length_ratio=0.3,
                      visible=False)
        quivers.append(q)
    return quivers

for pname,(col,num_pts) in phases_info.items():
    xP,yP,zP = phase_positions[pname]
    phase_quivers[pname] = create_phase_quivers(ax_main, xP,yP,zP, col)

###############################################################################
# 7. BLINKING BOMB
###############################################################################
def simulate_bomb_trajectory(x_init: float, y_init: float, z_init: float,
                             vx_init: float = 0, vy_init: float = 0, vz_init: float = -50,
                             dt: float = 0.04, drag: float = 0.0003, max_time: float = 40.0) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    # War Thunder style: slightly weaker gravity
    g=9.81*0.75
    bx=[x_init]
    by=[y_init]
    bz=[z_init]
    vx,vy,vz = vx_init,vy_init,vz_init
    t=0
    while t<max_time:
        xnew=bx[-1]+vx*dt
        ynew=by[-1]+vy*dt
        znew=bz[-1]+vz*dt
        spd_xy=math.hypot(vx,vy)
        if spd_xy>1e-3:
            drag_f=drag*spd_xy**2
            vx-=drag_f*(vx/spd_xy)*dt
            vy-=drag_f*(vy/spd_xy)*dt
        vz-=g*dt
        if znew<=0:
            znew=0
            bx.append(xnew)
            by.append(ynew)
            bz.append(znew)
            break
        bx.append(xnew)
        by.append(ynew)
        bz.append(znew)
        t+=dt
    return np.array(bx),np.array(by),np.array(bz)

# Let’s drop the bomb mid-bombing
bomb_drop_frame = idxB_end+(numC//2)
if bomb_drop_frame>=frames_total:
    bomb_drop_frame=frames_total-1
bomb_init_x = flight_x[bomb_drop_frame]
bomb_init_y = flight_y[bomb_drop_frame]
bomb_init_z = flight_z[bomb_drop_frame]

if bomb_drop_frame>0:
    pxp=flight_x[bomb_drop_frame-1]
    pyp=flight_y[bomb_drop_frame-1]
    pzp=flight_z[bomb_drop_frame-1]
    vx_plane = (bomb_init_x-pxp)*25
    vy_plane = (bomb_init_y-pyp)*25
    vz_plane = (bomb_init_z-pzp)*25
else:
    vx_plane=vy_plane=vz_plane=0

bomb_x,bomb_y,bomb_z = simulate_bomb_trajectory(
    bomb_init_x,bomb_init_y,bomb_init_z,
    vx_init=vx_plane,vy_init=vy_plane,vz_init=vz_plane,
    dt=0.03,drag=0.00025,max_time=50
)

bomb_marker = None
bomb_explosion_triggered=False
bomb_hit_frame=None

###############################################################################
# 8. IMPROVED AAA w/ turret
###############################################################################
def create_aaa_geometry(cx: float, cy: float, cz: float, size_base: float = 80, height_base: float = 30, size_turret: float = 40) -> List[List[Tuple[float, float, float]]]:
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
    turret_height=20
    turret_base_z=base_top
    turret_top_z=base_top+turret_height
    half_t=size_turret/2
    turret_verts = [
        (cx-half_t,cy-half_t,turret_base_z),
        (cx+half_t,cy-half_t,turret_base_z),
        (cx+half_t,cy+half_t,turret_base_z),
        (cx-half_t,cy+half_t,turret_base_z),
    ]
    turret_verts_top=[
        (cx-half_t,cy-half_t,turret_top_z),
        (cx+half_t,cy-half_t,turret_top_z),
        (cx+half_t,cy+half_t,turret_top_z),
        (cx-half_t,cy+half_t,turret_top_z),
    ]
    turret_faces=[
        [turret_verts[0],turret_verts[1],turret_verts[2],turret_verts[3]],
        [turret_verts_top[0],turret_verts_top[1],turret_verts_top[2],turret_verts_top[3]],
        [turret_verts[0],turret_verts[1],turret_verts_top[1],turret_verts_top[0]],
        [turret_verts[1],turret_verts[2],turret_verts_top[2],turret_verts_top[1]],
        [turret_verts[2],turret_verts[3],turret_verts_top[3],turret_verts_top[2]],
        [turret_verts[3],turret_verts[0],turret_verts_top[0],turret_verts_top[3]],
    ]
    return base_faces+turret_faces

def ground_aaa_path(t: float, center_x: float, center_y: float, radius: float = 500) -> Tuple[float, float, float]:
    angle=2*math.pi*t
    gx=center_x+radius*math.cos(angle)
    gy=center_y+radius*math.sin(angle)
    gz=0
    return gx,gy,gz

###############################################################################
# 9. LOCK-ON RETICLE + "Target Destroyed"
###############################################################################
lockon_line=None
lockon_line_radius=300
lockon_line_shrink=3.0
target_destroyed_text=None
strafe_explosion_active=False
strafe_explosion_count=0
strafe_explosion_max=30
strafe_explosion_poly=None

def spawn_strafe_explosion():
    global strafe_explosion_active,strafe_explosion_count
    strafe_explosion_active=True
    strafe_explosion_count=0

###############################################################################
# 10. DOGFIGHT BOGIE PATH -> if "hit" => spiral down + parachute
###############################################################################
bogie_x = np.full(frames_total,np.nan)
bogie_y = np.full(frames_total,np.nan)
bogie_z = np.full(frames_total,np.nan)

bogie_appear = idxD_end-20
bx_start = 20000
by_start = 7500
bz_start = 500
for f in range(frames_total):
    if f<bogie_appear:
        continue
    else:
        if f==bogie_appear:
            bogie_x[f]=bx_start
            bogie_y[f]=by_start
            bogie_z[f]=bz_start
        else:
            px_ = flight_x[f]
            py_ = flight_y[f]
            pz_ = flight_z[f]
            dx_ = px_ - bogie_x[f-1]
            dy_ = py_ - bogie_y[f-1]
            dz_ = pz_ - bogie_z[f-1]
            bogie_x[f] = bogie_x[f-1] + 0.2*dx_
            bogie_y[f] = bogie_y[f-1] + 0.2*dy_
            bogie_z[f] = bogie_z[f-1] + 0.2*dz_

bogie_is_hit=False
bogie_hit_frame=None

###############################################################################
# 11. EXPLOSION + PARACHUTE
###############################################################################
explosion_active=False
explosion_frame=0
explosion_max_frames=30
explosion_poly=None
explosion_center=(0,0,0)

def spawn_explosion(center: Tuple[float, float, float]):
    global explosion_active, explosion_frame, explosion_center
    explosion_active=True
    explosion_frame=0
    explosion_center=center

parachute_poly=None
parachute_active=False
parachute_frame=0
parachute_center=(0,0,0)

def spawn_parachute(center: Tuple[float, float, float]):
    global parachute_active, parachute_frame, parachute_center
    parachute_active=True
    parachute_frame=0
    parachute_center=center

###############################################################################
# 12. AIRCRAFT WEDGES (Bearcat & Bogie)
###############################################################################
def create_plane_wedge(position: Tuple[float, float, float], direction: Tuple[float, float, float], scale: int = 200, color: str = 'cyan') -> Poly3DCollection:
    _, _, _ = position
    dx,dy,dz = direction
    mag=math.sqrt(dx*dx+dy*dy+dz*dz)
    if mag<1e-6:
        dx,dy,dz=1,0,0
        mag=1
    dx /= mag
    dy /= mag
    dz /= mag

    tip  = np.array([0,0,0])
    left = np.array([-0.8,-0.2,0])
    right= np.array([-0.8,0.2,0])
    top  = np.array([-0.7,0,0.1])
    tip *= scale
    left *= scale
    right *= scale
    top *= scale

    forward=np.array([dx,dy,dz])
    up_guess=np.array([0,0,1])
    side=np.cross(forward,up_guess)
    side_mag=np.linalg.norm(side)
    if side_mag<1e-6:
        side=np.cross(forward,[1,0,0])
        side_mag=np.linalg.norm(side)
    side/=side_mag
    up=np.cross(side,forward)
    R=np.vstack([forward,side,up]).T

    def transform(local_pt):
        return position+R.dot(local_pt)

    tip_w=transform(tip)
    left_w=transform(left)
    right_w=transform(right)
    top_w=transform(top)
    faces=[
        [tip_w,left_w,right_w],
        [left_w,top_w,right_w],
        [tip_w,top_w,left_w],
        [tip_w,right_w,top_w],
    ]
    poly: Poly3DCollection = Poly3DCollection(faces,facecolor=color,alpha=1.0)
    poly.set_edgecolor((0, 0, 0, 1)) #type: ignore # RGBA tuple for black color
    return poly

bearcat_poly=None
bogie_poly=None

###############################################################################
# 13. BULLETS & ROCKETS
###############################################################################
active_bullets=[]
active_rockets=[]

def simulate_bullet_trajectory(plane_pos,plane_vel,muzzle_speed=890,
                               dt=0.02,max_time=2.0,gravity=9.81):
    px,py,pz=plane_pos
    vxp,vyp,vzp=plane_vel
    speed_plane=math.sqrt(vxp*vxp+vyp*vyp+vzp*vzp)
    if speed_plane<1e-6:
        direction=(1,0,0)
    else:
        direction=(vxp/speed_plane,vyp/speed_plane,vzp/speed_plane)
    bullet_speed = speed_plane + muzzle_speed
    vx_=bullet_speed*direction[0]
    vy_=bullet_speed*direction[1]
    vz_=bullet_speed*direction[2]
    bx=[px]; by=[py]; bz=[pz]
    t=0
    while t<max_time:
        xnew=bx[-1]+vx_*dt
        ynew=by[-1]+vy_*dt
        znew=bz[-1]+vz_*dt
        vz_-=gravity*dt
        if znew<=0:
            znew=0
            bx.append(xnew); by.append(ynew); bz.append(znew)
            break
        bx.append(xnew); by.append(ynew); bz.append(znew)
        t+=dt
    return np.array(bx),np.array(by),np.array(bz)

def spawn_bullets(px,py,pz,vx,vy,vz,muzzle_speed=890,num_bullets=1):
    for _ in range(num_bullets):
        bx,by,bz=simulate_bullet_trajectory((px,py,pz),(vx,vy,vz),
                                            muzzle_speed=muzzle_speed)
        bullet={'x':bx,'y':by,'z':bz,'index':0,'line':None}
        active_bullets.append(bullet)

def simulate_rocket_trajectory(plane_pos,plane_vel,rocket_speed=320.0,
                               dt=0.05,max_time=10.0,thrust_dur=3.0):
    px,py,pz=plane_pos
    vxp,vyp,vzp=plane_vel
    speed_plane=math.sqrt(vxp*vxp+vyp*vyp+vzp*vzp)
    if speed_plane<1e-6:
        direction=(1,0,0)
    else:
        direction=(vxp/speed_plane,vyp/speed_plane,vzp/speed_plane)
    vx_r=speed_plane+rocket_speed
    vx_vec=[vx_r*direction[0], vx_r*direction[1], vx_r*direction[2]]
    g=9.81
    rx=[px]; ry=[py]; rz=[pz]
    t=0
    while t<max_time:
        if t<thrust_dur:
            vx_vec[0]+=5*dt*direction[0]
            vx_vec[1]+=5*dt*direction[1]
            vx_vec[2]+=5*dt*direction[2]
        vx_,vy_,vz_=vx_vec
        vx_vec[2]-=g*dt
        xnew=rx[-1]+vx_*dt
        ynew=ry[-1]+vy_*dt
        znew=rz[-1]+vz_*dt
        if znew<=0:
            znew=0
            rx.append(xnew); ry.append(ynew); rz.append(znew)
            break
        rx.append(xnew); ry.append(ynew); rz.append(znew)
        t+=dt
    return np.array(rx),np.array(ry),np.array(rz)

def spawn_rocket(px,py,pz,vx,vy,vz):
    rx,ry,rz=simulate_rocket_trajectory((px,py,pz),(vx,vy,vz))
    rocket={'x':rx,'y':ry,'z':rz,'index':0,'line':None}
    active_rockets.append(rocket)

###############################################################################
# 14. ANIMATION UTILS
###############################################################################
def update_explosion():
    global explosion_active, explosion_frame, explosion_poly
    if not explosion_active:
        return
    if explosion_poly is not None:
        explosion_poly.remove()
    frac=explosion_frame/float(explosion_max_frames)
    radius=10+100*frac
    th,ph=np.mgrid[0:np.pi:15j, 0:2*np.pi:15j]
    xs=radius*np.sin(th)*np.cos(ph)+explosion_center[0]
    ys=radius*np.sin(th)*np.sin(ph)+explosion_center[1]
    zs=radius*np.cos(th)+explosion_center[2]
    explosion_poly=ax_main.plot_surface(xs,ys,zs,color='orange',alpha=0.4,edgecolor='none')
    explosion_frame+=1
    if explosion_frame>=explosion_max_frames:
        explosion_active=False
        if explosion_poly is not None:
            explosion_poly.remove()
            explosion_poly=None

def update_strafe_explosion():
    global strafe_explosion_active, strafe_explosion_poly, strafe_explosion_count
    if not strafe_explosion_active:
        return
    if strafe_explosion_poly is not None:
        strafe_explosion_poly.remove()
    frac=strafe_explosion_count/float(strafe_explosion_max)
    radius=5+60*frac
    t_,p_ = np.mgrid[0:np.pi:10j,0:2*np.pi:10j]
    # We'll use the strafe target center (the end of B_end)
    st_center = (10000,7000,0)
    xs=radius*np.sin(t_)*np.cos(p_)+st_center[0]
    ys=radius*np.sin(t_)*np.sin(p_)+st_center[1]
    zs=radius*np.cos(t_)+st_center[2]
    strafe_explosion_poly=ax_main.plot_surface(xs,ys,zs,color='red',alpha=0.4,edgecolor='none')
    strafe_explosion_count+=1
    if strafe_explosion_count>=strafe_explosion_max:
        strafe_explosion_active=False
        if strafe_explosion_poly is not None:
            strafe_explosion_poly.remove()
            strafe_explosion_poly=None

def update_parachute():
    global parachute_active, parachute_frame, parachute_poly
    if not parachute_active:
        return
    if parachute_poly is not None:
        parachute_poly.remove()
    t=parachute_frame
    dx=parachute_center[0]+10*np.sin(0.1*t)
    dy=parachute_center[1]+10*np.cos(0.1*t)
    dz=parachute_center[2]-3*t
    if dz<0: dz=0
    size=50
    half=size/2
    corners=[
        (dx-half,dy-half,dz+20),
        (dx+half,dy-half,dz+20),
        (dx+half,dy+half,dz+20),
        (dx-half,dy+half,dz+20),
    ]
    faces=[[corners[0],corners[1],corners[2],corners[3]]]
    p=Poly3DCollection(faces,facecolors='white',alpha=0.8)
    p.set_edgecolor('black')
    ax_main.add_collection3d(p)

    parachute_poly=p
    parachute_frame+=1
    if dz<=0:
        parachute_active=False
        if parachute_poly is not None:
            parachute_poly.remove()
            parachute_poly=None

###############################################################################
# 15. INIT ANIMATION
###############################################################################
def init_animation():
    # hide quivers initially
    for pname in phase_quivers:
        for q in phase_quivers[pname]:
            q.set_visible(False)
    return ()

###############################################################################
# 16. UPDATE ANIMATION
###############################################################################
def update_animation(frame):
    global bomb_marker, bomb_hit_frame, bomb_explosion_triggered
    global bearcat_poly, bogie_poly
    global bogie_is_hit, bogie_hit_frame
    global lockon_line, lockon_line_radius
    global target_destroyed_text
    global strafe_explosion_active, strafe_explosion_count
    global parachute_poly

    # 1) FLASHING ARROWS
    for pname,(col,num_pts) in phases_info.items():
        start_idx,end_idx = phase_slices[pname]
        quivers=phase_quivers[pname]
        if start_idx<=frame<end_idx:
            blink_speed=5
            blink_on=((frame//blink_speed)%2==0)
            for qv in quivers:
                qv.set_visible(blink_on)
        else:
            for qv in quivers:
                qv.set_visible(False)

    # 2) BEARCAT & BOMB MARKER
    # Bearcat wedge
    global bearcat_poly
    if bearcat_poly is not None:
        bearcat_poly.remove()
        bearcat_poly=None
    if frame<frames_total:
        bcx=flight_x[frame]
        bcy=flight_y[frame]
        bcz=flight_z[frame]
        if frame>0:
            vx_bc=flight_x[frame]-flight_x[frame-1]
            vy_bc=flight_y[frame]-flight_y[frame-1]
            vz_bc=flight_z[frame]-flight_z[frame-1]
        else:
            vx_bc=vy_bc=vz_bc=0
        bearcat_poly=create_plane_wedge((bcx,bcy,bcz),(vx_bc,vy_bc,vz_bc),
                                        scale=200,color='cyan')
        ax_main.add_collection3d(bearcat_poly)

    # Bomb marker (blink faster near impact)
    if bomb_marker is not None:
        bomb_marker.remove()
        bomb_marker=None
    bomb_frame_i=frame-bomb_drop_frame
    if bomb_frame_i>=0:
        if bomb_frame_i<len(bomb_x):
            bx_=bomb_x[bomb_frame_i]
            by_=bomb_y[bomb_frame_i]
            bz_=bomb_z[bomb_frame_i]
            alt=bz_
            blink_rate=20.0 - 0.02*alt
            if blink_rate<2: blink_rate=2
            bomb_blink_on=((frame//int(blink_rate))%2==0)
            if alt>0 and bomb_blink_on:
                bomb_marker=ax_main.scatter([bx_],[by_],[bz_],color='red',s=80,marker='o')
            if alt<=0 and not bomb_explosion_triggered:
                bomb_explosion_triggered=True
                spawn_explosion((bx_,by_,0))

    # 3) BOGIE + DOGFIGHT
    global bogie_poly
    if bogie_poly is not None:
        bogie_poly.remove()
        bogie_poly=None
    if frame<frames_total and not np.isnan(bogie_x[frame]):
        if bogie_is_hit:
            n=frame-bogie_hit_frame
            if n<0:n=0
            oldx=bogie_x[bogie_hit_frame]
            oldy=bogie_y[bogie_hit_frame]
            oldz=bogie_z[bogie_hit_frame]
            angle=0.4*n
            rad=50+5*n
            bx=oldx+rad*math.cos(angle)
            by=oldy+rad*math.sin(angle)
            bz=oldz-30*n
            if bz<0:bz=0
            bogie_x[frame]=bx
            bogie_y[frame]=by
            bogie_z[frame]=bz
            if bz<=0:
                if not explosion_active:
                    spawn_explosion((bx,by,0))
                    spawn_parachute((bx,by,0))

        btx=bogie_x[frame]
        bty=bogie_y[frame]
        btz=bogie_z[frame]
        if frame>0 and not np.isnan(bogie_x[frame-1]):
            vx_bog=bogie_x[frame]-bogie_x[frame-1]
            vy_bog=bogie_y[frame]-bogie_y[frame-1]
            vz_bog=bogie_z[frame]-bogie_z[frame-1]
        else:
            vx_bog=vy_bog=vz_bog=0
        bogie_poly=create_plane_wedge((btx,bty,btz),(vx_bog,vy_bog,vz_bog),
                                      scale=200,color='red')
        ax_main.add_collection3d(bogie_poly)

    # 4) STRAFE PHASE => Lock-on reticle
    strafe_s, strafe_e=phase_slices["Strafe"]
    global lockon_line
    if lockon_line is not None:
        lockon_line.remove()
        lockon_line=None
    if strafe_s<=frame<strafe_e:
        if lockon_line_radius>0:
            angles=np.linspace(0,2*np.pi,36)
            center_ = (10000,7000,0)
            xs=center_[0]+lockon_line_radius*np.cos(angles)
            ys=center_[1]+lockon_line_radius*np.sin(angles)
            zs=np.full_like(xs,center_[2]+10)
            lockon_line,=ax_main.plot(xs,ys,zs,color='yellow',linewidth=2)
            lockon_line_radius-=lockon_line_shrink
            if lockon_line_radius<0:
                lockon_line_radius=0
    else:
        lockon_line_radius=300

    # If we just ended strafe => "Target Destroyed"
    global target_destroyed_text
    if frame==strafe_e:
        if target_destroyed_text is None:
            target_destroyed_text=ax_main.text(10000,7000,100,
                                               "Target Destroyed",
                                               color='red',fontsize=14)
            spawn_strafe_explosion()

    # 5) Bullets & Rockets
    # Let's spawn bullets in strafe
    if strafe_s<=frame<strafe_e:
        if frame%8==0 and frame>0:
            px=flight_x[frame]
            py=flight_y[frame]
            pz=flight_z[frame]
            vx_=flight_x[frame]-flight_x[frame-1]
            vy_=flight_y[frame]-flight_y[frame-1]
            vz_=flight_z[frame]-flight_z[frame-1]
            spawn_bullets(px,py,pz,vx_,vy_,vz_,num_bullets=2)

    # Bombing -> already set up your rocket spawns
    bomb_s, bomb_e=phase_slices["Bombing"]
    mid_bomb = bomb_s+(bomb_e-bomb_s)//2
    if frame==mid_bomb or frame==(mid_bomb+5):
        if frame>0:
            vx_=flight_x[frame]-flight_x[frame-1]
            vy_=flight_y[frame]-flight_y[frame-1]
            vz_=flight_z[frame]-flight_z[frame-1]
        else:
            vx_=vy_=vz_=0
        px=flight_x[frame]
        py=flight_y[frame]
        pz=flight_z[frame]
        spawn_rocket(px,py,pz,vx_,vy_,vz_)

    # Dogfight => both planes shoot
    dog_s, dog_e=phase_slices["Dogfight"]
    if dog_s<=frame<dog_e:
        # Bearcat
        if frame%5==0 and frame>0:
            px=flight_x[frame]
            py=flight_y[frame]
            pz=flight_z[frame]
            vx_=flight_x[frame]-flight_x[frame-1]
            vy_=flight_y[frame]-flight_y[frame-1]
            vz_=flight_z[frame]-flight_z[frame-1]
            spawn_bullets(px,py,pz,vx_,vy_,vz_,num_bullets=3)
        # Bogie (if not hit)
        if frame%7==0 and frame>0 and not bogie_is_hit:
            bx_=bogie_x[frame]
            by_=bogie_y[frame]
            bz_=bogie_z[frame]
            if not np.isnan(bx_):
                vx_=bogie_x[frame]-bogie_x[frame-1]
                vy_=bogie_y[frame]-bogie_y[frame-1]
                vz_=bogie_z[frame]-bogie_z[frame-1]
                spawn_bullets(bx_,by_,bz_,vx_,vy_,vz_,muzzle_speed=800,num_bullets=2)
        # halfway => get a "hit"
        half_dog = dog_s+(dog_e-dog_s)//2
        if frame==half_dog and not bogie_is_hit:
            bogie_is_hit=True
            bogie_hit_frame=frame

    # 6) Update bullets
    done_bullets=[]
    for bullet in active_bullets:
        if bullet['index']<len(bullet['x'])-1:
            bullet['index']+=1
            idx=bullet['index']
            if bullet['line'] is None:
                line_,=ax_main.plot([],[],[],color='yellow',linewidth=2)
                bullet['line']=line_
            bx_=bullet['x'][:idx]
            by_=bullet['y'][:idx]
            bz_=bullet['z'][:idx]
            bullet['line'].set_data_3d(bx_,by_,bz_)
        else:
            if bullet['line'] is not None:
                bullet['line'].remove()
                bullet['line']=None
            done_bullets.append(bullet)
    for b in done_bullets:
        active_bullets.remove(b)

    # 7) Update rockets
    done_rockets=[]
    for rocket in active_rockets:
        if rocket['index']<len(rocket['x'])-1:
            rocket['index']+=1
            idx=rocket['index']
            if rocket['line'] is None:
                rline,=ax_main.plot([],[],[],color='magenta',linewidth=2)
                rocket['line']=rline
            rx_=rocket['x'][:idx]
            ry_=rocket['y'][:idx]
            rz_=rocket['z'][:idx]
            rocket['line'].set_data_3d(rx_,ry_,rz_)
        else:
            if rocket['line'] is not None:
                rocket['line'].remove()
                rocket['line']=None
            done_rockets.append(rocket)
    for r_ in done_rockets:
        active_rockets.remove(r_)

    # 8) Explosion from bomb
    if frame==(idxC_end+5) and not bomb_explosion_triggered and len(bomb_x)>0:
        bomb_explosion_triggered=True
        bomb_impact_pt=(bomb_x[-1],bomb_y[-1],0)
        spawn_explosion(bomb_impact_pt)
    update_explosion()

    # 9) AAA animations (two AAA sites: near strafe, near bomb)
    #   We remove old AAA & re-add
    for c_ in ax_main.collections[:]:
        if getattr(c_,'_aaa_flag',False):
            c_.remove()
    # AAA #1 (strafe area)
    cyc=(frame%200)/200.0
    gx1,gy1,gz1=ground_aaa_path(cyc,10000,7000,500)
    faces1=create_aaa_geometry(gx1,gy1,gz1,size_base=100,height_base=40,size_turret=60)
    col1=Poly3DCollection(faces1,facecolor='brown',alpha=0.9)
    col1.set_edgecolor('white')
    col1._aaa_flag=True
    ax_main.add_collection3d(col1)

    # AAA #2 (bomb area)
    gx2,gy2,gz2=ground_aaa_path(cyc+0.3,15000,7500,700)
    faces2=create_aaa_geometry(gx2,gy2,gz2,size_base=120,height_base=50,size_turret=70)
    col2=Poly3DCollection(faces2,facecolor='black',alpha=0.9)
    col2.set_edgecolor('white')
    col2._aaa_flag=True
    ax_main.add_collection3d(col2)

    # 10) Strafe explosion
    update_strafe_explosion()

    # 11) Parachute
    update_parachute()

    return ()

###############################################################################
# 17. RUN THE ANIMATION
###############################################################################
anim = FuncAnimation(fig, update_animation,
                     init_func=init_animation,
                     frames=frames_total,
                     interval=80,
                     blit=False)
plt.show()
