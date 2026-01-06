
import math  # type: ignore
from typing import Any, Dict, List, Optional, Sequence, Tuple  # type: ignore

import matplotlib as mpl  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import numpy as np  # type: ignore
import requests  # type: ignore
from cycler import cycler  # type: ignore
from matplotlib.animation import FuncAnimation  # type: ignore
from matplotlib.lines import Line2D  # type: ignore
from matplotlib.text import Text  # type: ignore
from mpl_toolkits.mplot3d import Axes3D  # type: ignore
from mpl_toolkits.mplot3d.art3d import Line3DCollection  # type: ignore
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # type: ignore
from numpy.typing import NDArray  # type: ignore

api_spec = """api: ver x.x.x
info:
  title: War Thunder Vehicles API (Fully Advanced)
  description: |
    This is the advanced, unofficial War Thunder Vehicles API, now including dynamic vehicle data retrieval,
    modifications, strategic analysis, key binding recommendations, and vehicle research suggestions powered by OpenAI.
    Not affiliated with Gaijin Entertainment.
  version: 4.0.0
  contact:
    email: studente.cosimo.sgambelluri@gmail.com
  license:
    name: GNU 3.0
    url: https://www.gnu.org/licenses/gpl-3.0.en.html
servers:
  - description: Main Server
    url: https://www.wtvehiclesapi.sgambe.serv00.net/api
tags:
  - name: Vehicles
    description: Endpoints to retrieve or search vehicle data.
  - name: Analysis
    description: Endpoints for AI-powered analysis and strategic assistance.
  - name: Search
    description: Search vehicles by name or other attributes.
  - name: Collection
    description: Collection management operations.
  - name: ThunderAPI
    description: Integration with the ThunderAPI for player and clan data.
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-KEY
  responses:
    NotFound:
      description: Resource not found.
      content:
        application/json:
          schema:
            type: object
            properties:
              error:
                type: string
              message:
                type: string
    BadRequest:
      description: Bad request or invalid parameters.
      content:
        application/json:
          schema:
            type: object
            properties:
              error:
                type: string
              message:
                type: string
    InternalServerError:
      description: Internal server error.
      content:
        application/json:
          schema:
            type: object
            properties:
              error:
                type: string
              message:
                type: string
components:
  schemas:
    ErrorResponse:
      type: object
      properties:
        error:
          type: string
          example: "Bad Request"
        message:
          type: string
          example: "Invalid query parameters."
      required:
        - error
        - message
    VehicleGeneric:
      type: object
      properties:
        identifier:
          type: string
        country:
          type: string
        vehicle_type:
          type: string
        era:
          type: integer
          format: int32
        arcade_br:
          type: integer
          format: int32
        realistic_br:
          type: integer
          format: int32
        realistic_ground_br:
          type: integer
          format: int32
        simulator_br:
          type: integer
          format: int32
        simulator_ground_br:
          type: integer
          format: int32
        event:
          oneOf:
            - type: string
            - type: "null"
        release_date:
          oneOf:
            - type: string
              format: date-time
            - type: "null"
        is_premium:
          type: boolean
        is_pack:
          type: boolean
        on_marketplace:
          type: boolean
        squadron_vehicle:
          type: boolean
        value:
          type: integer
          format: int32
        req_exp:
          type: integer
          format: int32
        ge_cost:
          type: integer
          format: int32
        sl_mul_arcade:
          type: number
        sl_mul_realistic:
          type: number
        sl_mul_simulator:
          type: number
        exp_mul:
          type: number
        crew_total_count:
          type: number
        visibility:
          type: number
        hull_armor:
          type: array
          items:
            type: integer
            format: int32
          minItems: 0
          maxItems: 3
        turret_armor:
          type: array
          items:
            type: integer
            format: int32
          minItems: 0
          maxItems: 3
        images:
          type: object
          properties:
            image:
              type: string
            techtree:
              type: string
paths:
  /vehicles:
    get:
      tags:
        - Vehicles
      summary: Get all vehicles
      description: List vehicles by filters, up to 200.
      operationId: getAllVehicles
      security:
        - ApiKeyAuth: []
      parameters:
        - name: limit
          in: query
          description: Max returned count.
          schema:
            type: integer
            minimum: 0
            maximum: 200
            default: 200
        - name: page
          in: query
          description: Pagination offset.
          schema:
            type: integer
            minimum: 0
            default: 0
        - name: country
          in: query
          description: Filter by country.
          schema:
            type: string
            enum:
              - britain
              - china
              - france
              - germany
              - israel
              - italy
              - japan
              - sweden
              - usa
              - ussr
        - name: vehicle_type
          in: query
          description: Filter by vehicle type.
          schema:
            type: string
            enum:
              - tank
              - light_tank
              - medium_tank
              - heavy_tank
              - tank_destroyer
              - spaa
              - lbv
              - mbv
              - hbv
              - exoskeleton
              - attack_helicopter
              - utility_helicopter
              - fighter
              - assault
              - bomber
              - ship
              - destroyer
              - light_cruiser
              - boat
              - heavy_boat
              - barge
              - frigate
              - heavy_cruiser
              - battlecruiser
              - battleship
              - submarine
        - name: era
          in: query
          description: Filter by vehicle era.
          schema:
            type: integer
        - name: isPremium
          in: query
          description: Filter by premium status.
          schema:
            type: boolean
            default: false
        - name: isPack
          in: query
          description: Filter by pack status.
          schema:
            type: boolean
            default: false
        - name: isSquadronVehicle
          in: query
          description: Filter by squadron vehicle status.
          schema:
            type: boolean
            default: false
        - name: isOnMarketplace
          in: query
          description: Filter by marketplace availability.
          schema:
            type: boolean
            default: false
        - name: excludeKillstreak
          in: query
          description: Exclude killstreak vehicles.
          schema:
            type: boolean
            default: true
        - name: excludeEventVehicles
          in: query
          description: Exclude event vehicles.
          schema:
            type: boolean
            default: true
      responses:
        "200":
          description: Vehicles matching criteria
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/VehicleGeneric"
        "400":
          $ref: "#/components/responses/BadRequest"
        "404":
          $ref: "#/components/responses/NotFound"
  /vehicles/{identifier}:
    get:
      tags:
        - Vehicles
      summary: Get vehicle by ID
      description: Fetch one vehicle by identifier.
      operationId: getVehicleByIdentifier
      parameters:
        - name: identifier
          in: path
          required: true
          description: Vehicle ID (e.g., yak-7b).
          schema:
            type: string
      responses:
        "200":
          description: Vehicle found.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/VehicleGeneric"
        "404":
          description: Not found.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
              example:
                error: Not Found
                message: No vehicle found.
  /vehicles/{identifier}/{version}:
    get:
      tags:
        - Vehicles
      summary: Get vehicle by ID & version
      description: Fetch a vehicle from a specific game version.
      operationId: getVehicleByIdentifierAndVersion
      parameters:
        - name: identifier
          in: path
          required: true
          description: e.g., yak-7b
          schema:
            type: string
        - name: version
          in: path
          required: true
          description: e.g., 2.37.0.10
          schema:
            type: string
      responses:
        "200":
          description: Version-specific vehicle found.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/VehicleGeneric"
        "404":
          description: Not found.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
              example:
                error: Not Found
                message: No vehicle found with given ID/version.
  /vehicles/search/{name}:
    get:
      tags:
        - Search
      summary: Search by name
      description: Returns vehicle IDs for a given name.
      operationId: searchVehicleByName
      parameters:
        - name: name
          in: path
          required: true
          description: Name search (e.g., t-34).
          schema:
            type: string
      responses:
        "200":
          description: IDs returned.
          content:
            application/json:
              schema:
                type: array
                maxItems: 200
                items:
                  type: string
        "404":
          description: No matches.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
              example:
                error: Not Found
                message: No vehicle IDs match query.
  /analysis:
    post:
      tags:
        - Analysis
      summary: Perform vehicle analysis
      description: Perform an analysis based on vehicle attributes and AI-powered recommendations.
      operationId: analyzeVehicle
      security:
        - ApiKeyAuth: []
      requestBody:
        description: Vehicle data for analysis
        content:
          application/json:
            schema:
              type: object
              properties:
                identifier:
                  type: string
                  description: Vehicle ID (e.g., yak-7b).
                analysis_type:
                  type: string
                  enum:
                    - strategic
                    - key_bindings
                    - vehicle_research
                  description: Type of analysis to perform.
      responses:
        "200":
          description: Analysis results
          content:
            application/json:
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: Detailed analysis of the vehicle's capabilities and strategic uses.
        "400":
          description: Bad request.
        "404":
          description: Not found.
  /collection:
    get:
      tags:
        - Collection
      summary: Get vehicle collection
      description: Retrieve user's vehicle collection based on filter and page size.
      operationId: getVehicleCollection
      security:
        - ApiKeyAuth: []
      parameters:
        - name: limit
          in: query
          description: Max returned count.
          schema:
            type: integer
            minimum: 0
            maximum: 200
            default: 200
        - name: page
          in: query
          description: Pagination offset.
          schema:
            type: integer
            minimum: 0
            default: 0
      responses:
        "200":
          description: User collection retrieved.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/VehicleGeneric"
        "400":
          description: Bad request.
  /thunderapi/{playerId}/stats:
    get:
      tags:
        - ThunderAPI
      summary: Get player statistics
      description: Retrieve player stats and achievements.
      operationId: getPlayerStats
      parameters:
        - name: playerId
          in: path
          required: true
          description: Player ID for ThunderAPI.
          schema:
            type: string
      responses:
        "200":
          description: Player stats returned.
          content:
            application/json:
              schema:
                type: object
                properties:
                  stats:
                    type: object
                    example:
                      total_battles: 4000
                      victories: 2500
                      losses: 1500
        "404":
          description: Player not found.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
              example:
                error: Not Found
                message: Player not found.
"""

