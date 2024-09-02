# Create a sample output that looks as if CommandPE might have created it,
#  with a matching input file for ROMANCER's CommandPE target-weapon-value pairings file
import csv
import heapq
import math
import os
from random import Random

# Approximate Timeline:
#  1. T=0, An adversary begins targeting early warning radars along west US coast with cruise missiles
#  2. Initially, only lower-value targets are targeted, using lower-value weapons,
#       until separate embargoes for each [targets, weapons] ends
#  3. A period of quiescence during which no shots are fired [missiles in-air may still arrive]
#  4. Embargo on shooting at high value targets ends
#  5. Embargo on shooting high yield weapons ends
#  6. Period of exclusively targeting high value targets
# Extra notes:
#   The early warning radars targeted are locations from the now-retired SAGE early warning system.
#   Target "values" are approximated by their proximity to the main "high-value" target
#   Many liberties are taken with this narrative - it is for use as an example only

# Don't hit HVTs until this time
embargo_hvt_s = 90 * 60
# Don't use high yield weapons until this time
embargo_weapon_yield_s = 190 * 60
# Exclusively attach HVTs from here on
hvt_exclusive_s = 260 * 60
# Wait this long between shots, on average
avg_fire_time_s = 10 * 60
# Stop firing at this time
quiesce_start_s = 120 * 60
# Do not fire for this long
quiesce_duration_s = 40 * 60
# Scenario ends at this time
scenario_end_time = 360 * 60

# Convert meters per second to knots
m_s_to_kts = 1.943844

# Convert meters to nm
m_to_nm = 0.000539957

# Target file data read
target_file = "targets.csv"
# Create the ROMANCER-CPEReader input file automatically
target_input_file = "targetClass.csv"
target_unit_input_file = "targetUnitClass.csv"

# For convenience, all targets will have the same "type"
target_typename = "TARGET"

# Weapon file
weapon_file = "weapons.csv"
# Create the ROMANCER-CPEReader input files automatically
weapon_input_file = "weaponClass.csv"

# Shooter Location
shooter_lat = 35.5
shooter_lon = -130.3
shooter_name = "SSGN"
shooter_type = "SSGN"
shooter_platform_index = 1

shooter_side = "BLUE"
target_side = "RED"

# All weapons are cruise missiles and fly at approx same speed
wpn_speed_m_s = 250

# First and second line of headers
weaponfired_headers1 = [
    "TimelineID",
    "Time",
    "FiringUnitID",
    "FiringUnitDBID",
    "FiringUnitName",
    "FiringUnitType",
    "FiringUnitClass",
    "FiringUnitSide",
    "FiringUnitLongitude",
    "FiringUnitLatitude",
    "FiringUnitCourse",
    "FiringUnitSpeed_kts",
    "FiringUnitAltitude_m",
    "FiringUnitAGL_m",
    "WeaponID",
    "WeaponDBID",
    "WeaponName",
    "WeaponType",
    "WeaponClass",
    "TargetContactID",
    "TargetContactLongitude",
    "TargetContactLatitude",
    "TargetContactHeading",
    "TargetContactSpeed",
    "TargetContactAltitude",
    "TargetContactRangeHoriz_nm",
    "TargetContactRangeSlant_nm",
    "TargetContactActualUnitID",
    "TargetContactActualUnitName",
    "TargetContactActualUnitClass",
    "TargetContactActualUnitSide",
    "SalvoID",
    "CountermeasuresRemaining"]

weaponfired_headers2 = [
    "The unique ID of the simulation run under which the event occured",
    "The scenario time at which the event occured",
    "FiringUnitID",
    "FiringUnitDBID",
    "FiringUnitName",
    "FiringUnitType",
    "FiringUnitClass",
    "FiringUnitSide",
    "The longitude of The firing unit",
    "The latitude of the firing unit",
    "The firing unit's course (heading) in degrees",
    "The firing unit's speed (true airspeed in the case of aircraft) in knots",
    "\"The firing unit's barometric (above mean surface level) altitude in meters\"",
    "\"The firing unit's actual above-ground altitude in meters\"",
    "The unique ID of the weapon being fired",
    "The database ID of the weapon being fired",
    "The actual name of the weapon being fired",
    "The type-description string (e.g. 'Guided Weapon') of the weapon being fired",
    "\"The unit-class description (e.g. 'AGM-154C-1 JSOW 2012') of the weapon being fired\"",
    "The unique ID of The contact being fired upon",
    "The current / last-known longitude of the contact being fired upon",
    "The current / last-known latitude of the contact being fired upon",
    "The current / last-known heading of the contact being fired upon",
    "The current / last-known speed of the contact being fired upon",
    "The current / last-known barometric altitude of the contact being fired upon",
    "\"The horizontal range from the firing unit to the engaged contact's last known location in nautical miles\"",
    "\"The slant range from the firing unit to the engaged contact's last known location in nautical miles\"",
    "The unique ID of the actual unit correlated with the engaged contact",
    "The actual name of The unit correlated with The engaged contact",
    "The unit-class description of the unit correlated with the engaged contact",
    "The name of the side to which the unit correlated with the engaged contact belongs",
    "SalvoID",
    "CountermeasuresRemaining"
]

