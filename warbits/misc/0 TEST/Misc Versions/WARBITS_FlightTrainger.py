
###############################################################################
# Import/From
###############################################################################
import math
from typing import Any, Dict, Tuple  # type: ignore

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler  # For advanced color cycling
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D  # type: ignore
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # type: ignore

# We keep your original background & face colors, but add more "pizzazz."
mpl.rcParams['figure.facecolor'] = 'white'          # Window background
mpl.rcParams['axes.facecolor']   = '#F0F0F0'        # Axes area background
mpl.rcParams['axes.edgecolor']   = 'black'
mpl.rcParams['axes.linewidth']   = 1.2
mpl.rcParams['grid.color']       = 'gray'
mpl.rcParams['grid.alpha']       = 0.5
mpl.rcParams['grid.linestyle']   = ':'
mpl.rcParams['axes.grid']        = True             # Default to show grids
mpl.rcParams['figure.dpi']       = 120              # Crispness
mpl.rcParams['savefig.dpi']      = 200              # If saving figures
mpl.rcParams['font.size']        = 14               # Larger baseline font
mpl.rcParams['axes.labelsize']   = 13
mpl.rcParams['axes.titlesize']   = 16
mpl.rcParams['axes.titleweight'] = 'bold'
mpl.rcParams['axes.titlecolor']  = '#202020'
mpl.rcParams['legend.fontsize']  = 12
mpl.rcParams['legend.frameon']   = True
mpl.rcParams['legend.fancybox']  = True
mpl.rcParams['legend.framealpha']= 0.85
mpl.rcParams['legend.edgecolor'] = '#333333'
mpl.rcParams['xtick.color']      = 'black'
mpl.rcParams['ytick.color']      = 'black'
mpl.rcParams['axes.prop_cycle']  = cycler(color=[
    "#1f77b4", "#ff7f0e", "#2ca02c",
    "#d62728", "#9467bd", "#8c564b",
    "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
])

# Optionally, let’s make lines a bit thicker & markers bigger:
mpl.rcParams['lines.linewidth']       = 2.0
mpl.rcParams['lines.markersize']      = 7
mpl.rcParams['lines.markeredgewidth'] = 1.3

# If you want spines on all sides:
mpl.rcParams['axes.spines.top']    = True
mpl.rcParams['axes.spines.right']  = True
mpl.rcParams['axes.spines.left']   = True
mpl.rcParams['axes.spines.bottom'] = True


###############################################################################
# 1. BEARCAT MASTER DATA (Ultra-Detailed, Extended)
###############################################################################
F8F1_Bearcat_Data: Dict[str, Any] = {
    "Name": "F8F-1 Bearcat",
    "Nation": "USA",
    "Type": "Naval Fighter (Carrier-Based)",
    "BR_Realistic": 4.7,
    "Crew": 1,

    "Dimensions": {
        "Length_m": 8.61,         # ~28.25 ft
        "Wingspan_m": 10.92,      # ~35.85 ft
        "Height_m": 3.83,         # ~12.57 ft
        "Wing_Area_m2": 20.5,     # ~221 sq ft (approx)
        "Empty_Weight_kg": 3175,  # ~7000 lb
        "Loaded_Weight_kg": 4220, # ~9300 lb typical
    },

    "Engine": {
        "Designation": "Pratt & Whitney R-2800-34W",
        "Type": "Two-row, 18-cylinder radial, air-cooled",
        "Horsepower_HP": 2250,      # Varies by WEP
        "Takeoff_Power_HP": 2800,   # With WEP + Water Injection
        "Supercharger_Stages": "Two-speed mechanical",
        "Optimal_Manifold_Pressure_psi": 54,  # Approx under WEP
        "Propeller": "Hamilton Standard Hydromatic, 3.96 m diameter",
    },

    "Performance": {
        # Existing War Thunder–style stats:
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

        # Additional real-world style expansions:
        "Takeoff_Distance_ft": 630,  # at ~loaded weight + WEP
        "Landing_Distance_ft": 750,  # with typical approach flaps
        "Rate_of_Climb_fpm_SeaLevel": 4700,
        "Time_to_20000ft_min": 7.0,  # ~7 min to 20k ft
        "Combat_Flaps_Deployment_Speed_mph": 200,  # recommended <200 mph
        "Wing_Loading_kg_m2": 205,   # typical loaded ~ (some sources vary)
        "Power_to_Weight_Ratio_hp_lb": 0.59  # ~2800 HP / ~ 4700-4800 lb (some partial references)
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
        "One of the fastest piston-engine aircraft developed near WWII’s end",
        "Entered service late 1945 but missed active WWII combat",
        "Used post-war; heavily praised for climb rate & agility",
        "Some saw action with French forces in Indochina War",
        "Renowned for short takeoff / landing on carriers",
        "Sometimes outperforms contemporary piston fighters in vertical maneuvers"
    ]
}