privacy_policy = "https://www.wtve.net/privacy"

def get_all_vehicles():
    url = "https://www.wtvehiclesapi.sgambe.serv00.net/api/vehicles"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None

def get_vehicle_by_identifier(identifier):
    url = "https://www.wtvehiclesapi.sgambe.serv00.net/api/vehicles/" + identifier
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None

def analyze_vehicle(identifier, analysis_type):
    url = "https://www.wtvehiclesapi.sgambe.serv00.net/api/analysis"
    payload = {"identifier": identifier, "analysis_type": analysis_type}
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        return r.json()
    return None

active_bullets: List[Dict[str, Any]] = []
active_rockets: List[Dict[str, Any]] = []
targets = []
target_destroyed = []
bogie_poly: Optional[Poly3DCollection]

mpl.rcParams['figure.facecolor'] = 'black'
mpl.rcParams['axes.facecolor'] = 'black'
mpl.rcParams['axes.edgecolor'] = '(0.05,0.05,0.1)'
mpl.rcParams['axes.linewidth'] = 1
mpl.rcParams['grid.color'] = "none"
mpl.rcParams['grid.alpha'] = 0
mpl.rcParams['grid.linestyle'] = ':'
mpl.rcParams['axes.grid'] = False
mpl.rcParams['figure.dpi'] = 75
mpl.rcParams['savefig.dpi'] = 120
mpl.rcParams['savefig.facecolor'] = 'black'
mpl.rcParams['savefig.edgecolor'] = 'black'
mpl.rcParams['savefig.transparent'] = True
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.size'] = 10
mpl.rcParams['axes.labelsize'] = 10
mpl.rcParams['axes.titlesize'] = 10
mpl.rcParams['axes.titleweight'] = 'bold'
mpl.rcParams['axes.titlecolor'] = '#FF0000'
mpl.rcParams['legend.fontsize'] = 8
mpl.rcParams['legend.frameon'] = True
mpl.rcParams['legend.fancybox'] = True
mpl.rcParams['legend.framealpha'] = 1
mpl.rcParams['legend.edgecolor'] = 'none'
mpl.rcParams['xtick.color'] = 'none'
mpl.rcParams['ytick.color'] = 'none'
mpl.rcParams['axes.prop_cycle'] = cycler(color=[
    "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
    "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"
])
mpl.rcParams['lines.linewidth'] = 1.0
mpl.rcParams['lines.markersize'] = 5
mpl.rcParams['lines.markeredgewidth'] = 1.3
mpl.rcParams['axes.spines.top'] = True
mpl.rcParams['axes.spines.right'] = True
mpl.rcParams['axes.spines.left'] = True
mpl.rcParams['axes.spines.bottom'] = False
mpl.rcParams['axes.xmargin'] = 0.02
mpl.rcParams['axes.ymargin'] = 0.02
mpl.rcParams['lines.antialiased'] = True
mpl.rcParams['patch.antialiased'] = True
mpl.rcParams['lines.solid_capstyle'] = 'butt'
mpl.rcParams['lines.solid_joinstyle'] = 'miter'
mpl.rcParams['lines.dash_capstyle'] = 'butt'
mpl.rcParams['lines.dash_joinstyle'] = 'miter'
mpl.rcParams['xtick.major.size'] = 10
mpl.rcParams['xtick.minor.size'] = 3
mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['xtick.top'] = False
mpl.rcParams['ytick.left'] = True
mpl.rcParams['axes.unicode_minus'] = True
mpl.rcParams['axes.autolimit_mode'] = 'round_numbers'
mpl.rcParams['axes.axisbelow'] = True
mpl.rcParams['toolbar'] = 'None'
mpl.rcParams['figure.figsize'] = (10,8)

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
        "Loaded_Weight_kg": 4220
    },
    "Engine": {
        "Designation": "Pratt & Whitney R-2800-34W",
        "Type": "Two-row, 18-cylinder radial, air-cooled",
        "Horsepower_HP": 2250,
        "Takeoff_Power_HP": 2800,
        "Supercharger_Stages": "Two-speed mechanical",
        "Optimal_Manifold_Pressure_psi": 54,
        "Propeller": "Hamilton Standard Hydromatic, 3.96 m diameter"
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
        "Landing_Distance_ft": 750,
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
        "Bombs_and_Rockets": {
            "Bomb_Hardpoints": 1,
            "1x_1000_lb_Bomb_ANM65A1": {
                "Damage_Radius_m": [15, 25],
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

phases_info = {
    "Approach": ("blue", 60),
    "Strafe": ("orange", 50),
    "Bombing": ("red", 50),
    "Escape": ("green", 60),
    "Dogfight": ("purple", 70)
}

def generate_path(start: Tuple[float, float, float], end: Tuple[float, float, float], num_points: int, curve: str = "") -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    x0, y0, z0 = start
    x1, y1, z1 = end
    t_vals = np.linspace(0, 1, num_points, dtype=np.float64)
    x_arr = x0 + (x1 - x0) * t_vals
    y_arr = y0 + (y1 - y0) * t_vals
    z_arr = z0 + (z1 - z0) * t_vals
    if curve == "strafe_dive":
        z_arr = z0 - (z0 - z1) * np.sin(t_vals * np.pi / 2)
    elif curve == "escape_climb":
        z_arr += 500 * np.sin(2 * np.pi * t_vals)
    elif curve == "dogfight_maneuver":
        x_arr += 400 * np.sin(4 * np.pi * t_vals)
        y_arr += 300 * np.cos(2 * np.pi * t_vals)
        z_arr += 200 * np.sin(3 * np.pi * t_vals)
    return x_arr, y_arr, z_arr

A_start = (0,6000,3000)
A_end = (6000,7500,2200)
numA = phases_info["Approach"][1]
xA,yA,zA = generate_path(A_start,A_end,numA)

B_start = A_end
B_end = (10000,7000,400)
numB = phases_info["Strafe"][1]
xB,yB,zB = generate_path(B_start,B_end,numB,"strafe_dive")

C_start = B_end
C_end = (15000,7500,1000)
numC = phases_info["Bombing"][1]
xC,yC,zC = generate_path(C_start,C_end,numC)

D_start = C_end
D_end = (7000,6000,4000)
numD = phases_info["Escape"][1]
xD,yD,zD = generate_path(D_start,D_end,numD,"escape_climb")

E_start = D_end
E_end = (5000,6500,3500)
numE = phases_info["Dogfight"][1]
xE,yE,zE = generate_path(E_start,E_end,numE,"dogfight_maneuver")

Victory_start = E_end
Victory_mid = (E_end[0]+2000, E_end[1], E_end[2]+1000)
Victory_end = A_start
numV1 = 80
xV1,yV1,zV1 = generate_path(Victory_start,Victory_mid,numV1,"escape_climb")
numV2 = 120
xV2,yV2,zV2 = generate_path(Victory_mid,Victory_end,numV2,"dogfight_maneuver")
xVictory = np.concatenate([xV1, xV2])
yVictory = np.concatenate([yV1, yV2])
zVictory = np.concatenate([zV1, zV2])
flight_x = np.concatenate([xA, xB, xC, xD, xE, xVictory])
flight_y = np.concatenate([yA, yB, yC, yD, yE, yVictory])
flight_z = np.concatenate([zA, zB, zC, zD, zE, zVictory])
frames_total = len(flight_x)
idxA_end = numA
idxB_end = idxA_end+numB
idxC_end = idxB_end+numC
idxD_end = idxC_end+numD
idxE_end = idxD_end+numE
phase_slices = {
    "Approach": (0,idxA_end),
    "Strafe": (idxA_end,idxB_end),
    "Bombing": (idxB_end,idxC_end),
    "Escape": (idxC_end,idxD_end),
    "Dogfight": (idxD_end,idxE_end)
}
phase_positions = {
    "Approach": (xA,yA,zA),
    "Strafe": (xB,yB,zB),
    "Bombing": (xC,yC,zC),
    "Escape": (xD,yD,zD),
    "Dogfight": (xE,yE,zE)
}
phase_quivers: Dict[str, Sequence[Line3DCollection]] = {pname:[] for pname in phase_positions}
arrow_len=400

def create_phase_quivers(ax: Axes3D, xarr: NDArray[np.float64], yarr: NDArray[np.float64], zarr: NDArray[np.float64], color: str) -> List[Line3DCollection]:
    quivs: List[Line3DCollection] = []
    interval=3
    for i in range(0,len(xarr)-1,interval):
        dx = xarr[i+1]-xarr[i]
        dy = yarr[i+1]-yarr[i]
        dz = zarr[i+1]-zarr[i]
        q: Line3DCollection = ax.quiver(
            xarr[i], yarr[i], zarr[i],
            dx, dy, dz,
            length=arrow_len, normalize=True,
            color=color, arrow_length_ratio=0.3
        )
        quivs.append(q)
    return quivs

fig = plt.figure(figsize=(20, 14))
ax_main: Axes3D = fig.add_subplot(111, projection='3d')
for pname,(col,num_pts) in phases_info.items():
    xP,yP,zP = phase_positions[pname]
    phase_quivers[pname] = create_phase_quivers(ax_main, xP,yP,zP, col)

def generate_terrain(xmin: int = 0, xmax: int = 18500, ymin: int = 4000, ymax: int = 9300, step: int = 300, amplitude: int = 600) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    x_vals = np.linspace(xmin, xmax, step)
    y_vals = np.linspace(ymin, ymax, step)
    x, y = np.meshgrid(x_vals, y_vals)
    np.random.seed(42)
    z = amplitude * 0.4 * np.sin(x / 1500) * np.cos(y / 1500)
    z += amplitude * 0.4 * np.random.rand(step, step)
    return x, y, z

fig = plt.figure(figsize=(20, 14))
ax_main: Axes3D = fig.add_subplot(111, projection='3d')
xmin, xmax = 0, 18500
ymin, ymax = 4000, 9300
step, amplitude = (100, 800)
ax_main.set_xlim(xmin, xmax)
ax_main.set_ylim(ymin, ymax)
ax_main.set_zlim(0, 15000)
ax_main.xaxis.pane.set_facecolor((0,0,0,0))
ax_main.yaxis.pane.set_facecolor((0,0,0,0))
ax_main.zaxis.pane.set_facecolor((0,0,0,0))
ax_main.xaxis.pane.set_edgecolor((0,0,0,0))
ax_main.yaxis.pane.set_edgecolor((0,0,0,0))
ax_main.zaxis.pane.set_edgecolor((0,0,0,0))
x_terr, y_terr, z_terr = generate_terrain()
ax_main.plot_surface(x_terr, y_terr, z_terr, cmap='terrain', alpha=0.2, edgecolor='none')
ax_main.set_title("F8F-1 Bearcat 3D (Approach->Strafe->Bomb->Escape->Dogfight)")
ax_main.set_xlabel("X (m)")
ax_main.set_ylabel("Y (m)")
ax_main.set_zlabel("Altitude (m)")
ax_main.set_xlim(0, 16000)
ax_main.set_ylim(5000, 9000)
ax_main.set_zlim(0, 5000)
ax_main.view_init(elev=30, azim=-60)
plt.tight_layout()

def create_aaa_geometry(cx: float, cy: float, cz: float, size_base: float = 100, height_base: float = 50, size_turret: float = 70, turret_angle_deg: float = 0) -> List[List[Tuple[float, float, float]]]:
    from math import cos, radians, sin
    angle_r = radians(turret_angle_deg)
    b=size_base/2
    base_bottom=cz
    base_top=cz+height_base
    base_verts = [
        (cx-b,cy-b,base_bottom),
        (cx+b,cy-b,base_bottom),
        (cx+b,cy+b,base_bottom),
        (cx-b,cy+b,base_bottom)
    ]
    base_verts_top=[
        (cx-b,cy-b,base_top),
        (cx+b,cy-b,base_top),
        (cx+b,cy+b,base_top),
        (cx-b,cy+b,base_top)
    ]
    base_faces = [
        [base_verts[0],base_verts[1],base_verts[2],base_verts[3]],
        [base_verts_top[0],base_verts_top[1],base_verts_top[2],base_verts_top[3]],
        [base_verts[0],base_verts[1],base_verts_top[1],base_verts_top[0]],
        [base_verts[1],base_verts[2],base_verts_top[2],base_verts_top[1]],
        [base_verts[2],base_verts[3],base_verts_top[3],base_verts_top[2]],
        [base_verts[3],base_verts[0],base_verts_top[0],base_verts_top[3]]
    ]
    turret_z_bottom = base_top
    turret_z_top = base_top + 30
    half_t = size_turret/2
    def rotX(x_, y_):
        dx_ = x_ - cx
        dy_ = y_ - cy
        xr_ = dx_*cos(angle_r) - dy_*sin(angle_r)
        yr_ = dx_*sin(angle_r) + dy_*cos(angle_r)
        return (cx + xr_, cy + yr_)
    t_verts_bot_raw = [
        (cx-half_t, cy-half_t, turret_z_bottom),
        (cx+half_t, cy-half_t, turret_z_bottom),
        (cx+half_t, cy+half_t, turret_z_bottom),
        (cx-half_t, cy+half_t, turret_z_bottom)
    ]
    turret_verts_bot: List[Tuple[float, float, float]] = []
    for (xx,yy,zz) in t_verts_bot_raw:
        rx, ry = rotX(xx,yy)
        turret_verts_bot.append((rx,ry,zz))
    t_verts_top_raw = [
        (cx-half_t, cy-half_t, turret_z_top),
        (cx+half_t, cy-half_t, turret_z_top),
        (cx+half_t, cy+half_t, turret_z_top),
        (cx-half_t, cy+half_t, turret_z_top)
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
        [turret_verts_bot[3],turret_verts_bot[0],turret_verts_top[0],turret_verts_top[3]]
    ]
    return base_faces + turret_faces

def ground_aaa_position(frame: int, center_x: float, center_y: float, radius: float = 600) -> Tuple[float, float, float]:
    t = (frame % 200) / 200.0
    angle = 2 * math.pi * t
    gx = center_x + radius * math.cos(angle)
    gy = center_y + radius * math.sin(angle)
    gz = 0
    return gx, gy, gz

bogie_x = np.full(frames_total, np.nan)
bogie_y = np.full(frames_total, np.nan)
bogie_z = np.full(frames_total, np.nan)
bogie_appear = idxD_end - 20
bx_start = 20000
by_start = 7500
bz_start = 500
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

explosion_active=False
explosion_frame=0
explosion_max_frames=30
explosion_poly=None
explosion_center=(0,0,0)

def spawn_explosion(center: Tuple[float, float, float]):
    global explosion_active, explosion_frame, explosion_center, explosion_poly
    explosion_active = True
    explosion_frame = 0
    explosion_center = center
    if explosion_poly:
        explosion_poly.remove()
        explosion_poly = None

parachute_poly = None
parachute_active = False
parachute_frame = 0
parachute_center = (0, 0, 0)

def spawn_parachute(center: Tuple[float, float, float]):
    global parachute_active, parachute_frame, parachute_center
    parachute_active = True
    parachute_frame = 0
    parachute_center = center

def create_bearcat_model(position: Tuple[float, float, float], direction: Tuple[float, float, float], scale: float = 80, color: str = 'red') -> Poly3DCollection:
    _, _, _ = position
    dx, dy, dz = direction
    mag = math.sqrt(dx*dx + dy*dy + dz*dz)
    if mag < 1e-6:
        dx, dy, dz = 1.0, 0.0, 0.0
        mag = 1.0
    dx /= mag
    dy /= mag
    dz /= mag
    scale_fac = scale
    nose = np.array([1.5, 0.0]) * scale_fac
    left_wing = np.array([0.0, -0.8]) * scale_fac
    right_wing = np.array([0.0, 0.8]) * scale_fac
    tail = np.array([-1.3, 0.0]) * scale_fac
    thickness = 0.15 * scale_fac
    top_pts: List[List[float]] = [
        [nose[0], nose[1], thickness],
        [right_wing[0], right_wing[1], thickness],
        [tail[0], tail[1], thickness],
        [left_wing[0], left_wing[1], thickness]
    ]
    bottom_pts: List[List[float]] = [
        [nose[0], nose[1], -thickness],
        [right_wing[0], right_wing[1], -thickness],
        [tail[0], tail[1], -thickness],
        [left_wing[0], left_wing[1], -thickness]
    ]
    faces: List[List[Tuple[float, float, float]]] = []
    faces.append([
        (top_pts[0][0], top_pts[0][1], top_pts[0][2]),
        (top_pts[1][0], top_pts[1][1], top_pts[1][2]),
        (top_pts[2][0], top_pts[2][1], top_pts[2][2]),
        (top_pts[3][0], top_pts[3][1], top_pts[3][2])
    ])
    faces.append([
        (bottom_pts[0][0], bottom_pts[0][1], bottom_pts[0][2]),
        (bottom_pts[1][0], bottom_pts[1][1], bottom_pts[1][2]),
        (bottom_pts[2][0], bottom_pts[2][1], bottom_pts[2][2]),
        (bottom_pts[3][0], bottom_pts[3][1], bottom_pts[3][2])
    ])
    for i in range(4):
        i2 = (i+1)%4
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
    R = np.vstack([forward, side, up]).T
    def transform_local(pt: Tuple[float, float, float]) -> NDArray[np.float64]:
        local = np.array(pt)
        return position + R.dot(local)
    face_world: List[List[Tuple[float, float, float]]] = []
    for f in faces:
        face_w: List[Tuple[float, float, float]] = []
        for v_ in f:
            face_w.append(tuple(transform_local(v_)))
        face_world.append(face_w)
    poly: Poly3DCollection = Poly3DCollection(face_world, facecolor=color, alpha=1.0)
    poly.set_edgecolor((0, 0, 0, 1))
    return poly

def clamp_xyz_arrays(x_: NDArray[np.float64], y_: NDArray[np.float64], z_: NDArray[np.float64]) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    min_len = min(len(x_), len(y_), len(z_))
    return (np.array(x_[:min_len], dtype=np.float64), np.array(y_[:min_len], dtype=np.float64), np.array(z_[:min_len], dtype=np.float64))

def simulate_bullet_trajectory(plane_pos: Tuple[float,float,float], plane_vel: Tuple[float,float,float], muzzle_speed: float = 1500.0, dt: float = 0.02, max_time: float = 0.1, gravity: float = 9.81) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    px, py, pz = plane_pos
    vx_p, vy_p, vz_p = plane_vel
    speed_plane = math.hypot(vx_p, vy_p, vz_p)
    if speed_plane < 1e-6:
        direction = (1.0, 0.0, 0.0)
    else:
        direction = (vx_p/speed_plane, vy_p/speed_plane, vz_p/speed_plane)
    bullet_speed = speed_plane + muzzle_speed
    vx_ = bullet_speed * direction[0]
    vy_ = bullet_speed * direction[1]
    vz_ = bullet_speed * direction[2]
    bx: List[float] = [px]
    by: List[float] = [py]
    bz: List[float] = [pz]
    t = 0.0
    while t < max_time:
        xnew = bx[-1] + vx_ * dt
        ynew = by[-1] + vy_ * dt
        znew = bz[-1] + vz_ * dt
        vz_ -= gravity * dt
        if znew <= 0.0:
            znew = 0.0
            bx.append(xnew)
            by.append(ynew)
            bz.append(znew)
            break
        bx.append(xnew)
        by.append(ynew)
        bz.append(znew)
        t += dt
    return clamp_xyz_arrays(np.array(bx), np.array(by), np.array(bz))

def spawn_bullets(px: float, py: float, pz: float, vx: float, vy: float, vz: float, frame: int, muzzle_speed: float = 3000.0, num_bullets: int = 5) -> None:
    for _ in range(num_bullets):
        bx_, by_, bz_ = simulate_bullet_trajectory((px,py,pz), (vx,vy,vz), muzzle_speed=muzzle_speed)
        bullet: Dict[str, Any] = {
            'x': bx_,
            'y': by_,
            'z': bz_,
            'index': 0,
            'line': None
        }
        active_bullets.append(bullet)

def simulate_rocket_trajectory(plane_pos: Tuple[float,float,float], plane_vel: Tuple[float,float,float], rocket_speed: float = 1000.0, dt: float = 0.05, max_time: float = 1.5, thrust_dur: float = 3.0) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    px, py, pz = plane_pos
    vx_p, vy_p, vz_p = plane_vel
    speed_plane = math.hypot(vx_p, vy_p, vz_p)
    if speed_plane < 1e-6:
        direction = (1.0, 0.0, 0.0)
    else:
        direction = (vx_p/speed_plane, vy_p/speed_plane, vz_p/speed_plane)
    vx_r = speed_plane + rocket_speed
    vx_vec = [vx_r*direction[0], vx_r*direction[1], vx_r*direction[2]]
    rx: List[float] = [px]
    ry: List[float] = [py]
    rz: List[float] = [pz]
    t = 0.0
    g = 9.81
    while t < max_time:
        if t < thrust_dur:
            vx_vec[0] += 5.0 * dt * direction[0]
            vx_vec[1] += 5.0 * dt * direction[1]
            vx_vec[2] += 5.0 * dt * direction[2]
        vx_, vy_, vz_ = vx_vec
        vx_vec[2] -= g * dt
        xnew = rx[-1] + vx_ * dt
        ynew = ry[-1] + vy_ * dt
        znew = rz[-1] + vz_ * dt
        if znew <= 0.0:
            znew = 0.0
            rx.append(xnew)
            ry.append(ynew)
            rz.append(znew)
            break
        rx.append(xnew)
        ry.append(ynew)
        rz.append(znew)
        t += dt
    return clamp_xyz_arrays(np.array(rx), np.array(ry), np.array(rz))

def spawn_rocket(px: float, py: float, pz: float, vx: float, vy: float, vz: float) -> None:
    rx_, ry_, rz_ = simulate_rocket_trajectory((px,py,pz), (vx,vy,vz))
    rocket: Dict[str, Any] = {
        'x': rx_,
        'y': ry_,
        'z': rz_,
        'index': 0,
        'line': None
    }
    active_rockets.append(rocket)

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

def simulate_bomb_trajectory(xi: float, yi: float, zi: float, vx_i: float, vy_i: float, vz_i: float, dt: float = 0.03, drag: float = 0.00025, max_time: float = 50) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    g=9.81*0.75
    bx = [xi]
    by = [yi]
    bz = [zi]
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
            bx.append(xnew)
            by.append(ynew)
            bz.append(znew)
            break
        bx.append(xnew)
        by.append(ynew)
        bz.append(znew)
        t+=dt
    bx_,by_,bz_=clamp_xyz_arrays(np.array(bx, dtype=np.float64), np.array(by, dtype=np.float64), np.array(bz, dtype=np.float64))
    return bx_,by_,bz_

bomb_x, bomb_y, bomb_z = map(np.array, simulate_bomb_trajectory(bomb_init_x, bomb_init_y, bomb_init_z, vx_plane, vy_plane, vz_plane))
bomb_marker=None
bomb_explosion_triggered=False

def update_explosion() -> None:
    global explosion_active, explosion_frame, explosion_poly
    if not explosion_active:
        return
    if explosion_poly:
        explosion_poly.remove()
        explosion_poly = None
    frac = explosion_frame / float(explosion_max_frames)
    radius = 10 + 80 * frac
    th, ph = np.mgrid[0:np.pi:15j, 0:2*np.pi:15j]
    xs: NDArray[np.float64] = radius * np.sin(th) * np.cos(ph) + explosion_center[0]
    ys: NDArray[np.float64] = radius * np.sin(th) * np.sin(ph) + explosion_center[1]
    zs: NDArray[np.float64] = radius * np.cos(th) + explosion_center[2]
    explosion_poly = ax_main.plot_surface(xs, ys, zs, color='orange', alpha=1.0, edgecolor='red')
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
    t = parachute_frame
    dx = parachute_center[0] + 10 * math.sin(0.1 * t)
    dy = parachute_center[1] + 10 * math.cos(0.1 * t)
    dz = parachute_center[2] - 3 * t
    if dz < 0:
        dz = 0
    size = 50
    half = size / 2
    corners = [
        (dx - half, dy - half, dz + 20),
        (dx + half, dy - half, dz + 20),
        (dx + half, dy + half, dz + 20),
        (dx - half, dy + half, dz + 20)
    ]
    faces = [[corners[0], corners[1], corners[2], corners[3]]]
    p = Poly3DCollection(faces, facecolors='white', alpha=0.8)
    p.set_edgecolor('black')
    ax_main.add_collection3d(p)
    parachute_poly = p
    parachute_frame += 1
    if dz <= 0:
        parachute_active = False
        if parachute_poly:
            parachute_poly.remove()
            parachute_poly = None

bearcat_poly: Optional[Poly3DCollection] = None
bogie_poly: Optional[Poly3DCollection] = None
lockon_line: Optional[Line2D] = None
lockon_line_radius = 300.0
lockon_line_shrink = 3.0
target_destroyed_text: Optional[Text] = None
bogie_is_hit = False
bogie_hit_frame = 0

def init_animation() -> tuple[()]:
    return ()

def update_animation(frame: int) -> tuple[()]:
    global bearcat_poly, bogie_poly, bomb_marker, bomb_explosion_triggered, bogie_is_hit, bogie_hit_frame, lockon_line, lockon_line_radius, target_destroyed_text
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
        bearcat_poly=create_bearcat_model((bcx,bcy,bcz),(vx_bc,vy_bc,vz_bc),80,'white')
        ax_main.add_collection3d(bearcat_poly)
    if bomb_marker is not None:
        bomb_marker.remove()
        bomb_marker = None
    bomb_frame_i = frame - bomb_drop_frame
    if bomb_frame_i >= 0:
        if bomb_frame_i < len(bomb_x):
            bx_ = bomb_x[bomb_frame_i]
            by_ = bomb_y[bomb_frame_i]
            bz_ = bomb_z[bomb_frame_i]
            alt = bz_
            blink_rate = 20.0 - 0.02 * alt
            if blink_rate < 2:
                blink_rate = 2
            bomb_blink_on = ((frame // int(blink_rate)) % 2 == 0)
            if alt > 0 and bomb_blink_on:
                bomb_marker = ax_main.scatter([bx_], [by_], bz_, color='red', s=50, marker='o')
            if alt <= 0 and not bomb_explosion_triggered:
                bomb_explosion_triggered = True
                spawn_explosion((bx_, by_, 0))
    if bogie_poly is not None:
        bogie_poly.remove()
    if frame<frames_total and not np.isnan(bogie_x[frame]):
        if bogie_is_hit:
            if bogie_hit_frame is not None:
                n = int(frame) - int(bogie_hit_frame)
            else:
                n = 0
            if n < 0:
                n = 0
            oldx = bogie_x[bogie_hit_frame] if bogie_hit_frame is not None else 0.0
            oldy = float(bogie_y[bogie_hit_frame])
            oldz = float(bogie_z[bogie_hit_frame])
            angle = 0.4 * n
            rad = 50 + 5 * n
            bxx = oldx + rad * math.cos(angle)
            byy = oldy + rad * math.sin(angle)
            bzz = oldz - 30 * n
            if bzz < 0:
                bzz = 0
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
        bogie_poly=create_bearcat_model((btx,bty,btz),(vx_bog,vy_bog,vz_bog),100,'red')
        ax_main.add_collection3d(bogie_poly)
    strafe_s, strafe_e = phase_slices["Strafe"]
    if lockon_line is not None:
        lockon_line.remove()
        lockon_line = None
    if strafe_s <= frame < strafe_e:
        if lockon_line_radius > 0:
            angles = np.linspace(0, 2 * math.pi, 36, dtype=np.float64)
            center_ = (10000, 7000, 0)
            xs = center_[0] + lockon_line_radius * np.cos(angles)
            zs = np.full_like(xs, center_[2] + 10)
            ys = center_[1] + lockon_line_radius * np.sin(angles)
            lockon_line, = ax_main.plot(xs, ys, zs, color='red', linewidth=1)
            lockon_line_radius -= lockon_line_shrink
            if lockon_line_radius < 0:
                lockon_line_radius = 0
    else:
        lockon_line_radius=300
    if target_destroyed_text is not None:
        target_destroyed_text.remove()
        target_destroyed_text = None
    if frame == strafe_e:
        if target_destroyed_text is None:
            target_destroyed_text = ax_main.text(10000, 7000, 100, "Target Destroyed", color='red', fontsize=12)
        else:
            target_destroyed_text.remove()
            target_destroyed_text = None
    if strafe_s<=frame<strafe_e:
        if frame%15==0 and frame>0:
            px=flight_x[frame]
            py=flight_y[frame]
            pz=flight_z[frame]
            vx_=flight_x[frame]-flight_x[frame-1]
            vy_=flight_y[frame]-flight_y[frame-1]
            vz_=flight_z[frame]-flight_z[frame-1]
            spawn_bullets(px,py,pz,vx_,vy_,vz_,frame,3000.0,5)
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
    dog_s,dog_e=phase_slices["Dogfight"]
    if dog_s<=frame<dog_e:
        if frame%15==0 and frame>0:
            px=flight_x[frame]
            py=flight_y[frame]
            pz=flight_z[frame]
            vx_=flight_x[frame]-flight_x[frame-1]
            vy_=flight_y[frame]-flight_y[frame-1]
            vz_=flight_z[frame]-flight_z[frame-1]
            spawn_bullets(px,py,pz,vx_,vy_,vz_,frame,3000.0,5)
        if frame%15==0 and frame>0 and not bogie_is_hit:
            bx_=bogie_x[frame]
            by_=bogie_y[frame]
            bz_=bogie_z[frame]
            if not np.isnan(bx_):
                vx_=bogie_x[frame]-bogie_x[frame-1]
                vy_=bogie_y[frame]-bogie_y[frame-1]
                vz_=bogie_z[frame]-bogie_z[frame-1]
                spawn_bullets(bx_,by_,bz_,vx_,vy_,vz_,frame,10000,5)
        half_dog=dog_s+(dog_e-dog_s)//2
        if frame==half_dog and not bogie_is_hit:
            bogie_is_hit=True
            bogie_hit_frame=frame
    done_bul: List[dict[str, Any]] = []
    for bullet in active_bullets:
        if bullet in done_bul:
            continue
        idx = bullet['index']
        bx_arr = bullet['x']
        by_arr = bullet['y']
        max_len = len(bx_arr)
        if idx < max_len:
            bullet['index'] += 1
            i = bullet['index']
            if i > max_len:
                i = max_len
            if bullet['line'] is None:
                line_ = ax_main.plot([], [], [], color='yellow', linewidth=1)[0]
                bullet['line'] = line_
            bullet['line'].set_data(bx_arr[:i], by_arr[:i])
        else:
            if bullet['line'] is not None:
                bullet['line'].remove()
            bullet['line'] = None
    done_roc: List[dict[str, Any]] = []
    for rocket in active_rockets:
        if rocket in done_roc:
            continue
        idx = rocket['index']
        rx_arr = rocket['x']
        ry_arr = rocket['y']
        max_len = len(rx_arr)
        if idx < max_len:
            rocket['index'] += 1
            i = rocket['index']
            if i > max_len:
                i = max_len
            if rocket['line'] is None:
                rline = ax_main.plot([], [], [], color='white', linewidth=1)[0]
                rocket['line'] = rline
            rocket['line'].set_data(rx_arr[:i], ry_arr[:i])
        else:
            if rocket['line'] is not None:
                rocket['line'].remove()
            rocket['line'] = None
    if frame == (idxC_end + 5) and not bomb_explosion_triggered and len(bomb_x) > 0:
        bomb_explosion_triggered = True
        spawn_explosion((bomb_x[-1], bomb_y[-1], 0))
    update_explosion()
    for c_ in ax_main.collections[:]:
        if getattr(c_,'_aaa_flag',False):
            c_.remove()
    gx1,gy1,gz1=ground_aaa_position(frame,10000,7000,700)
    if frame<frames_total:
        ax_ = flight_x[frame]-gx1
        ay_ = flight_y[frame]-gy1
        angle_aaa = math.degrees(math.atan2(ay_,ax_))
    else:
        angle_aaa=0
    faces1 = create_aaa_geometry(gx1,gy1,gz1,120,50,70,angle_aaa)
    col1=Poly3DCollection(faces1,facecolor='brown',alpha=0.9)
    col1.set_edgecolor('white')
    col1._aaa_flag=True
    ax_main.add_collection3d(col1)
    gx2,gy2,gz2=ground_aaa_position(frame+30,15000,7500,900)
    if frame<frames_total:
        ax2_ = flight_x[frame]-gx2
        ay2_ = flight_y[frame]-gy2
        angle_aaa2=math.degrees(math.atan2(ay2_,ax2_))
    else:
        angle_aaa2=0
    faces2 = create_aaa_geometry(gx2,gy2,gz2,150,60,80,angle_aaa2)
    col2=Poly3DCollection(faces2,facecolor='black',alpha=0.9)
    col2.set_edgecolor('white')
    col2._aaa_flag=True
    ax_main.add_collection3d(col2)
    update_parachute()
    return ()

anim = FuncAnimation(fig, update_animation, init_func=init_animation, frames=frames_total, interval=80, blit=False, repeat=True)
plt.show()
