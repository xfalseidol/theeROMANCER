from context import *
import networkx as nx
import matplotlib.pyplot as plt


def setup():
    sup = SingleThreadSupervisor()
    env = romancer.SingleThreadEnvironment(supervisor=sup, disposition_tree=None, perception_engine=None) # env is only needed to initialize TestImprovedRomancerObject
    cbr_agent = casebasedreasoner.cbr.CaseBasedReasoner(env, env.time)
    cbr_agent.add_mop(mop_name='M-ENEMY-DETECTED', absts={'M-EVENT'}, mop_type='mop')
    cbr_agent.add_mop(mop_name='I-M-E1-DETECTED', absts={'M-ENEMY-DETECTED'}, mop_type='instance')
    cbr_agent.add_mop(mop_name='I-M-E2-DETECTED', absts={'M-ENEMY-DETECTED'}, mop_type='instance')
    cbr_agent.add_mop(mop_name='M-FRIENDLY-DETECTED', absts={'M-EVENT'}, mop_type='mop')
    return env, sup, cbr_agent


class TestMOPandCBR:
    env, sup, cbr_agent = setup()


    def test_add_mop(self):
        # check self.cbr_agent.mops, that it contains the correct things
        assert False, "Not implemented"


    def test_get_sibling(self):
        pattern = ''
        mop = self.cbr_agent.mops['I-M-E1-DETECTED']
        expected_sibling = self.cbr_agent.mops['I-M-E2-DETECTED']
        actual_sibling = self.cbr_agent.get_sibling(pattern, mop)
        assert expected_sibling == actual_sibling, f"Expected {expected_sibling}, got {actual_sibling}"


    def test_revert_time(self):
        # make changes to the agent
        friendly1_detected = self.cbr_agent.add_mop(mop_name="I-M-F1-DETECTED", absts={'M-FRIENDLY-DETECTED'}, mop_type='instance')
        friendly2_detected = self.cbr_agent.add_mop(mop_name="I-M-F2-DETECTED", absts={'M-FRIENDLY-DETECTED'}, mop_type='instance')
        # advance time
        self.cbr_agent.forward_simulation(5.0)
        # make changes to the agent
        self.cbr_agent.remove_mop('I-M-F2-DETECTED')
        friendly3_detected = self.cbr_agent.add_mop(mop_name="I-M-F3-DETECTED", absts={'M-FRIENDLY-DETECTED'}, mop_type='instance')
        assert not 'I-M-F2-DETECTED' in self.cbr_agent.mops, f"I-M-F2-DETECTED in CBR MOPs but shouldn't be."
        assert 'I-M-F3-DETECTED' in self.cbr_agent.mops, f"I-M-F3-DETECTED not in CBR MOPs but should be."
        # revert time
        self.cbr_agent.rewind(4.0)
        assert 'I-M-F2-DETECTED' in self.cbr_agent.mops, f"I-M-F2-DETECTED not in CBR MOPs but should be."
        assert friendly2_detected in self.cbr_agent.mops['M-FRIENDLY-DETECTED'].specs, "I-M-F2-DETECTED not in M-FRIENDLY-DETECTED's specs"
        assert self.cbr_agent.mops['M-FRIENDLY-DETECTED'] in friendly2_detected.absts, "M-FRIENDLY-DETECTED not in I-M-F2-DETECTED's absts"
        assert not 'I-M-F3-DETECTED' in self.cbr_agent.mops, f"I-M-F3-DETECTED in CBR MOPs but shouldn't be."


    def test_add_filler(self):
        plane_mop = casebasedreasoner.cbr.MOP(environment=self.env, time=self.env.time, parent=None, mop_name='PLANE', absts={'M-ROOT'})
        pilot_mop = casebasedreasoner.cbr.MOP(environment=self.env, time=self.env.time, parent=None, mop_name='PILOT', absts={'M-ROOT'})
        plane_mop.add_role_filler('pilot', pilot_mop)
        assert ('pilot', pilot_mop) in plane_mop.slots.items()


    def test_remove_mop(self):
        # self.cbr_agent.remove_mop('M-ENEMY-DETECTED')
        # self.cbr_agent.remove_mop('M-EVENT')
        assert True == False, f"Not implemented"


    def test_is_abstraction(self):
        mop_name = 'M-ENEMY-DETECTED'
        mop = self.cbr_agent.mops[mop_name]
        result = mop.is_abstraction(self.cbr_agent.mops['M-EVENT']) # should be false
        assert not result, f"Expected False, got {result}"
        result = mop.is_abstraction(self.cbr_agent.mops['I-M-E1-DETECTED']) # should be true
        assert result, f"Expected True, got {result}"


    def test_calc_all_abstractions(self):
        expected = {self.cbr_agent.mops['M-EVENT'], self.cbr_agent.mops['M-ROOT'],}
        mop_name = 'M-ENEMY-DETECTED'
        actual = self.cbr_agent.mops[mop_name].calc_all_abstractions()
        assert expected == actual, f"Expected {expected}, but got {actual}"
        expected.add(self.cbr_agent.mops['M-ENEMY-DETECTED'])
        mop = self.cbr_agent.mops['I-M-E1-DETECTED']
        actual = mop.calc_all_abstractions()
        assert actual == expected, f"Expected {expected}, but got {actual}"


    def test_link_abst(self):
        # create a MOP
        # create another MOP
        # call link_abst from one to the other
        # check that the one MOP has the other in its absts
        # check that the other MOP has the one MOP in its specs
        assert False, "Not implemented"

    
    def test_unlink_abst(self):
        assert False, "Not implemented"


    def test_draw_graph(self):
        G = self.cbr_agent.get_graph()
        nx.draw_networkx(G)
        # plt.show()
