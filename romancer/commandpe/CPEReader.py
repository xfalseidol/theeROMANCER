from datetime import datetime
import csv


class CPEWeaponFiredReader:
    ''' A class for reading outputs from CommandPE '''

    # Returns target_category => { weapon_category => count }
    def __init__(self, weapon_class_csv, target_class_csv, target_unit_csv, weapon_fired_csv, shooter_side='BLUE'):
        self.shooterSide = shooter_side
        ''' Weapon Class is a configuration file mapping Weapon Class [from Command PE] to a Consideration-Level'''
        self.weapon_scale = self.load_weapon_scale(weapon_class_csv)
        ''' Target Class is two configuration files mapping targets to Consideration-level'''
        ''' The "Target Unit" file is so that specific units can be assigned specific consideration levels and takes priority'''
        ''' The "Target Class" file is so that targets can be assigned specific consideration levels by their type'''
        self.target_scale, self.target_unit_scale = self.load_target_scale(target_class_csv, target_unit_csv)

        print("Loaded Scaling Maps for Weapons and Targets:")
        print(f"Weapon Category: {len(self.weapon_scale)} items, Target Category: {len(self.target_scale)} items, Target Unit Category: {len(self.target_unit_scale)} items")

        weaponfired_f = open(weapon_fired_csv, "r")
        self.weaponfired_reader = csv.DictReader(weaponfired_f)
        # First row is comments. Ignore it
        next(self.weaponfired_reader)
        # Because this is a stateful API, we'll start off with the first one
        self.last_weapon_fired_record = next(self.weaponfired_reader)
        self.curr_time_s = 0

        self.scenario_complete = False
        self.records_read = 0

    def load_target_scale(self, target_class_csv, target_unit_csv):
        target_scale = {}
        with open(target_class_csv, "r") as f:
            csv_reader = csv.DictReader(f)
            target_scale = {row['TargetClass']: row['TargetCategory'] for row in csv_reader}

        target_unit = {}
        with open(target_unit_csv, "r") as f:
            csv_reader = csv.DictReader(f)
            target_unit = {row['TargetUnit']: row['TargetCategory'] for row in csv_reader}

        return target_scale, target_unit

    def load_weapon_scale(self, weapon_class_csv):
        weapon_scale = {}
        with open(weapon_class_csv, "r") as f:
            csv_reader = csv.DictReader(f)
            weapon_scale = {row['WeaponClass']: row['WeaponCategory'] for row in csv_reader}

        return weapon_scale

    def get_time_s(self, t_str):
        ''' Accept a timestamp in CommandPE's format, return t_s '''
        # For simplicity, ignore sub-second component of time
        #   Decision may need revisiting once AI is in charge of Nuclear decision-making
        timefmt = "%H:%M:%S"
        time_obj = datetime.strptime(t_str.split(".")[0], timefmt)
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

    def get_current_time_s(self):
        return self.curr_time_s

    def get_records_read(self):
        return self.records_read

    def is_scenario_complete(self):
        ''' Return true if the scenario is "complete" [ie, ran out of inputs] '''
        return self.scenario_complete

    def read_next_weapons_fired(self, timeframe_s=(15*60)):
        ''' Get a map of { weaponscale => n_weapons_fired } during the next timeframe_s seconds from last time this returned '''
        if self.scenario_complete:
            return {}

        t_end = self.curr_time_s + timeframe_s
        retval = {}
        time_last_weapon_fired_s = self.get_time_s(self.last_weapon_fired_record['Time'])

        while time_last_weapon_fired_s < t_end:
            self.records_read += 1

            wpn_class = self.last_weapon_fired_record['WeaponClass']
            this_wpn_scale = self.weapon_scale.get(wpn_class)

            firing_side = self.last_weapon_fired_record['FiringUnitSide']

            target_name = self.last_weapon_fired_record['TargetContactActualUnitName']
            target_class = self.last_weapon_fired_record['TargetContactActualUnitClass']
            this_target_scale = self.target_unit_scale[target_name] if target_name in self.target_unit_scale else self.target_scale.get(target_class)

            if firing_side == self.shooterSide:
                if this_target_scale is None:
                    print(f"Couldn't find a target scaling lookup for class '{target_class}' or unit name '{target_name}'")
                elif this_wpn_scale is None:
                    print(f"Couldn't find a weapon scaling lookup for class '{wpn_class}'")
                else:
                    retval[this_wpn_scale] = retval.get(this_wpn_scale, 0) + 1

            time_last_weapon_fired_str = self.last_weapon_fired_record['Time']
            try:
                self.last_weapon_fired_record = next(self.weaponfired_reader)
                time_last_weapon_fired_s = self.get_time_s(time_last_weapon_fired_str)
            except StopIteration:
                self.scenario_complete = True
                break

        self.curr_time_s = t_end
        return retval


if __name__ == "__main__":
    cpeoutputfolder = "data/commandpe_output"
    cpeinputfolder = "data/commandpe_input"
    cper = CPEWeaponFiredReader(f"{cpeinputfolder}/weaponClass.csv", f"{cpeinputfolder}/targetClass.csv",
                                f"{cpeinputfolder}/targetUnitClass.csv",
                                f"{cpeoutputfolder}/WeaponFired.csv", 'BLUE')
    while not cper.is_scenario_complete():
        print(cper.read_next_weapons_fired(5 * 60))
        print(f"Time is: {cper.get_current_time_s()}, total wpns fired = {cper.get_records_read()}")