###############################################################################
# 2. ADDITIONAL ADVANCED DATA
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
# 3. PHASES
###############################################################################
phases_info = {
    "Approach": ("blue",   60),
    "Strafe":   ("orange", 50),
    "Bombing":  ("red",    50),
    "Escape":   ("green",  60),
    "Dogfight": ("purple", 70)
}

###############################################################################
# 4. GENERATE FLIGHT PATHS
###############################################################################
def generate_path(
    start: Tuple[float, float, float],
    end: Tuple[float, float, float],
    num_points: int,
    curve: str = ""
) -> Tuple[np.ndarray[np.float64, np.dtype[np.float64]], np.ndarray[np.float64, np.dtype[np.float64]], np.ndarray[np.float64, np.dtype[np.float64]]]:
    x0, y0, z0 = start
    x1, y1, z1 = end
    t_vals: np.ndarray[np.float64, np.dtype[np.float64]] = np.linspace(0, 1, num_points)
    x_arr: np.ndarray[np.float64, np.dtype[np.float64]] = x0 + (x1 - x0) * t_vals
    y_arr: np.ndarray[np.float64, np.dtype[np.float64]] = y0 + (y1 - y0) * t_vals
    z_arr: np.ndarray[np.float64, np.dtype[np.float64]] = z0 + (z1 - z0) * t_vals
    if curve == "strafe_dive":
        z_arr = z0 - (z0 - z1) * np.sin(t_vals * np.pi / 2)
    elif curve == "escape_climb":
        z_arr += 500 * np.sin(2 * np.pi * t_vals)
    elif curve == "dogfight_maneuver":
        x_arr += 400 * np.sin(4 * np.pi * t_vals)
        y_arr += 300 * np.cos(2 * np.pi * t_vals)
        z_arr += 200 * np.sin(3 * np.pi * t_vals)
    return x_arr, y_arr, z_arr

# Phase starts
A_start = (0, 6000, 3000)
A_end   = (6000, 7500, 2200)
numA = phases_info["Approach"][1]
xA,yA,zA = generate_path(A_start,A_end,numA)

B_start = A_end
B_end   = (10000,7000,400)
numB = phases_info["Strafe"][1]
xB,yB,zB = generate_path(B_start,B_end,numB,curve="strafe_dive")

C_start = B_end
C_end   = (15000,7500,1000)
numC = phases_info["Bombing"][1]
xC,yC,zC = generate_path(C_start,C_end,numC)

D_start = C_end
D_end   = (7000,6000,4000)
numD = phases_info["Escape"][1]
xD,yD,zD = generate_path(D_start,D_end,numD,curve="escape_climb")

E_start = D_end
E_end   = (5000,6500,3500)
numE = phases_info["Dogfight"][1]
xE,yE,zE = generate_path(E_start,E_end,numE,curve="dogfight_maneuver")

flight_x = np.concatenate([xA,xB,xC,xD,xE])
flight_y = np.concatenate([yA,yB,yC,yD,yE])
flight_z = np.concatenate([zA,zB,zC,zD,zE])
frames_total = len(flight_x)

# Slices
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
# 5. MASSIVE TERRAIN
###############################################################################
def generate_terrain(
    xmin: int = 0,
    xmax: int = 18500,
    ymin: int = 4000,
    ymax: int = 9300,
    step: int = 100,
    amplitude: int = 800
) -> Tuple[np.ndarray[np.float64, np.dtype[np.float64]], np.ndarray[np.float64, np.dtype[np.float64]], np.ndarray[np.float64, np.dtype[np.float64]]]:
    x_vals = np.linspace(xmin, xmax, step)
    y_vals = np.linspace(ymin, ymax, step)
    x, y = np.meshgrid(x_vals, y_vals)
    np.random.seed(42)
    z = amplitude * 0.4 * np.sin(x / 1500) * np.cos(y / 1500)
    z += amplitude * 0.4 * np.random.rand(step, step)
    return x, y, z

