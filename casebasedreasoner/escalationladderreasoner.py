from cbr import CaseBasedReasoner, MOPComparerSorter, MOP
from dill import dump, load
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import copy

from romancer.environment.object import LoggedDict


## CB-ELR Design Model:
# 1. The ELR inherits from the CBR, so that it can perform case-based reasoning like the Judge.
# 2. Like the Judge, it needs its own set of "domain-specific" MOPs, like "percepts", "ladder rungs", "amygdala data", and "outcomes".
# 3. Like the Judge, it creates a specialization of M-CASE, M_ELRScenario (I've changed naming convention to M_... for ease of typing).
# 4. Like the Judge, it uses make_decision, adapt_outcome, and mop_calc to fill missing roles (ie, "outcome") based on prior cases and its own knowledge.
# 5. "percepts" and "ladder rungs" are purely abstract: their form is inferred from the external caller/trainer, although we do assume a single percept is a single dictionary of data


## Proposed CB-ELR Model/Process:
### An ELRScenario is defined by {percepts, amygdala_data, current_rung, next_rung, outcome} (do we need current_rung? why?)
### In the Simulation, one "percept" has a list of "events" (eg, events[0] = {'weapon': 3, 'target': 4}),
# but I made the choice to turn each event into its own "percept" for this model, since each event could trigger escalation

## The CB-ELR should be able to figure out whether it "should" escalate/deescalate/neither, without consulting its memories
## In other words, it needs to be able to compare the percepts in a scenario with the current_rung in the scenario,
## and make a decision, regardless of prior scenarios.
## But, this decision is a purely rational decision, based on comparing perceived events to an escalation ladder rung.
## So, the point of this CB-ELR model is to account for the amygdala. In other words,
## the CB-ELR should be able to take the "correct" outcome and adjust it based on its memories of prior scenarios and their amygdala data.