weaponendgame_headers1 = [
    "TimelineID",
    "Time",
    "WeaponID",
    "WeaponName",
    "WeaponSide",
    "ParentFiringUnitID",
    "ParentFiringUnitName",
    "TargetID",
    "TargetName",
    "TargetSide",
    "TargetLongitude",
    "TargetLatitude",
    "TargetAltitude_ASL_m",
    "TargetAltitude_AGL_m",
    "DistanceFromFiringUnit_Horiz",
    "Result",
    "EndgameMessage "
]

weaponendgame_headers2 = [
    "The unique ID of the simulation run under which the event occured",
    "The scenario time at which the event occured",
    "WeaponID",
    "WeaponName",
    "WeaponSide",
    "The unique ID of the unit that fired the weapon",
    "The actual name of the unit that fired the weapon",
    "The unique ID of the target unit at which the weapon is attacking",
    "The actual name of the target unit which the weapon is attacking",
    "The name of the side to which the attacked unit belongs",
    "The longitude of the target unit",
    "The latitude of the target unit",
    "\"The barometric (above mean surface level) altitude of the attacked unit in meters\"",
    "\"The actual above-ground altitude in meters of the attacked unit\"",
    "\"The horizontal range from the weapon's firing unit to the endgame location in nautical miles\"",
    "\"The result of the endgame sequence: Direct hit miss or defeated by point defences\"",
    "The generated logged message that describes the endgame sequence"
]

# Approximate distance between pairs of points on earths surface, in m
def haversine_m(lat1_dd, lon1_dd, lat2_dd, lon2_dd):
    d2r = math.pi/180
    R = 6371 * 1000.0 # Earth radius in meters
    lat1 = lat1_dd * d2r
    lat2 = lat2_dd * d2r
    lon1 = lon1_dd * d2r
    lon2 = lon2_dd * d2r
    dLon = lon2 - lon1
    dLat = lat2 - lat1
    a = math.sin(dLat/2.0)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dLon/2.0)**2
    c = 2.0 * math.asin(math.sqrt(a))
    return R * c

def time_to_hms(t_s):
    t_s_int = math.floor(t_s)
    h = t_s_int // 3600
    m = (t_s_int % 3600) // 60
    s = t_s_int % 60
    return f"{h}:{m:02}:{s:02}"

