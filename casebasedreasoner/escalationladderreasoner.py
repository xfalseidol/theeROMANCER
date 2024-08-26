from .cbr import CaseBasedReasoner
from dill import dump, load
from pathlib import Path


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
class EscalationLadderReasoner(CaseBasedReasoner):
    def __init__(self, env, time, load_memory_from = None):
        if load_memory_from:
            super().__init__(env, time)
            self.load(load_memory_from)
        else:
            super().__init__(env, time)
            ## percepts only track weapon and target class
            self.add_mop(mop_name='M_percept', absts={'M-EVENT'}, slots={'weapon_class': 0, 'target_class': 0}, mop_type = 'mop')
            self.add_mop(mop_name='M_percept_group', absts={'M-GROUP'}, slots={1: self.name_mop('M_percept')})
            self.add_mop(mop_name='M_amygdala_data', absts={'M-EVENT'}, slots={'pbf_level': 0.0, 'fight_level': 0.0, 'flight_level': 0.0, 'freeze_level': 0.0}, mop_type = 'mop')
            ## ladder rungs only look for weapon and target class
            self.add_mop(mop_name='M_ladder_rung', absts={'M-STATE'}, slots={'weapon_class': 0, 'target_class': 0}, mop_type = 'mop')
            ## potential outcomes
            outcome = self.add_mop(mop_name='M_ELRScenario_outcome', absts={'M-EVENT'}, mop_type = 'mop')
            self.add_mop(mop_name='I_M_escalate_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance')
            self.add_mop(mop_name='I_M_deescalate_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance')
            self.add_mop(mop_name='I_M_no_change_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance')
            ## ELRScenario
            self.add_mop(mop_name='M_ELRScenario',
                        absts={'M-CASE'},
                        mop_type='mop',
                        is_core_cbr_mop=True,
                        slots={'percepts': self.name_mop('M_percept_group'),
                                'amygdala_data': self.name_mop('M_amygdala_data'),
                                'current_rung': self.name_mop('M_ladder_rung'),
                                'outcome': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.adapt_outcome})
                                }
            )
            ## adaptation MOPs
            self.add_mop(mop_name='M_adapt_outcome',
                         absts={'M-CALC'},
                         slots={'role': outcome,
                                'value': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.adjust_outcome})})
            self.add_mop(mop_name='M_adapt')


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


    def add_ELRScenario(self, percepts, amygdala_parameters, current_rung_match_attributes, outcome):
        # percepts
        slots={}
        counter = 1
        for percept in percepts:
            for event in percept.events_list:
                slots[counter] = self.add_mop(mop_type='instance', absts={'M_percept'}, slots={'weapon_class': event['weapon'], 'target_class': event['target']})
                counter += 1
        percept_group = self.add_mop(absts={'M_percept_group'}, mop_type='instance', slots=slots)

        # amygdala data
        amygdala_data_slots = {'pbf_level': amygdala_parameters.current_pbf,
                               'fight_level': amygdala_parameters.current_fight,
                               'flight_level': amygdala_parameters.current_flight,
                               'freeze_level': amygdala_parameters.current_freeze}
        amygdala_data = self.add_mop(slots=amygdala_data_slots, absts={'M_amygdala_data'}, mop_type='instance')
       
        # current rung
        current_rung_slots = {'weapon_class': current_rung_match_attributes['weapon'], 'target_class': current_rung_match_attributes['target']}
        current_rung = self.add_mop(slots=current_rung_slots, absts={'M_ladder_rung'}, mop_type='instance')
       
        # outcome
        if outcome == 'deescalate':
            outcome = self.name_mop('I_M_deescalate_outcome')
        elif outcome == 'escalate':
            outcome = self.name_mop('I_M_escalate_outcome')
        else:
            outcome = self.name_mop('I_M_no_change_outcome')
       
        ## create the new scenario
        slots = {'percepts': percept_group, 'amygdala_data': amygdala_data, 'current_rung': current_rung, 'outcome': outcome}
        self.add_mop(absts={'M_ELRScenario'},
                     mop_type='instance',
                     slots=slots)
