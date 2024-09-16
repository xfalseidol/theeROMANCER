from casebasedreasoner.cbr import CaseBasedReasoner, MOPComparerSorter, MOP
from dill import dump, load
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import copy

from romancer.environment.object import LoggedDict


class ELRPerceptMOPComparer(MOPComparerSorter):
    def __init__(self, keycols=None, valcols=None):
        if keycols is None:
            keycols = ["weapon", "target"]
        if valcols is None:
            valcols = ["count"]
        self.keycols = keycols
        self.valcols = valcols

    def compare_mops_and_sort(self, cbr, mop_name, compare_mop_names, visual=False):
        pivot_percepts = self.get_percept_list(cbr, mop_name)
        pivot_percepts.sort(key=lambda x: (x['weapon'], x['target']))
        compare_percepts = { comp_mopname : self.get_percept_list(cbr, comp_mopname) for comp_mopname in compare_mop_names }
        distances = { comp_mopname : self.compare_two_percept_lists(pivot_percepts, compare_percepts[comp_mopname]) for comp_mopname in compare_mop_names }
        sorted_mopnames = sorted(distances, key=lambda k: distances[k])
        if visual:
            print("For mop " + mop_name + " " + str(pivot_percepts))
            self.visualise(pivot_percepts, compare_percepts, sorted_mopnames, 20)
            reverse_mopnames = sorted(distances, key=lambda k: distances[k], reverse=True)
            self.visualise(pivot_percepts, compare_percepts, reverse_mopnames, 20, "rev")
            for i in range(min(len(sorted_mopnames), 10)):
                these_percepts = compare_percepts[sorted_mopnames[i]]
                these_percepts.sort(key=lambda x: (x['weapon'], x['target']))
                print(f"#{i}: {sorted_mopnames[i]} = {distances[sorted_mopnames[i]]} - {these_percepts}")
        return sorted_mopnames

    # Return a map of sorted lists, of the possible values for each key
    def get_possible_keys(self, compare_percepts):
        retval = { k : [] for k in self.keycols }
        for percepts in compare_percepts.values():
            for p in percepts:
                for k in self.keycols:
                    retval[k].append(p[k]) if p[k] not in retval[k] else None
        for lst in retval.values():
            lst.sort()
        return retval

    def create_heatmap(self, possible_keys, percepts):
        k0 = self.keycols[0]
        k1 = self.keycols[1]
        heatmap = np.full((len(possible_keys[k0]), len(possible_keys[k1])), np.nan)
        for p in percepts:
            idx_a = possible_keys[k0].index(p[k0])
            idx_b = possible_keys[k1].index(p[k1])
            cnt = p[self.valcols[0]]
            if cnt > 0:
                heatmap[idx_a, idx_b] = cnt
        return heatmap

    def visualise(self, pivot_percepts, compare_percepts, sorted_keys, n_charts, suffix=""):
        possible_keys = self.get_possible_keys(compare_percepts)

        heatmap_compare = self.create_heatmap(possible_keys, pivot_percepts)
        fig, axes = plt.subplots(nrows=n_charts, ncols=2, figsize=(10, 5 * n_charts))
        for i, percepts in enumerate([compare_percepts[k] for k in sorted_keys]):
            if i >= n_charts:
                break
            cax = axes[i][0].imshow(heatmap_compare, aspect='auto')
            axes[i][0].set_title(f"Compare_to")
            axes[i][0].set_xlabel(self.keycols[0])
            axes[i][0].set_ylabel(self.keycols[1])
            axes[i][0].set_xticks([])
            axes[i][0].set_yticks([])

            heatmap = self.create_heatmap(possible_keys, percepts)
            cax = axes[i][1].imshow(heatmap, aspect='auto')
            axes[i][1].set_title(f"{i} {suffix}: {sorted_keys[i]}")
            axes[i][1].set_xlabel(self.keycols[0])
            axes[i][1].set_ylabel(self.keycols[1])
            axes[i][1].set_xticks([])
            axes[i][1].set_yticks([])
        plt.tight_layout()
        plt.show()
        plt.close()

    def compare_two_percept_lists(self, pl1, pl2):
        # For each item in pl1, Find the closest item in p2, then add that to the cumulative distance
        # Does not need to be symmetric; comp(pl1, pl2) does not need to equal comp(pl2, pl1)
        total_dist = 0
        for p1 in pl1:
            data = {}
            for i in range(len(pl2)):
                p2 = pl2[i]
                data[i] = self.singlepercept_dist(p1, p2)
            min_dist_idx = min(data, key=lambda k: data[k])
            total_dist += data[min_dist_idx]
        return total_dist

    def singlepercept_dist(self, p1, p2):
        # What's the distance between a pair of single percepts
        dist = 0.0
        # Use taxicab distance on keycols, multiply by 100, add taxicab on valcols
        for k in self.keycols:
            try:
                dist += abs(float(p1[k]) - float(p2[k]))
            except:
                pass
        dist *= 100
        for k in self.valcols:
            try:
                dist += abs(float(p1[k]) - float(p2[k]))
            except:
                pass
        return dist

    def get_percept_list(self, cbr, mop_name):
        flattened_percepts = self.get_flattened_percept_list(cbr, mop_name)
        combined_percepts = self.combine_percept_list(flattened_percepts)
        return combined_percepts

    def combine_percept_list(self, percept_list):
        # We may have percepts that need combining [eg same weapon/target pairing should have their counts summed]
        # This is destructive on the passed list. Pass a deepcopy if you don't want that
        combined_percept_list = []

        while len(percept_list) > 0:
            percept = percept_list.pop(0)
            i = 0
            while i < len(percept_list):
                p_test = percept_list[i]
                is_match = True
                for k in self.keycols:
                    if p_test[k] != percept[k]:
                        is_match = False
                        break
                if is_match:
                    # print("Combining " + str(percept) + " and " + str(p_test))
                    for valcol in self.valcols:
                        percept[valcol] += p_test[valcol]
                    percept_list.pop(i)
                else:
                    i+=1

            combined_percept_list.append(percept)
        return combined_percept_list

    # For a given mop, get all the individual percepts as a single list-of-dicts
    #  May have to traverse lists mutliple times, recursively
    def get_flattened_percept_list(self, cbr, mop_name):
        # Not doing any sanity checking. If you don't pass this a scenario, expect it to break
        mop = cbr.mops[mop_name]
        percepts = mop.slots["percepts"]
        group_mop = cbr.mops["M_percept_group"]
        return self.get_flattened_percept_list_r(cbr, percepts, group_mop)

    def get_flattened_percept_list_r(self, cbr, percept_mop, group_mop, depth=0):
        retval = []
        if group_mop.is_abstraction(percept_mop):
            for next_mop in percept_mop.slots.values():
                retval.extend(self.get_flattened_percept_list_r(cbr, next_mop, group_mop, depth+1))
        else:
            slots = percept_mop.slots
            # Sometimes the percept is just a list of things.
            #  It still gets stored as a key then a value that is a group.
            #  Throw away the key and start again with the value
            if 1 == len(slots):
                slotval = next(iter(slots.values()))
                if isinstance(slotval, MOP) and group_mop.is_abstraction(slotval):
                    retval.extend(self.get_flattened_percept_list_r(cbr, slotval, group_mop))
                    return retval
            if isinstance(slots, LoggedDict):
                slots = slots.data
            retval.append(copy.deepcopy(slots))
        # print(".".join(["" for _ in range(depth+1)]) + " " + str(len(retval)))
        return retval