fig = plt.figure(figsize=(16, 10))
ax_main: Axes3D = fig.add_subplot(2, 2, (1, 3), projection='3d')
ax_bullet_drop = fig.add_subplot(2, 2, 2)
ax_climb_rate = fig.add_subplot(2, 2, 4)

x_terr, y_terr, z_terr = generate_terrain()
ax_main.plot_surface(x_terr, y_terr, z_terr, cmap='terrain', alpha=0.2, edgecolor='none')
ax_main.set_title("F8F-1 Bearcat 3D (Approach->Strafe->Bomb->Escape->Dogfight)")
ax_main.set_xlabel("X (m)")
ax_main.set_ylabel("Y (m)")
ax_main.set_zlabel("Altitude (m)")

# Make the visible region smaller so we can see the flight better
ax_main.set_xlim(0, 16000)
ax_main.set_ylim(5000, 9000)
ax_main.set_zlim(0, 5000)
ax_main.view_init(elev=30, azim=-60)

# Subplots
ranges = np.array([0, 500, 1000, 1500])
drop_vals = np.array([0, -0.2, -0.9, -2.5])
ax_bullet_drop.plot(ranges, drop_vals, 'm-o', label='.50 cal Drop')
ax_bullet_drop.fill_between(ranges, drop_vals, color='m', alpha=0.1)
ax_bullet_drop.axhline(y=0, color='gray', linestyle='--')
ax_bullet_drop.set_title("Bearcat .50 cal Bullet Drop vs. Range")
ax_bullet_drop.set_xlabel("Range (m)")
ax_bullet_drop.set_ylabel("Vertical Drop (m)")
ax_bullet_drop.legend()
ax_bullet_drop.grid(True)

alt_km = np.array([0, 3, 6, 10])
climb_vals = np.array([25.2, 20.5, 17.7, 10.6])
ax_climb_rate.plot(alt_km, climb_vals, 'g-s', label='Climb Rate (m/s)')
ax_climb_rate.set_title("Bearcat Climb Rate vs. Altitude")
ax_climb_rate.set_xlabel("Altitude (km)")
ax_climb_rate.set_ylabel("Climb Rate (m/s)")
ax_climb_rate.legend()
ax_climb_rate.grid(True)

plt.tight_layout()

###############################################################################
# 6. AAA WITH TURRET AIM
###############################################################################
def create_aaa_geometry(cx,cy,cz,size_base=100,height_base=50,size_turret=70,
                        turret_angle_deg=0):
    """
    Two-part geometry: large block base + turret on top that 'rotates' to aim.
    We'll rotate the turret top by turret_angle_deg around the vertical axis.
    """
    from math import cos, radians, sin
    angle_r = radians(turret_angle_deg)

    b=size_base/2
    base_bottom=cz
    base_top=cz+height_base

    # Base block:
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

    # Turret block:
    turret_z_bottom = base_top
    turret_z_top    = base_top + 30
    half_t = size_turret/2

    # We'll "rotate" the turret by angle_r around the center (cx,cy).
    def rotX(x_,y_):
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
    turret_verts_bot = []
    for (xx,yy,zz) in t_verts_bot_raw:
        rx, ry = rotX(xx,yy)
        turret_verts_bot.append((rx,ry,zz))

    t_verts_top_raw = [
        (cx-half_t, cy-half_t, turret_z_top),
        (cx+half_t, cy-half_t, turret_z_top),
        (cx+half_t, cy+half_t, turret_z_top),
        (cx-half_t, cy+half_t, turret_z_top),
    ]
    turret_verts_top = []
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

def ground_aaa_position(frame, center_x, center_y, radius=600):
    """
    Moves the AAA in a circle.
    """
    t = (frame%200)/200.0
    angle = 2*math.pi*t
    gx = center_x + radius*math.cos(angle)
    gy = center_y + radius*math.sin(angle)
    gz = 0
    return gx,gy,gz

###############################################################################
# 7. LOCKON + DOGFIGHT BOGIE
###############################################################################
bogie_x = np.full(frames_total, np.nan)
bogie_y = np.full(frames_total, np.nan)
bogie_z = np.full(frames_total, np.nan)

bogie_appear = idxD_end - 20
bx_start=20000; by_start=7500; bz_start=500

for f in range(frames_total):
    if f<bogie_appear:
        continue
    else:
        if f==bogie_appear:
            bogie_x[f] = bx_start
            bogie_y[f] = by_start
            bogie_z[f] = bz_start
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
# 8. EXPLOSION + PARACHUTE
###############################################################################
explosion_active=False
explosion_frame=0
explosion_max_frames=30
explosion_poly=None
explosion_center=(0,0,0)