## Should the CB-ELR be able to decide what the outcome of a scenario "should" be? Eg, compare percepts to current_rung and conclude "I should escalate"
## Should the CB-ELR *not* calculate the "correct" outcome and only make conclusions based on past memories?
## If we do calculate the "correct" outcome, then that means we're only using memories to decide whether our amygdala overrides our outcome. Is this what we want?

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
            dist += abs(p1[k] - p2[k])
        dist *= 100
        for k in self.valcols:
            dist += abs(p1[k] - p2[k])
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
        if load_memory_from:
            super().__init__(env, time)
            self.load(load_memory_from)
        else:
            super().__init__(env, time)
            self.add_mop(mop_name='M-CALC', mop_type='mop', is_default_mop=True)
            self.add_mop(mop_name='M_percept', absts={'M-EVENT'}, mop_type = 'mop', is_default_mop=True)
            self.add_mop(mop_name='M_percept_group', absts={'M-GROUP'}, slots={1: self.name_mop('M_percept')}, is_default_mop=True)
            self.add_mop(mop_name='M_amygdala_data', absts={'M-EVENT'}, slots={'pbf_level': 0.0, 'fight_level': 0.0, 'flight_level': 0.0, 'freeze_level': 0.0}, mop_type = 'mop', is_default_mop=True)
            self.add_mop(mop_name='M_ladder_rung', absts={'M-STATE'}, mop_type = 'mop', is_default_mop=True)
            self.add_mop(mop_name='M_escalation_ladder', absts={'M-GROUP'}, slots={1:self.name_mop('M_ladder_rung')}, is_default_mop=True)
            ## potential outcomes
            outcome = self.add_mop(mop_name='M_ELRScenario_outcome', absts={'M-EVENT'}, mop_type = 'mop', is_default_mop=True)
            self.add_mop(mop_name='I_M_escalate_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance', is_default_mop=True)
            self.add_mop(mop_name='I_M_deescalate_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance', is_default_mop=True)
            self.add_mop(mop_name='I_M_no_change_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance', is_default_mop=True)
            ## ELRScenario
            self.add_mop(mop_name='M_ELRScenario',
                        absts={'M-CASE'},
                        mop_type='mop',
                        slots={'percepts': self.name_mop('M_percept_group'),
                                'amygdala_data': self.name_mop('M_amygdala_data'),
                                'current_rung': self.name_mop('M_ladder_rung'),
                                'outcome': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.adapt_outcome}, is_default_mop=True)
                                },
                         is_default_mop=True
            )
            ## adaptation MOPs
            self.add_mop(mop_name='M_adapt_outcome',
                         absts={'M-CALC'},
                         slots={'role': outcome,
                                'value': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.adjust_outcome}, is_default_mop=True)},
                         is_default_mop=True)
            self.add_mop(mop_name='M_adapt', is_default_mop=True)


    def make_decision(self, scenario_slots): # like judge.judge_case
        # this function is called whenever the ELR tries to fill the outcome slot
        print("---------------------------")
        instance = self.slots_to_mop(slots=scenario_slots, absts={'M_ELRScenario'}, mop_type='instance', must_work=True)
        print(f"Deciding outcome in {instance}...")
        outcome = instance.get_filler('outcome')
        print(f"Outcome in {instance} is {outcome}.")


    ## TODO:
    ## 1. figure out how to get an "old" case with the same current_rung as the "this" case
    ## 2. figure out how to get the "base" outcome, ie "given the percepts and the current_rung, what *should* I do?"
    ## 3. write adapt_outcome MOPs to cover possible scenarios involving two different sets of amygdala data and/or percepts
    ## 4. write self.adapt_outcome() to construct the slots for an adapt_outcome MOP and get the result
    ## 5. write self.adjust_outcome() which should adjust an outcome up or down based on what the adapt_outcome MOP says
    ## 6. optionally, we should explore more than 1 "old" scenario to aggregate our decision
    def adapt_outcome(self, pattern, mop): # compares amygdala parameters in old and new scenarios, adjusting outcome if it should
        old_mop = mop.get_filler('old') ## whatever it gets from OLD ought to have the same current_rung, or else the comparison is nonsense
        old_outcome = old_mop.get_filler('outcome')

        outcome = "???"
        print("---------------------------")
        print(f"Based on percepts and current rung, outcome should be {outcome}")
        print("---------------------------")
        print(f"Looking at amygdala parameters in {old_mop}")
        ## the Judge calculates the MOTIVES of the old and new crimes (crime_compare_slots, using mop_calc)
        ## then, it calculates the adjustment to the old sentence (mop_calc > adjust_sentence) using the ADAPT-SETENCE mop it calculates
        # for pos in range(0, min(old_size, size)):
        #     old_index = old_size - pos
        #     index = size - pos
        #     slots = {'role': sentence, 'index': pos, 'old_sentence': old_sentence}
        #     slots.update(judge.crime_compare_slots(old_mop, old_index, ['old_action', 'old_motive', 'old_severity']))
        #     slots.update(judge.crime_compare_slots(mop, index, ['this_action', 'this_motive', 'this_severity']))
        #     result = judge.mop_calc(slots)
        #     if result is not None:
        #         return result

        ## we don't need a calculated field like MOTIVES, so we don't need something like crime_compare_slots
        ## but we do something like adjust_sentence, to move an outcome up or down based on amygdala params
        ## let's brainstorm some situations:
        ## ** assume current_rung is the same for both scenarios **
        ## old_outcome is what it should be (amygdala didn't override) -> compare this_fight, this_flight, this_freeze to old values, if not too different, give same outcome
        ## old_outcome should not be "escalate" but is "escalate" (fight) -> compare this_fight to old_fight
        ## old_outcome should not be "no change" but is "no change" (freeze) -> compare this_freeze to old_freze
        ## old_outcome should not be "deescalate" but is "deescalate" (flight) -> compare this_flight to old_flight
        amygdala_data = []
        for value in amygdala_data:
            # construct the slots of an M_adapt_outcome spec (see above for examples of these specs)
            pass
   
        print("---------------------------")
        print("No major differences found")
        print("Using old outcome")
        return old_outcome


    def adjust_outcome(self, pattern, mop): 
        pass

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

    def add_escalation_ladder(self, rungs):
        # assume rungs is a list of match_attribute dictionaries
        if len(self.name_mop("M_escalation_ladder").specs) > 0:
            for spec in self.name_mop("M_escalation_ladder").specs:
                self.remove_mop(spec)

        rung_group = {}
        counter = 1
        for rung in rungs:
            rung_mop = self.add_mop(absts={'M_ladder_rung'}, slots=rung, mop_type='instance', is_default_mop=True)
            rung_group[counter] = rung_mop
            counter += 1
        self.add_mop(absts={"M_escalation_ladder"}, slots={'rungs': rung_group}, mop_type='instance', is_default_mop=True)

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


    def add_ELRScenario(self, percepts, amygdala_parameters, current_rung_match_attributes, outcome):
        percept_mop = self.create_mop_percepts_slots_r(percepts)

        # amygdala data
        amygdala_data_slots = {'pbf_level': amygdala_parameters.current_pbf,
                               'fight_level': amygdala_parameters.current_fight,
                               'flight_level': amygdala_parameters.current_flight,
                               'freeze_level': amygdala_parameters.current_freeze,
                               'dominant_response': amygdala_parameters.current_dominant_response}
        amygdala_data = self.add_mop(slots=amygdala_data_slots, absts={'M_amygdala_data'}, mop_type='instance')
       
        # current rung
        current_rung = self.add_mop(slots=current_rung_match_attributes, absts={'M_ladder_rung'}, mop_type='instance')

        # outcome
        if outcome == 'deescalate':
            outcome = self.name_mop('I_M_deescalate_outcome')
        elif outcome == 'escalate':
            outcome = self.name_mop('I_M_escalate_outcome')
        else:
            outcome = self.name_mop('I_M_no_change_outcome')
       
        ## create the new scenario
        slots = {'percepts': percept_mop, 'amygdala_data': amygdala_data, 'current_rung': current_rung, 'outcome': outcome}
        self.add_mop(absts={'M_ELRScenario'},
                     mop_type='instance',
                     slots=slots)


    def display_memory(self, include_scenario_details=False):
        ## show escalation ladder
        print("------------------")
        print("Displaying escalation ladder:")
        for spec in self.name_mop("M_escalation_ladder").specs:
            # ladder = self.name_mop(spec)
            print(spec.mop_name)
            for rung_number, rung in spec.slots.items():
                print(rung_number, rung)

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
