from escalationladderreasoner import EscalationLadderCBR
from simulation_scenario import run
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from romancer.agent.escalationladderreasoner import EscalationLadderReasoner, MatchAllRung, EscalationLadder
from romancer.agent.amygdala import Amygdala
from romancer.environment.percept import Percept
import random


def _get_next_amygdala():
    # randomize key parameters
    red_response_threshhold = random.random()
    red_flight_weight = random.random()
    red_fight_weight = random.random()
    red_freeze_weight = random.random()
    red_initial_pbf = random.random()

    # construct amygdala
    amygdala = Amygdala(environment = env, time = env.time, fight_weight = red_fight_weight, flight_weight = red_flight_weight, freeze_weight = red_freeze_weight, initial_fight = red_initial_fight, initial_flight = red_initial_flight, initial_freeze = red_initial_freeze, initial_pbf = red_initial_pbf, pbf_halflife = red_pbf_halflife, max_pbf = red_max_pbf, response_threshhold = red_response_threshhold)
    return amygdala

### DEFAULT AMYGDALA PARAMETERS
red_fight_weight = 1.0
red_flight_weight = 1.0
red_freeze_weight = 1.0
red_initial_fight = 0.0
red_initial_flight = 0.0
red_initial_freeze = 0.0
red_initial_pbf = 0.0001
red_pbf_halflife = 100.0
red_max_pbf = 1.0

### ESCALATION LADDER DEFINITION
rung1 = MatchAllRung(match_attributes = {'weapon': '1', 'target': '1'})
rung2 = MatchAllRung(match_attributes = {'weapon': '2', 'target': '2'})
rung3 = MatchAllRung(match_attributes = {'weapon': '3', 'target': '3'})
rung4 = MatchAllRung(match_attributes = {'weapon': '4', 'target': '4'})
rung5 = MatchAllRung(match_attributes = {'weapon': '5', 'target': '5'})
rungs = [rung1, rung2, rung3, rung4, rung5]
escalation_ladder = EscalationLadder(rungs)

### TRAINING
env = SingleThreadEnvironment(None, None, None)
ELCBR = EscalationLadderCBR(env, env.time)
ELR = EscalationLadderReasoner(env, env.time, escalation_ladder=escalation_ladder, identity='red', cbr=ELCBR)

# inform ELCBR of ladder rungs
match_attributes = []
for rung in rungs:
    match_attributes.append(rung.match_attributes)
ELCBR.add_escalation_ladder(match_attributes)

# train on random amygdalas and systematic percepts
amygdala_scenarios = 10
weapon_classes = 5
target_classes = 5
hit_counts = 1
for i in range(amygdala_scenarios):
    print(f"Training {weapon_classes*target_classes*hit_counts} percepts for Random Amygdala Scenario {i + 1}...")
    amygdala = _get_next_amygdala()
    for weapon in range(1, weapon_classes + 1):
        for target in range(1, target_classes + 1):
            for hit_count in range(hit_counts):
                percept = Percept(events_list={'weapon': weapon, 'target': target, 'count': hit_count})
                ELR.enqueue_digested_percept(digested_percept=percept, percept_time=0)
                ELR.deliberate(0, amygdala) # this will log ELRscenario memories into the attached CBR

ELCBR.display_memory()

# serialize it
ELCBR.serialize("trainedELCBR.pkl")

# create a new CB-ELR and load the old one's memories into it
new_ELCBR = EscalationLadderCBR(env, env.time, load_memory_from="trainedELCBR.pkl")
print(new_ELCBR.mops)