if __name__ == "__main__":
    output_folder = "commandpe_output"
    input_folder = "commandpe_input"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    if not os.path.exists(input_folder):
        os.makedirs(input_folder)

    rng = Random()

    # Parse weapon CSV input file
    with open(weapon_file, "r") as wpn_file:
        csv_reader = csv.DictReader(wpn_file)
        wpn_list = {}
        for row in csv_reader:
            wpn_list[row['Name']] = { "Name" : row['Name'],
                              "WeaponValue" : int(row['WeaponValue']),
                              "SSPK" : float(row['SSPK']) }
    # Create ROMANCER CPE Reader input file for weapon classification
    with open(os.path.join(input_folder, weapon_input_file), "w") as f:
        f.write("WeaponClass,WeaponCategory\n")
        for wpn in wpn_list.values():
            f.write(f"{wpn['Name']},{wpn['WeaponValue']}\n")

    global_unique_id = 10 # Manufacture  global ids

    # Parse target CSV input file
    with open(target_file, "r") as tgt_file:
        csv_reader = csv.DictReader(tgt_file)
        tgt_list = {}
        # There are some columns in this file that we don't need, filter to just what's wanted
        for row in csv_reader:
            filtered_row = { "Name" : row['Name'],
                             "Lat" : float(row['Lat']),
                             "Lon" : float(row['Lon']),
                             "TargetValue" : int(row['TargetValue']) }
            tgt_list[row['Name']] = filtered_row
        # Give indices to targets
        for tgt in tgt_list.values():
            tgt['idx'] = global_unique_id
            global_unique_id += 1

    # Create ROMANCER CPE Reader input file for target classification
    with open(os.path.join(input_folder, target_input_file), "w") as f:
        f.write("TargetClass,TargetCategory\n")
        f.write(f"{target_typename},3\n")
    # Create ROMANCER CPE Reader input file for target classification by specific unit
    with open(os.path.join(input_folder, target_unit_input_file), "w") as f:
        f.write("TargetUnit,TargetCategory\n")
        for tgt in tgt_list.values():
            f.write(f"{tgt['Name']},{tgt['TargetValue']}\n")

    with (open(os.path.join(output_folder, "WeaponFired.csv"), "w") as f_fired,
          open(os.path.join(output_folder, "WeaponEndgame.csv"), "w") as f_endgame):
        f_fired.write(",".join(weaponfired_headers1) + "\n")
        f_fired.write(",".join(weaponfired_headers2) + "\n")

        f_endgame.write(",".join(weaponendgame_headers1) + "\n")
        f_endgame.write(",".join(weaponendgame_headers2) + "\n")

        # As weapons are fired, they go into this queue, for popping off at the moment they arrive
        weapon_arrival_queue = []

        # Main Loop. Time moves forward
        t_now = 0.0
        while t_now < scenario_end_time:
            t_now += avg_fire_time_s + rng.uniform(-60.0, 60.0)

            # Deal with weapons that have arrived
            while len(weapon_arrival_queue)>0 and weapon_arrival_queue[0][0] < t_now:
                event = heapq.heappop(weapon_arrival_queue)
                t_arrival = event[0]
                wpn = event[1]
                tgt = event[2]
                wpn_idx = event[3]
                track_idx = event[4]
                print(f"Boom @ T={t_arrival:.2f}, {wpn['Name']} hit {tgt['Name']}")

                if tgt['Name'] not in tgt_list:
                    # Already killed while missile was in-flight. Ignore for now
                    continue

                is_kill = (rng.uniform(0.0, 1.0) < wpn['SSPK'])

                msg = f"Wpn {wpn['Name']} hit {tgt['Name']}. Kill: {is_kill}"

                line = [
                    42,
                    time_to_hms(t_arrival),
                    # Shooter
                    wpn_idx,
                    wpn['Name'],
                    shooter_side,
                    shooter_platform_index,
                    shooter_name,
                    # Target
                    tgt['idx'],
                    tgt['Name'],
                    target_side,
                    tgt['Lon'],
                    tgt['Lat'],
                    1, # Altitude
                    1,
                    m_to_nm * haversine_m(shooter_lat, shooter_lon, tgt['Lat'], tgt['Lon']),
                    "HIT" if is_kill else "MISS",
                    msg
                ]
                f_endgame.write(",".join(str(el) for el in line) + "\n")



            if quiesce_start_s < t_now < quiesce_start_s + quiesce_duration_s:
                print(f"T={t_now:.2f}, Shooting Paused")
                continue

            viable_tgts = [tgt_list[tgt] for tgt in tgt_list if
                           (t_now < hvt_exclusive_s and tgt_list[tgt]["TargetValue"] < 5)
                             or (t_now >= hvt_exclusive_s and tgt_list[tgt]["TargetValue"] >= 5)]
            viable_wpns = [wpn_list[wpn] for wpn in wpn_list if t_now > embargo_weapon_yield_s or wpn_list[wpn]["WeaponValue"] < 4]
            if 0 == len(viable_tgts) or 0 == len(viable_wpns):
                continue

            chosen_wpn = rng.choice(viable_wpns)
            chosen_tgt = rng.choice(viable_tgts)
            # Asign some IDs
            weapon_id = global_unique_id
            global_unique_id += 1
            track_id = global_unique_id
            global_unique_id += 1

            # Plan for weapon arrival
            flight_dist_m = haversine_m(shooter_lat, shooter_lon, chosen_tgt["Lat"], chosen_tgt["Lon"])
            flight_time_s = flight_dist_m / wpn_speed_m_s
            heapq.heappush(weapon_arrival_queue, (t_now + flight_time_s, chosen_wpn, chosen_tgt, weapon_id, track_id))

            print(f"T={t_now}, Firing {chosen_wpn['Name']} at {chosen_tgt['Name']}, flight time {flight_time_s:.2f}s")
            line = [
                42, # Simulation ID
                time_to_hms(t_now),

                # Shooter information
                shooter_platform_index,
                shooter_platform_index,
                shooter_name,
                shooter_type,
                shooter_type,
                shooter_side,
                shooter_lon,
                shooter_lat,
                90.0, # Heading due East
                0.0, # Speed=0
                0.0, # SSGN is at sea level
                0.0,  # SSGN is at sea level

                # Weapon Information
                weapon_id,
                weapon_id,
                chosen_wpn['Name'],
                chosen_wpn['Name'],
                chosen_wpn['Name'],

                # Track information
                chosen_tgt['idx'],
                chosen_tgt['Lon'],
                chosen_tgt['Lat'],
                0.0, # Heading nowhere
                0.0, # Not moving
                1.0, # 1m off ground
                flight_dist_m * m_to_nm, # Ground range
                flight_dist_m * m_to_nm, # Slant range - same as ground range, approx

                # Target information
                chosen_tgt['idx'],
                chosen_tgt['Name'],
                target_typename,
                target_side,
                1, # Salvo
                0 # Countermeasures remaining
            ]
            f_fired.write(",".join(str(el) for el in line) + "\n")