def spawn_explosion(center):
    global explosion_active, explosion_frame, explosion_center, explosion_poly
    explosion_active=True
    explosion_frame=0
    explosion_center=center
    if explosion_poly is not None:
        explosion_poly.remove()
        explosion_poly=None

parachute_poly=None
parachute_active=False
parachute_frame=0
parachute_center=(0,0,0)

def spawn_parachute(center):
    global parachute_active, parachute_frame, parachute_center
    parachute_active=True
    parachute_frame=0
    parachute_center=center

###############################################################################
# 9. AIRCRAFT 3D MODEL (Bearcat & Bogie)
###############################################################################
def create_bearcat_model(position, direction, scale=80, color='cyan'):
    """
    More detailed shape than a simple wedge: approximate short wings + cylindrical nose.
    We'll keep it simple but better than a single tetra.
    """
    px,py,pz = position
    dx,dy,dz = direction
    mag = math.sqrt(dx*dx + dy*dy + dz*dz)
    if mag<1e-6:
        dx,dy,dz=1,0,0
        mag=1
    dx/=mag; dy/=mag; dz/=mag

    # We'll define local geometry in XY-plane, then transform.
    # A rough 'fighter' shape from top view:
    #     nose = (1.5, 0)
    #     left_wing = (0, -0.8)
    #     right_wing= (0, 0.8)
    #     tail = (-1.3,0)
    # Then extrude a bit in the "Z" to give thickness.
    # We do a simple top-lid + bottom-lid, connect sides => a small prism.

    # scale factor (the user wants them smaller relative to the environment):
    scale_fac = scale

    # 2D top silhouette:
    nose = np.array([1.5, 0.0])
    left_wing = np.array([0.0, -0.8])
    right_wing= np.array([0.0, 0.8])
    tail = np.array([-1.3, 0.0])

    # Multiply all x,y by scale_fac
    nose      *= scale_fac
    left_wing *= scale_fac
    right_wing*= scale_fac
    tail      *= scale_fac

    # We'll create top-lid (z=+0.2*scale_fac) and bottom-lid (z=-0.2*scale_fac)
    thickness = 0.15*scale_fac

    top_pts = [
        [nose[0], nose[1], thickness],
        [right_wing[0], right_wing[1], thickness],
        [tail[0], tail[1], thickness],
        [left_wing[0], left_wing[1], thickness],
    ]
    bottom_pts = [
        [nose[0], nose[1], -thickness],
        [right_wing[0], right_wing[1], -thickness],
        [tail[0], tail[1], -thickness],
        [left_wing[0], left_wing[1], -thickness],
    ]

    # So we have a "barrel" shape. We'll define faces:
    faces = []
    # top face
    faces.append([top_pts[0], top_pts[1], top_pts[2], top_pts[3]])
    # bottom face
    faces.append([bottom_pts[0], bottom_pts[1], bottom_pts[2], bottom_pts[3]])
    # sides
    for i in range(4):
        i2 = (i+1)%4
        faces.append([
            top_pts[i], top_pts[i2], bottom_pts[i2], bottom_pts[i]
        ])

    # We now transform each vertex by the orientation (dx,dy,dz).
    forward = np.array([dx,dy,dz])
    # pick an "up" guess:
    up_guess = np.array([0,0,1])
    side = np.cross(forward, up_guess)
    side_mag = np.linalg.norm(side)
    if side_mag<1e-6:
        side = np.cross(forward,[1,0,0])
        side_mag=np.linalg.norm(side)
    side/=side_mag
    up = np.cross(side, forward)
    # build rotation matrix:
    R = np.vstack([forward, side, up]).T

    def transform_local(pt):
        # pt is local, shape = [x,y,z]
        # transform by R => world, then shift by position
        local = np.array(pt)
        return position + R.dot(local)

    # For each face => transform
    face_world=[]
    for f in faces:
        face_w=[]
        for v_ in f:
            face_w.append(transform_local(v_))
        face_world.append(face_w)

    poly = Poly3DCollection(face_world,facecolor=color,alpha=1.0)
    poly.set_edgecolor('black')
    return poly

###############################################################################
# 10. BULLETS & ROCKETS (Keeping old logic but clamp shapes)
###############################################################################
active_bullets = []
active_rockets = []

