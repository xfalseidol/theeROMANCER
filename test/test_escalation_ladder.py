from context import *
import unittest
import romancer.agent.escalationladderreasoner
import romancer.environment
import romancer.environment.environment
from romancer.environment.percept import Percept
from romancer.agent.amygdala import Amygdala

# create an EscalationLadderReasoner (assume we're making blue)
## create an EscalationLadder
## create EscalationLadderRungs: "ConDef"
class EscalationLadderTest(unittest.TestCase):
    sup = romancer.supervisor.singlethreadsupervisor.SingleThreadSupervisor()
    env = romancer.environment.singlethreadenvironment.SingleThreadEnvironment(sup, None, None)
    reasoner = None

    def test_rungs(self):
        ladder = romancer.agent.escalationladderreasoner.EscalationLadder()
        rung_1 = self.get_rung_1()
        ladder.append(rung_1)
        ladder.append(self.get_rung_2())
        ladder.append(self.get_rung_3())
        ladder.append(self.get_rung_4())
        ladder.append(self.get_rung_5())
    
        self.reasoner = romancer.agent.escalationladderreasoner.EscalationLadderReasoner(environment=self.env, time=self.env.time, escalation_ladder=ladder, identity='blue')
        assert self.reasoner.current_rung == rung_1, f"Reasoner's current rung {self.reasoner.current_rung} does not match Rung 1 {rung_1}"
  
    
    def test_deliberate_current_time(self):
        self.reset_reasoner()

        # call deliberate with several different values of max_time, depending on the time of the percepts in the previous test
        # deliberate is suppoosed to return certain time values or None, depending on whether escalation has occurred
        max_time = 0
        amygdala = Amygdala(self.env, self.env.time)
        result = self.reasoner.deliberate(max_time, amygdala)
        assert result is None, "Result of deliberating at t=0 resulted in an escalation, but shouldn't have."
        current_rung_number = self.reasoner.escalation_ladder.rung_number(self.reasoner.current_rung)
        assert current_rung_number == 1, f"expected 1, got {current_rung_number}"

        ## simple escalation to Rung 2
        new_time = 5
        self.reasoner.forward_simulation(new_time)
        new_percept = Percept(weapon_class=1, location='Hong Kong')
        self.reasoner.enqueue_digested_percept(digested_percept=new_percept, percept_time=new_time, most_recent_percept_time=new_time)
        result = self.reasoner.deliberate(new_time, amygdala)
        assert result == 5, f"expected 5, got {result} (should have escalated)"
        current_rung_number = self.reasoner.escalation_ladder.rung_number(self.reasoner.current_rung)
        assert current_rung_number == 2, f"expected 2, got {current_rung_number}"

        ## no escalation
        new_time = 10
        self.reasoner.forward_simulation(new_time)
        new_percept = Percept(speed=1000, location='Hong Kong')
        self.reasoner.enqueue_digested_percept(digested_percept=new_percept, percept_time=new_time, most_recent_percept_time=new_time)
        result = self.reasoner.deliberate(new_time, amygdala)
        assert result is None, f"expected None, got {result} (should not have escalated)"
        current_rung_number = self.reasoner.escalation_ladder.rung_number(self.reasoner.current_rung)
        assert current_rung_number == 2, f"expected 2, got {current_rung_number}"

        ## simple escalation to Rung 3
        new_time = 15
        self.reasoner.forward_simulation(new_time)
        new_percept = Percept(weapon_class=1, location='South China Sea')
        self.reasoner.enqueue_digested_percept(digested_percept=new_percept, percept_time=new_time, most_recent_percept_time=new_time)
        result = self.reasoner.deliberate(new_time, amygdala)
        assert result == 15, f"expected 15, got {result} (should have escalated)"
        current_rung_number = self.reasoner.escalation_ladder.rung_number(self.reasoner.current_rung)
        assert current_rung_number == 3, f"expected 3, got {current_rung_number}"

        ## suddenly jump to Rung 5
        new_time = 20
        self.reasoner.forward_simulation(new_time)
        new_percept = Percept(weapon_class=5)
        self.reasoner.enqueue_digested_percept(digested_percept=new_percept, percept_time=new_time, most_recent_percept_time=new_time)
        result = self.reasoner.deliberate(new_time, amygdala)
        assert result == 20, f"expected 20, got {result} (should have escalated)"
        current_rung_number = self.reasoner.escalation_ladder.rung_number(self.reasoner.current_rung)
        assert current_rung_number == 5, f"expected 5, got {current_rung_number}"


    def test_deliberate_jump_several_rungs(self):
        self.reset_reasoner()

        amygdala = Amygdala(self.env, self.env.time)
        new_time = 20
        self.reasoner.forward_simulation(new_time)
        new_percept = Percept(weapon_class=5, location="Taiwan")
        self.reasoner.enqueue_digested_percept(digested_percept=new_percept, percept_time=new_time, most_recent_percept_time=new_time)
        result = self.reasoner.deliberate(new_time, amygdala)
        assert result == 20, f"expected 20, got {result} (should have escalated)"
        # assert self.reasoner.current_rung.match_attributes == {"weapon_class": 5}, f"expected rung with attributes 'weapon_class': 5, got rung with attributes {self.reasoner.current_rung.match_attributes}"
        current_rung_number = self.reasoner.escalation_ladder.rung_number(self.reasoner.current_rung)
        assert current_rung_number == 5, f"expected rung 5, got rung {current_rung_number}"

    def test_deliberate_future_time(self):
        ## for example, a plane on a bearing at present time is not in a restricted zone
        ## but is headed toward one

        ## for example, this amygdala has a stress condition, which increases stress over time
        pass


    def reset_reasoner(self):
        self.reasoner.rewind(0)
        self.reasoner.current_rung = self.reasoner.escalation_ladder[0]

   
    def get_rung_1(self):
        rung_1_match_attributes = {"weapon_class": 0}
        rung_1_blue_actions = ["Routine Patrols", "Training Exercises"]
        rung_1_red_actions = ["None", "Monitoring Only"]
        rung_1_blue_deescalation_actions = ["Reduce Patrols", "Stand Down Exercises"]
        rung_1_red_deescalation_actions = ["No Action Required", "Continue Monitoring"]

        rung_1 = romancer.agent.escalationladderreasoner.EscalationLadderRung(
            match_attributes=rung_1_match_attributes,
            blue_actions=rung_1_blue_actions,
            red_actions=rung_1_red_actions,
            blue_deescalation_actions=rung_1_blue_deescalation_actions,
            red_deescalation_actions=rung_1_red_deescalation_actions
        )

        return rung_1


    def get_rung_2(self):
        rung_2_match_attributes = {"weapon_class": 1, "location": "South China Sea"}
        rung_2_blue_actions = ["Strengthen Security Measures", "Increase Surveillance"]
        rung_2_red_actions = ["Increased Surveillance", "Gather Intelligence"]
        rung_2_blue_deescalation_actions = ["Reduce Security Measures", "Lower Surveillance"]
        rung_2_red_deescalation_actions = ["Decrease Surveillance", "Cease Intelligence Gathering"]

        rung_2 = romancer.agent.escalationladderreasoner.EscalationLadderRung(
            match_attributes=rung_2_match_attributes,
            blue_actions=rung_2_blue_actions,
            red_actions=rung_2_red_actions,
            blue_deescalation_actions=rung_2_blue_deescalation_actions,
            red_deescalation_actions=rung_2_red_deescalation_actions
        )

        return rung_2


    def get_rung_3(self):
        rung_3_match_attributes = {"weapon_class": 2, "location": "South China Sea"}
        rung_3_blue_actions = ["Mobilize Troops", "Deploy Strategic Assets"]
        rung_3_red_actions = ["Mobilize Forces", "Prepare Defenses"]
        rung_3_blue_deescalation_actions = ["Stand Down Troops", "Withdraw Strategic Assets"]
        rung_3_red_deescalation_actions = ["Stand Down Forces", "Disarm Defenses"]

        rung_3 = romancer.agent.escalationladderreasoner.EscalationLadderRung(
            match_attributes=rung_3_match_attributes,
            blue_actions=rung_3_blue_actions,
            red_actions=rung_3_red_actions,
            blue_deescalation_actions=rung_3_blue_deescalation_actions,
            red_deescalation_actions=rung_3_red_deescalation_actions
        )

        return rung_3


    def get_rung_4(self):
        rung_4_match_attributes = {"weapon_class": 3, "location": "Taiwan"}
        rung_4_blue_actions = ["Deploy Forces", "Activate Defense Systems"]
        rung_4_red_actions = ["Deploy Nuclear Forces", "Activate Countermeasures"]
        rung_4_blue_deescalation_actions = ["Recall Forces", "Deactivate Defense Systems"]
        rung_4_red_deescalation_actions = ["Stand Down Nuclear Forces", "Deactivate Countermeasures"]

        rung_4 = romancer.agent.escalationladderreasoner.EscalationLadderRung(
            match_attributes=rung_4_match_attributes,
            blue_actions=rung_4_blue_actions,
            red_actions=rung_4_red_actions,
            blue_deescalation_actions=rung_4_blue_deescalation_actions,
            red_deescalation_actions=rung_4_red_deescalation_actions
        )

        return rung_4


    def get_rung_5(self):
        rung_5_match_attributes = {"weapon_class": 5}
        rung_5_blue_actions = ["Launch Nuclear Weapons", "Engage Enemy Forces"]
        rung_5_red_actions = ["Launch Nuclear Weapons", "Engage Blue Forces"]
        rung_5_blue_deescalation_actions = ["Cease Fire", "Initiate Peace Talks"]
        rung_5_red_deescalation_actions = ["Cease Fire", "Agree to Peace Talks"]

        rung_5 = romancer.agent.escalationladderreasoner.EscalationLadderRung(
            match_attributes=rung_5_match_attributes,
            blue_actions=rung_5_blue_actions,
            red_actions=rung_5_red_actions,
            blue_deescalation_actions=rung_5_blue_deescalation_actions,
            red_deescalation_actions=rung_5_red_deescalation_actions
        )

        return rung_5


# test deliberate (behavior and timing)

# trigger the EscalationLadderReasoners percept engine (???)

# test take_next_action

# test heapification of reasoner.planned_actions

if __name__ == "__main__":
    test = EscalationLadderTest()
    test.test_rungs()
    test.test_deliberate_current_time()
    test.test_deliberate_jump_several_rungs()
    test.test_deliberate_future_time()