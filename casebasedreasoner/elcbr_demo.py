import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from casebasedreasoner.escalationladderreasoner import EscalationLadderCBR


def test_get_sibling_scenario():
    sup = SingleThreadSupervisor()
    env = SingleThreadEnvironment(sup, None, None)
    ELCBR = EscalationLadderCBR(env, env.time)
    ELCBR.add_ELRScenario([], 3, 'escalation')
    ELCBR.add_ELRScenario([], 4, 'escalation')
    ELCBR.add_ELRScenario([], 5, 'deescalation')
    scenario_slots = {'percepts': None, 'current_rung': 3}
    new_scenario = ELCBR.slots_to_mop(slots=scenario_slots, absts={'M_ELRScenario'}, mop_type='instance', must_work=True)
    old = ELCBR.get_sibling_scenario(None, new_scenario)
    print(old)
    print(old.slots)


def test_make_decision():
    sup = SingleThreadSupervisor()
    env = SingleThreadEnvironment(sup, None, None)
    ELCBR = EscalationLadderCBR(env, env.time, load_memory_from="trainedELCBR.pkl")
    all_scenarios = ELCBR.name_mop('M_ELRScenario').specs
    percept_slots = {'weapon': '3', 'target': '3', 'count': '4'}
    new_percept = ELCBR.create_mop_percepts_slots_r([percept_slots])
    new_scenario_slots = {'percepts': new_percept, 'current_rung': 2}
    ELCBR.make_decision(new_scenario_slots)
    pass

# test_get_sibling_scenario()
test_make_decision()