def clamp_xyz_arrays(x_, y_, z_):
    """Clamp arrays so they have same length, to avoid shape mismatch."""
    min_len = min(len(x_), len(y_), len(z_))
    return x_[:min_len], y_[:min_len], z_[:min_len]

def simulate_bullet_trajectory(plane_pos, plane_vel, muzzle_speed=890,
                               dt=0.02, max_time=2.0, gravity=9.81):
    px,py,pz = plane_pos
    vx_p,vy_p,vz_p = plane_vel
    speed_plane = math.sqrt(vx_p*vx_p + vy_p*vy_p + vz_p*vz_p)
    if speed_plane < 1e-6:
        direction=(1,0,0)
    else:
        direction=(vx_p/speed_plane,vy_p/speed_plane,vz_p/speed_plane)
    bullet_speed = speed_plane + muzzle_speed
    vx_ = bullet_speed*direction[0]
    vy_ = bullet_speed*direction[1]
    vz_ = bullet_speed*direction[2]

    bx=[px]; by=[py]; bz=[pz]
    t=0
    while t<max_time:
        xnew = bx[-1]+vx_*dt
        ynew = by[-1]+vy_*dt
        znew = bz[-1]+vz_*dt
        vz_ -= gravity*dt
        if znew<=0:
            znew=0
            bx.append(xnew); by.append(ynew); bz.append(znew)
            break
        bx.append(xnew); by.append(ynew); bz.append(znew)
        t+=dt

    bx_,by_,bz_ = clamp_xyz_arrays(np.array(bx),np.array(by),np.array(bz))
    return bx_,by_,bz_

def spawn_bullets(px,py,pz,vx,vy,vz,muzzle_speed=890,num_bullets=1):
    for _ in range(num_bullets):
        bx_,by_,bz_ = simulate_bullet_trajectory((px,py,pz),(vx,vy,vz),
                                                 muzzle_speed=muzzle_speed)
        bullet = {'x':bx_,'y':by_,'z':bz_,'index':0,'line':None}
        active_bullets.append(bullet)

def simulate_rocket_trajectory(plane_pos, plane_vel, rocket_speed=320,
                               dt=0.05, max_time=10.0, thrust_dur=3.0):
    px,py,pz = plane_pos
    vx_p,vy_p,vz_p = plane_vel
    speed_plane = math.sqrt(vx_p*vx_p + vy_p*vy_p + vz_p*vz_p)
    if speed_plane<1e-6:
        direction=(1,0,0)
    else:
        direction=(vx_p/speed_plane, vy_p/speed_plane, vz_p/speed_plane)
    vx_r = speed_plane + rocket_speed
    vx_vec=[vx_r*direction[0], vx_r*direction[1], vx_r*direction[2]]
    g=9.81

    rx=[px]; ry=[py]; rz=[pz]
    t=0
    while t<max_time:
        if t<thrust_dur:
            # small forward thrust
            vx_vec[0]+=5*dt*direction[0]
            vx_vec[1]+=5*dt*direction[1]
            vx_vec[2]+=5*dt*direction[2]
        vx_,vy_,vz_ = vx_vec
        vx_vec[2] -= g*dt
        xnew=rx[-1]+vx_*dt
        ynew=ry[-1]+vy_*dt
        znew=rz[-1]+vz_*dt
        if znew<=0:
            znew=0
            rx.append(xnew); ry.append(ynew); rz.append(znew)
            break
        rx.append(xnew); ry.append(ynew); rz.append(znew)
        t+=dt

    rx_,ry_,rz_ = clamp_xyz_arrays(np.array(rx),np.array(ry),np.array(rz))
    return rx_,ry_,rz_

def spawn_rocket(px,py,pz,vx,vy,vz):
    rx_,ry_,rz_=simulate_rocket_trajectory((px,py,pz),(vx,vy,vz))
    rocket={'x':rx_,'y':ry_,'z':rz_,'index':0,'line':None}
    active_rockets.append(rocket)