class EscalationLadderCBR(CaseBasedReasoner):
    def __init__(self, env, time, load_memory_from = None):
        super().__init__(env, time)
        self.upper_threshold = 5  # how many net deviations from a known case are required to think the new case is more severe
        self.lower_threshold = -5 # how many net deviations from a known case are required to think the new case is less severe
        self.too_distant_threshold = 400 
        self.distant_threshold = 200
        if load_memory_from:
            self.load(load_memory_from)
        else:
            self.add_mop(mop_name='M-CALC', mop_type='mop', is_default_mop=True)
            self.add_mop(mop_name='M_percept', absts={'M-EVENT'}, mop_type = 'mop', is_default_mop=True)
            self.add_mop(mop_name='M_percept_group', absts={'M-GROUP'}, slots={1: self.name_mop('M_percept')}, is_default_mop=True)
            ## potential outcomes
            self.add_mop(mop_name='M_ELRScenario_outcome', absts={'M-EVENT'}, mop_type = 'mop', is_default_mop=True)
            self.add_mop(mop_name='I_M_escalate_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance', is_default_mop=True)
            self.add_mop(mop_name='I_M_deescalate_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance', is_default_mop=True)
            self.add_mop(mop_name='I_M_no_change_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance', is_default_mop=True)
            ## ELRScenario
            self.add_mop(mop_name='M_ELRScenario',
                        absts={'M-CASE'},
                        mop_type='mop',
                        slots={ 'old': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.get_sibling_scenario}, is_default_mop=True),
                               'percepts': self.name_mop('M_percept_group'),
                                'current_rung': 0,
                                'next_rung': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.decide_next_rung}, is_default_mop=True),
                                # 'outcome': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.adapt_outcome}, is_default_mop=True)
                                },
                         is_default_mop=True
            )


    def get_sibling_scenario(self, pattern, mop):
        '''Finds a sibling of MOP. It is only defined for instance MOPs.'''
        if self.decision_making_ability is not None:
            mop_name = mop.mop_name
            compare_mops = [sibling for sibling in self.get_all_siblings(mop) if sibling != mop]
            sorted_mops = self.mop_comparer_sorter.compare_mops_and_sort(self, mop_name, compare_mops)
            best_sibling = self.name_mop(sorted_mops[0])
            for sibling_name in sorted_mops:
                sibling = self.name_mop(sibling_name)
                if sibling.slots['current_rung'] == mop.slots['current_rung']:
                    best_sibling = sibling
            return best_sibling
        else:
            for abst in mop.absts: # goes up one layer in abstraction
                for spec in abst.specs: # looks at all specializations
                    if isinstance(spec, MOP) and \
                        spec.is_instance_mop() and \
                        spec != mop and not spec.is_abstraction(self.name_mop('M-FAILED-SOLUTION')) and \
                        spec.slots['current_rung'] == mop.slots['current_rung']:
                                        sibling = spec
        return sibling


    def make_decision(self, scenario_slots): # like judge.judge_case
        # this function is called whenever the ELR tries to fill the outcome slot
        print("---------------------------")
        instance = self.slots_to_mop(slots=scenario_slots, absts={'M_ELRScenario'}, mop_type='instance', must_work=True)
        print(f"Deciding outcome in {instance}...")
        # outcome = instance.get_filler('outcome')
        next_rung = instance.get_filler('next_rung')
        print(f"Next rung in {instance} is {next_rung}.")
        return next_rung


    def decide_next_rung(self, pattern, mop):
        self.mop_comparer_sorter = ELRPerceptMOPComparer()
        old_mop = mop.get_filler('old') # calls get_sibling
        print(f"Comparing new scenario {mop} (current_rung={mop.get_filler('current_rung')}) to old scenario {old_mop} (current_rung={old_mop.get_filler('current_rung')}, next_rung={old_mop.get_filler('next_rung')})...")
        old_outcome = old_mop.get_filler('outcome')
        # calculate difference between percepts
        old_percepts = self.mop_comparer_sorter.get_flattened_percept_list(self, old_mop.mop_name)
        new_percepts = self.mop_comparer_sorter.get_flattened_percept_list(self, mop.mop_name)
        distance = self.mop_comparer_sorter.compare_two_percept_lists(old_percepts, new_percepts)
        print("---------------------------")
        current_rung = mop.get_filler('current_rung')
        if distance > self.too_distant_threshold:
            next_rung = current_rung
            print(f"New and old scenarios too distant (distance={distance}),", end=' ')
        elif distance > self.distant_threshold:
            rung_change = old_mop.get_filler('next_rung') - old_mop.get_filler('current_rung')
            if abs(rung_change) == 1 or rung_change == 0:
                next_rung = current_rung
            elif rung_change > 1:
                next_rung = current_rung + 1
            else:
                next_rung = current_rung - 1
            print(f"New and old scenarios distant (distance={distance}),", end=' ')
        else:
            next_rung = old_mop.get_filler('next_rung')
            print(f"New and old scenarios not similar at distant (distance={distance}),", end=' ')
        if (current_rung - next_rung) > 0:
            outcome = 'deescalate'
        elif (current_rung - next_rung) < 0:
            outcome = 'escalate'
        else:
            outcome = 'no change'
        print(f"{outcome} from {current_rung} to {next_rung}")
        print("---------------------------")
        mop.absts.add(old_mop.mop_name)
        return next_rung


    def increase_outcome(self, outcome):
        if outcome == 'deescalation':
            return 'no change'
        return 'escalation'
    

    def decrease_outcome(self, outcome):
        if outcome == 'escalation':
            return 'no change'
        return 'deescalation'
    

    def mop_calc(self, slots):
        instance = self.slots_to_mop(slots=slots, absts={'M-CALC'}, mop_type='instance')
        if instance:
            return instance.get_filler('value')
        return None


    def serialize(self, path):
        filepath = Path.cwd() / path
        with open(filepath, 'wb') as f:
            dump(self.mops, f)
   

    def load(self, path):
        filepath = Path.cwd() / path
        with open(filepath, 'rb') as f:
            self.mops = load(f)


    ''' Given some percepts, recursively create groups for as long as some of the things are lists or dicts.
     Eventually return a mop'''
    def create_mop_percepts_slots_r(self, percepts):
        slots_dict = {}
        if isinstance(percepts, dict):
            for k, v in percepts.items():
                if isinstance(v, dict) or isinstance(v, list):
                    slots_dict[k] = self.create_mop_percepts_slots_r(v)
                else:
                    slots_dict[k] = v
        elif isinstance(percepts, list):
            if 0 == len(percepts):
                return None
            elif 1 == len(percepts):
                return self.create_mop_percepts_slots_r(percepts[0])
            else:
                group_slots = {}
                for i in range(len(percepts)):
                    group_slots[i] = self.create_mop_percepts_slots_r(percepts[i])
                return self.add_mop(absts={'M_percept_group'}, mop_type='instance', slots=group_slots)
        else:
            print("Percepts is neither dict nor list")
            slots_dict["percept"] = percepts
        return self.add_mop(mop_type='instance', absts={'M_percept'}, slots=slots_dict)
    

    def add_ELRScenario(self, percepts, current_rung, next_rung, outcome):
        percept_group = self.create_mop_percepts_slots_r(percepts)

        # outcome
        if outcome == 'deescalate':
            outcome = self.name_mop('I_M_deescalate_outcome')
        elif outcome == 'escalate':
            outcome = self.name_mop('I_M_escalate_outcome')
        else:
            outcome = self.name_mop('I_M_no_change_outcome')
       
        ## create the new scenario
        slots = {'percepts': percept_group, 'current_rung': current_rung, 'next_rung': next_rung, 'outcome': outcome}
        self.add_mop(absts={'M_ELRScenario'},
                     mop_type='instance',
                     slots=slots)


    def display_memory(self, include_scenario_details=False):
        print("------------------")
        print("ELRScenarios:")
        outcome_totals = {}
        for spec in self.name_mop("M_ELRScenario").specs:
            outcome = spec.slots['outcome']
            outcome_totals[outcome] = outcome_totals.get(outcome, 0) + 1
        print("Outcomes: " + str(outcome_totals))
        print()

        if include_scenario_details:
            ## show known ELRScenarios
            for spec in self.name_mop("M_ELRScenario").specs:
                print(spec.mop_name)
                print(spec.slots['percepts'])
                print(spec.slots['outcome'])
                print()