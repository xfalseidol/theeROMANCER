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
        assert 'I-M-F2-DETECTED' not in self.cbr_agent.mops, f"I-M-F2-DETECTED in CBR MOPs but shouldn't be."
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


    def test_slots_satisfied_by(self):
        m_range = self.cbr_agent.add_mop(mop_name='M-RANGE', absts={'M-PATTERN'}, mop_type='mop', slots={'abst_fn': range_constraint})

        veg = self.cbr_agent.add_mop(mop_name='M-VEGETABLE', absts={'M-ROOT'}, mop_type='mop', slots={'color': None, 'calories': self.cbr_agent.add_mop(mop_type='instance', absts={"M-RANGE"}, slots={'above': 0})})
        root_veg = self.cbr_agent.add_mop(mop_name='M-ROOT-VEGETABLE', absts={'M-VEGETABLE'}, mop_type='mop', slots={'depth': self.cbr_agent.add_mop(absts={"M-RANGE"}, slots={'below': 5}, mop_type='instance')})
        leafy_veg = self.cbr_agent.add_mop(mop_name='M-LEAFY-VEGETABLE', absts={'M-VEGETABLE'}, mop_type='mop', slots={'height': self.cbr_agent.add_mop(absts={"M-RANGE"}, slots={'below': 5}, mop_type='instance')})
        potato = self.cbr_agent.add_mop(mop_name='I-M-POTATO', absts={'M-ROOT-VEGETABLE'}, mop_type='instance', slots={'calories': 100, 'depth': 1})
        carrot = self.cbr_agent.add_mop(mop_name='I-M-CARROT', absts={'M-ROOT-VEGETABLE', 'M-LEAFY-VEGETABLE'}, mop_type='instance', slots={'calories': 50, 'depth': 2, 'height': 1})
        lettuce = self.cbr_agent.add_mop(mop_name='I-M-LETTUCE', absts={'M-LEAFY-VEGETABLE'}, mop_type='instance', slots={'calories': 10, 'height': 2})
        new_veg = self.cbr_agent.add_mop(absts={'M-VEGETABLE'}, mop_type='instance', slots={'calories': 200})
        new_veg2 = self.cbr_agent.add_mop(absts={'M-VEGETABLE'}, mop_type='instance', slots={'calories': 200, 'color': 'blue'})

        # print(leafy_veg.slots_satisfied_by(carrot)) # True
        # print(root_veg.slots_satisfied_by(carrot)) # True
        # print(root_veg.slots_satisfied_by(lettuce)) # False

        # what are other good tests that will determine whether slots_satisfied_by works correctly?
        # does lettuce satisfy the requirements of a root vegetable?

        # need tests for:
        # 1) No Constraint
        # color has no constraint, both new_veg and new_veg2 should satisfy veg:
        assert veg.slots_satisfied_by(new_veg), f"{new_veg} does not satisfy {veg}, but should."
        assert veg.slots_satisfied_by(new_veg2), f"{new_veg2} does not satisfy {veg}, but should."
        # 2) Pattern Constraint with abst_fn
        # veg with wrong value for calories
        veg_no_calories = self.cbr_agent.add_mop(mop_type='instance', absts={'M-VEGETABLE'}, slots={'calories': -10})
        assert not veg.slots_satisfied_by(veg_no_calories), f"{veg_no_calories} satisfies {veg}, but shouldn't."
        print("test over")
        # 3) Constraint is abstraction of Filler
        # 4) Constraint is Instance, Filler is None (?)
        # 5) Filler exists and Constraint is Satisfied by it (?)

def range_constraint(constraint, filler, slots):
        '''Assume filler is a number that can be compared against the constraint'''
        below = constraint.role_filler('below')
        above = constraint.role_filler('above')
        try:
            if below is not None:
                return filler < below
            if above is not None:
                return filler > above
        except:
            pass
        return False


if __name__ == "__main__":
    test_obj = TestMOPandCBR()
    test_obj.test_slots_satisfied_by()