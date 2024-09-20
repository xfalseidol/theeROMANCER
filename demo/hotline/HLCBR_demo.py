import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from romancer.environment.percept import Percept
from casebasedreasoner.escalationladderreasoner import EscalationLadderCBR
from casebasedreasoner.MOP_comparer_sorter import HLRComparerSorter
def test_get_sibling_scenario(new_scenario_slots):
    new_scenario = ELCBR.slots_to_mop(slots=new_scenario_slots, absts={'M_ELRScenario'}, mop_type='instance', must_work=True)
    old = ELCBR.get_sibling_scenario(None, new_scenario)
    print("TESTING GET SIBLING:")
    print(old)
    print(old.slots)
    print(old.slots['percepts'].slots[1].slots)
    print()
def test_make_decision(new_scenario_slots):
    print("TESTING MAKE DECISION:")
    result = ELCBR.make_decision(new_scenario_slots)
    print(result)
    print()
sup = SingleThreadSupervisor()
env = SingleThreadEnvironment(sup, None, None)
ELCBR = EscalationLadderCBR(env, env.time, load_memory_from="demo\\hotline\\trainedHLR.pkl", verbose=True, comparer_sorter=HLRComparerSorter())
percepts = [Percept(actor=6, action_taken=15)]
rung = 1
new_scenario_slots = ELCBR.make_scenario_slots(percepts, rung)
test_get_sibling_scenario(new_scenario_slots)
test_make_decision(new_scenario_slots)