###############################################################################
# 11. BOMB
###############################################################################
bomb_drop_frame = idxB_end + (numC//2)
if bomb_drop_frame>=frames_total:
    bomb_drop_frame=frames_total-1
bomb_init_x = flight_x[bomb_drop_frame]
bomb_init_y = flight_y[bomb_drop_frame]
bomb_init_z = flight_z[bomb_drop_frame]

if bomb_drop_frame>0:
    pxp=flight_x[bomb_drop_frame-1]
    pyp=flight_y[bomb_drop_frame-1]
    pzp=flight_z[bomb_drop_frame-1]
    vx_plane=(bomb_init_x-pxp)*25
    vy_plane=(bomb_init_y-pyp)*25
    vz_plane=(bomb_init_z-pzp)*25
else:
    vx_plane=vy_plane=vz_plane=0

def simulate_bomb_trajectory(xi,yi,zi,vx_i,vy_i,vz_i,
                             dt=0.03, drag=0.00025, max_time=50):
    g=9.81*0.75
    bx=[xi]; by=[yi]; bz=[zi]
    vx,vy,vz=vx_i,vy_i,vz_i
    t=0
    while t<max_time:
        xnew=bx[-1]+vx*dt
        ynew=by[-1]+vy*dt
        znew=bz[-1]+vz*dt
        spd_xy = math.hypot(vx,vy)
        if spd_xy>1e-3:
            drag_f=drag*spd_xy**2
            vx-=drag_f*(vx/spd_xy)*dt
            vy-=drag_f*(vy/spd_xy)*dt
        vz-=g*dt
        if znew<=0:
            znew=0
            bx.append(xnew); by.append(ynew); bz.append(znew)
            break
        bx.append(xnew); by.append(ynew); bz.append(znew)
        t+=dt
    bx_,by_,bz_=clamp_xyz_arrays(np.array(bx),np.array(by),np.array(bz))
    return bx_,by_,bz_

bomb_x,bomb_y,bomb_z = simulate_bomb_trajectory(
    bomb_init_x,bomb_init_y,bomb_init_z,
    vx_plane,vy_plane,vz_plane
)
bomb_marker=None
bomb_explosion_triggered=False

###############################################################################
# 12. ANIMATION UTILS
###############################################################################
def update_explosion():
    global explosion_active, explosion_frame, explosion_poly
    if not explosion_active:
        return
    if explosion_poly is not None:
        explosion_poly.remove()
    frac=explosion_frame/float(explosion_max_frames)
    radius=10+80*frac
    th,ph=np.mgrid[0:np.pi:15j,0:2*np.pi:15j]
    xs=radius*np.sin(th)*np.cos(ph)+explosion_center[0]
    ys=radius*np.sin(th)*np.sin(ph)+explosion_center[1]
    zs=radius*np.cos(th)+explosion_center[2]
    explosion_poly=ax_main.plot_surface(xs,ys,zs,color='orange',alpha=1.0,edgecolor='red')
    explosion_frame+=1
    if explosion_frame>=explosion_max_frames:
        explosion_active=False
        if explosion_poly is not None:
            explosion_poly.remove()
            explosion_poly=None

def update_parachute():
    global parachute_active, parachute_frame, parachute_poly
    if not parachute_active:
        return
    if parachute_poly is not None:
        parachute_poly.remove()
    t=parachute_frame
    dx=parachute_center[0]+10*math.sin(0.1*t)
    dy=parachute_center[1]+10*math.cos(0.1*t)
    dz=parachute_center[2]-3*t
    if dz<0:
        dz=0
    size=50
    half=size/2
    corners=[
        (dx-half,dy-half,dz+20),
        (dx+half,dy-half,dz+20),
        (dx+half,dy+half,dz+20),
        (dx-half,dy+half,dz+20),
    ]
    faces=[ [corners[0],corners[1],corners[2],corners[3]] ]
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
# 13. INIT + UPDATE
###############################################################################
bearcat_poly=None
bogie_poly=None
lockon_line=None
lockon_line_radius=300
lockon_line_shrink=3.0
target_destroyed_text=None

def init_animation():
    return ()

def update_animation(frame):
    global bearcat_poly, bogie_poly
    global bomb_marker, bomb_explosion_triggered
    global bogie_is_hit, bogie_hit_frame
    global lockon_line, lockon_line_radius
    global target_destroyed_text

    # FLASHING ARROWS (we do simpler approach: skip lines, if you want you can keep quivers)
    # For brevity, we skip them or do nothing special.

    # 1) Bearcat
    if bearcat_poly is not None:
        bearcat_poly.remove()
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
        bearcat_poly=create_bearcat_model((bcx,bcy,bcz),(vx_bc,vy_bc,vz_bc),
                                          scale=80,color='cyan')
        ax_main.add_collection3d(bearcat_poly)

    # 2) Bomb marker
    global bomb_drop_frame
    global bomb_x,bomb_y,bomb_z
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
            # blink faster near impact
            blink_rate=20.0 - 0.02*alt
            if blink_rate<2: blink_rate=2
            bomb_blink_on=((frame//int(blink_rate))%2==0)
            if alt>0 and bomb_blink_on:
                bomb_marker=ax_main.scatter([bx_],[by_],[bz_],color='red',s=50,marker='o')
            if alt<=0 and not bomb_explosion_triggered:
                bomb_explosion_triggered=True
                spawn_explosion((bx_,by_,0))

    # 3) Bogie
    if bogie_poly is not None:
        bogie_poly.remove()
    if frame<frames_total and not np.isnan(bogie_x[frame]):
        if bogie_is_hit:
            n=frame-bogie_hit_frame
            if n<0: n=0
            oldx=bogie_x[bogie_hit_frame]
            oldy=bogie_y[bogie_hit_frame]
            oldz=bogie_z[bogie_hit_frame]
            angle=0.4*n
            rad=50+5*n
            bxx=oldx+rad*math.cos(angle)
            byy=oldy+rad*math.sin(angle)
            bzz=oldz-30*n
            if bzz<0: bzz=0
            bogie_x[frame]=bxx
            bogie_y[frame]=byy
            bogie_z[frame]=bzz
            if bzz<=0:
                if not explosion_active:
                    spawn_explosion((bxx,byy,0))
                    spawn_parachute((bxx,byy,0))

        btx=bogie_x[frame]
        bty=bogie_y[frame]
        btz=bogie_z[frame]
        if frame>0 and not np.isnan(bogie_x[frame-1]):
            vx_bog=bogie_x[frame]-bogie_x[frame-1]
            vy_bog=bogie_y[frame]-bogie_y[frame-1]
            vz_bog=bogie_z[frame]-bogie_z[frame-1]
        else:
            vx_bog=vy_bog=vz_bog=0
        bogie_poly=create_bearcat_model((btx,bty,btz),(vx_bog,vy_bog,vz_bog),
                                        scale=80,color='red')
        ax_main.add_collection3d(bogie_poly)

    # 4) Strafe-phase => lockon reticle
    strafe_s, strafe_e = phase_slices["Strafe"]
    if lockon_line is not None:
        lockon_line.remove()
        lockon_line=None
    if strafe_s<=frame<strafe_e:
        if lockon_line_radius>0:
            angles=np.linspace(0,2*math.pi,36)
            center_=(10000,7000,0)
            xs=center_[0]+lockon_line_radius*np.cos(angles)
            ys=center_[1]+lockon_line_radius*np.sin(angles)
            zs=np.full_like(xs, center_[2]+10)
            lockon_line,=ax_main.plot(xs,ys,zs,color='red',linewidth=1)
            lockon_line_radius-=lockon_line_shrink
            if lockon_line_radius<0:
                lockon_line_radius=0
    else:
        lockon_line_radius=300

    if frame==strafe_e:
        global target_destroyed_text
        if target_destroyed_text is None:
            target_destroyed_text=ax_main.text(10000,7000,100,"Target Destroyed",
                                              color='red',fontsize=10)

    # 5) Bullets & Rockets
    # Strafe bullets
    if strafe_s<=frame<strafe_e:
        if frame%15==0 and frame>0:
            px=flight_x[frame]
            py=flight_y[frame]
            pz=flight_z[frame]
            vx_=flight_x[frame]-flight_x[frame-1]
            vy_=flight_y[frame]-flight_y[frame-1]
            vz_=flight_z[frame]-flight_z[frame-1]
            spawn_bullets(px,py,pz,vx_,vy_,vz_,num_bullets=2)

    # Bombing => spawn rocket
    bomb_s,bomb_e=phase_slices["Bombing"]
    mid_bomb=bomb_s+(bomb_e-bomb_s)//2
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
    dog_s,dog_e=phase_slices["Dogfight"]
    if dog_s<=frame<dog_e:
        # Bearcat
        if frame%15==0 and frame>0:
            px=flight_x[frame]
            py=flight_y[frame]
            pz=flight_z[frame]
            vx_=flight_x[frame]-flight_x[frame-1]
            vy_=flight_y[frame]-flight_y[frame-1]
            vz_=flight_z[frame]-flight_z[frame-1]
            spawn_bullets(px,py,pz,vx_,vy_,vz_,num_bullets=2)
        # Bogie
        if frame%15==0 and frame>0 and not bogie_is_hit:
            bx_=bogie_x[frame]
            by_=bogie_y[frame]
            bz_=bogie_z[frame]
            if not np.isnan(bx_):
                vx_=bogie_x[frame]-bogie_x[frame-1]
                vy_=bogie_y[frame]-bogie_y[frame-1]
                vz_=bogie_z[frame]-bogie_z[frame-1]
                spawn_bullets(bx_,by_,bz_,vx_,vy_,vz_,muzzle_speed=10000,num_bullets=3)
        # halfway => hit bogie
        half_dog=dog_s+(dog_e-dog_s)//2
        if frame==half_dog and not bogie_is_hit:
            bogie_is_hit=True
            bogie_hit_frame=frame

    # 6) Update bullets
    done_bul=[]
    for bullet in active_bullets:
        idx=bullet['index']
        bx_arr=bullet['x']
        by_arr=bullet['y']
        bz_arr=bullet['z']
        max_len=len(bx_arr)
        if idx<max_len:
            bullet['index']+=1
            i=bullet['index']
            # clamp i
            if i>max_len:
                i=max_len
            if bullet['line'] is None:
                line_,=ax_main.plot([],[],[],color='yellow',linewidth=1)
                bullet['line']=line_
            bullet['line'].set_data_3d(bx_arr[:i], by_arr[:i], bz_arr[:i])
        else:
            if bullet['line'] is not None:
                bullet['line'].remove()
            bullet['line']=None
            done_bul.append(bullet)
    for b_ in done_bul:
        active_bullets.remove(b_)

    # 7) Update rockets
    done_roc=[]
    for rocket in active_rockets:
        idx=rocket['index']
        rx_arr=rocket['x']
        ry_arr=rocket['y']
        rz_arr=rocket['z']
        max_len=len(rx_arr)
        if idx<max_len:
            rocket['index']+=1
            i=rocket['index']
            if i>max_len:
                i=max_len
            if rocket['line'] is None:
                rline,=ax_main.plot([],[],[],color='magenta',linewidth=2)
                rocket['line']=rline
            rocket['line'].set_data_3d(rx_arr[:i], ry_arr[:i], rz_arr[:i])
        else:
            if rocket['line'] is not None:
                rocket['line'].remove()
            rocket['line']=None
            done_roc.append(rocket)
    for r_ in done_roc:
        active_rockets.remove(r_)

    # 8) Bomb explosion
    # If we want to ensure an explosion if bomb ended:
    if frame==(idxC_end+5) and not bomb_explosion_triggered and len(bomb_x)>0:
        bomb_explosion_triggered=True
        spawn_explosion((bomb_x[-1],bomb_y[-1],0))
    update_explosion()

    # 9) AAA => we remove old + re-add with turret angle
    for c_ in ax_main.collections[:]:
        if getattr(c_,'_aaa_flag',False):
            c_.remove()

    # AAA #1
    gx1,gy1,gz1=ground_aaa_position(frame,10000,7000, radius=700)
    # turret aims at Bearcat => angle
    # Find vector from AAA to Bearcat:
    if frame<frames_total:
        ax_ = flight_x[frame]-gx1
        ay_ = flight_y[frame]-gy1
        angle_aaa = math.degrees(math.atan2(ay_,ax_))
    else:
        angle_aaa=0
    faces1 = create_aaa_geometry(gx1,gy1,gz1,size_base=120,height_base=50,
                                 size_turret=70,turret_angle_deg=angle_aaa)
    col1=Poly3DCollection(faces1,facecolor='brown',alpha=0.9)
    col1.set_edgecolor('white')
    col1._aaa_flag=True
    ax_main.add_collection3d(col1)

    # AAA #2
    gx2,gy2,gz2=ground_aaa_position(frame+30,15000,7500, radius=900)
    if frame<frames_total:
        ax2_ = flight_x[frame]-gx2
        ay2_ = flight_y[frame]-gy2
        angle_aaa2=math.degrees(math.atan2(ay2_,ax2_))
    else:
        angle_aaa2=0
    faces2 = create_aaa_geometry(gx2,gy2,gz2,size_base=150,height_base=60,
                                 size_turret=80,turret_angle_deg=angle_aaa2)
    col2=Poly3DCollection(faces2,facecolor='black',alpha=0.9)
    col2.set_edgecolor('white')
    col2._aaa_flag=True
    ax_main.add_collection3d(col2)

    # 10) Parachute
    update_parachute()

    return ()

###############################################################################
# 14. RUN
###############################################################################
anim = FuncAnimation(fig, update_animation,
                     init_func=init_animation,
                     frames=frames_total,
                     interval=80,
                     blit=False)
plt.show()
