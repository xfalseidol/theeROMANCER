from escalationladderreasoner import EscalationLadderCBR
from simulation_scenario import run
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from romancer.agent.escalationladderreasoner import EscalationLadderReasoner, MatchAllRung, EscalationLadder
from romancer.agent.amygdala import Amygdala, Amygdala_Fight, Amygdala_Freeze, Amygdala_Flight, Amygdala_StoneCold
from romancer.environment.percept import Percept
from casebasedreasoner.util import  export_cbr_sqlite
import random

def _get_amygdala_random(env, count):
    ### DEFAULT AMYGDALA PARAMETERS
    red_initial_fight = 0.0
    red_initial_flight = 0.0
    red_initial_freeze = 0.0
    red_pbf_halflife = 100.0
    red_max_pbf = 1.0

    def _get_random_amygdala():
        # randomize key parameters
        red_response_threshhold = random.random()
        red_flight_weight = random.random()
        red_fight_weight = random.random()
        red_freeze_weight = random.random()
        red_initial_pbf = random.random()

        # construct amygdala
        amygdala = Amygdala(environment=env, time=env.time, fight_weight=red_fight_weight,
                            flight_weight=red_flight_weight, freeze_weight=red_freeze_weight,
                            initial_fight=red_initial_fight, initial_flight=red_initial_flight,
                            initial_freeze=red_initial_freeze, initial_pbf=red_initial_pbf,
                            pbf_halflife=red_pbf_halflife, max_pbf=red_max_pbf,
                            response_threshhold=red_response_threshhold)
        return amygdala

    random_amygs = [_get_random_amygdala() for _ in range(count)]
    return random_amygs

def _get_amygdala_archetypes(env):
    archetype_amygs = [
        Amygdala_Fight(env, env.time),
        Amygdala_Flight(env, env.time),
        Amygdala_Freeze(env, env.time),
        Amygdala_StoneCold(env, env.time)
    ]
    return archetype_amygs

### EVENT CONSTRUCTION
weapon_classes = 5
target_classes = 5
hit_counts = 1

### ESCALATION LADDER DEFINITION
rungs = []
for i in range(weapon_classes):
    eventclass = i+1
    rung = MatchAllRung(match_attributes = {'weapon': str(eventclass), 'target': str(eventclass)})
    rungs.append(rung)
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
amygdala_scenarios = 100
# amygdalas = _get_amygdala_random(env, amygdala_scenarios)
amygdalas = _get_amygdala_archetypes(env)
amygdala_cnt = 0
for amygdala in amygdalas:
    amygdala_cnt += 1
    print(f"Training {weapon_classes*target_classes*hit_counts} percepts on {len(ELR.escalation_ladder)} rungs for Random Amygdala Scenario {amygdala_cnt}/{len(amygdalas)} ...")
    for weapon in range(1, weapon_classes + 1):
        for target in range(1, target_classes + 1):
            for hit_count in range(hit_counts):
                for rungnum in range(len(ELR.escalation_ladder)):
                    ELR.reset_reasoner(rungnum)
                    percept = Percept(events_list={'weapon': weapon, 'target': target, 'count': hit_count})
                    ELR.enqueue_digested_percept(digested_percept=percept, percept_time=0)
                    ELR.deliberate(0, amygdala) # this will log ELRscenario memories into the attached CBR

ELCBR.display_memory()

export_cbr_sqlite(ELCBR, "trainedELCBR.sqlite")

# serialize it
print(f"Pickling trained ELCBR, with {len(ELCBR.mops)} mops")
ELCBR.serialize("trainedELCBR.pkl")

# create a new CB-ELR and load the old one's memories into it
print("Verify-Loading trained ELCBR")
new_ELCBR = EscalationLadderCBR(env, env.time, load_memory_from="trainedELCBR.pkl")
print(f"Reloaded CBR has {len(new_ELCBR.mops)} mops")