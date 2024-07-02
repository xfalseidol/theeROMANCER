from context import *
from romancer.agent.amygdala import Amygdala, CurrentAmygdalaParameters, UpdateAmygdalaParameters
import unittest

class AmygdalaTest(unittest.TestCase):
    sup = romancer.supervisor.SingleThreadSupervisor()
    env = romancer.SingleThreadEnvironment(sup, None, None)
    amygdala = Amygdala(env, env.time)

    def test_current_amygdala_parameters(self):
        # Test when all parameters are initialized to 0
        expected_params = CurrentAmygdalaParameters(0.0, 0.0, 0.0, 0.0, None)
        assert self.amygdala.current_amygdala_parameters() == expected_params

        # Test when parameters have non-zero values
        self.amygdala.current_pbf = 0.5
        self.amygdala.current_fight = 0.3
        self.amygdala.current_flight = 0.2
        self.amygdala.current_freeze = 0.1
        self.amygdala.current_dominant_response = 'fight'

        expected_params = CurrentAmygdalaParameters(0.5, 0.3, 0.2, 0.1, 'fight')
        assert self.amygdala.current_amygdala_parameters() == expected_params


    # test anticipated_parameters_at_time
    def test_anticipated_parameters_at_time(self):

        # Test when all parameters are initialized to 0
        expected_params = CurrentAmygdalaParameters(0.0, 0.0, 0.0, 0.0, None)
        assert self.amygdala.anticipated_parameters_at_time(0) == expected_params

        # Test when parameters have non-zero values
        self.amygdala.current_pbf = 0.5
        self.amygdala.current_fight = 0.3
        self.amygdala.current_flight = 0.2
        self.amygdala.current_freeze = 0.1
        self.amygdala.current_dominant_response = 'fight'

        # Test anticipated parameters after 1 time unit
        expected_params = CurrentAmygdalaParameters(0.5, 0.3, 0.2, 0.1, 'fight')
        assert self.amygdala.anticipated_parameters_at_time(1) == expected_params

        # Test anticipated parameters after 2 time units
        expected_params = CurrentAmygdalaParameters(0.5, 0.3, 0.2, 0.1, 'fight')
        assert self.amygdala.anticipated_parameters_at_time(2) == expected_params

        # Test anticipated parameters after 3 time units
        expected_params = CurrentAmygdalaParameters(0.5, 0.3, 0.2, 0.1, 'fight')
        assert self.amygdala.anticipated_parameters_at_time(3) == expected_params

        # Test anticipated parameters after 4 time units
        expected_params = CurrentAmygdalaParameters(0.5, 0.3, 0.2, 0.1, 'fight')
        assert self.amygdala.anticipated_parameters_at_time(4) == expected_params

        # Test anticipated parameters after 5 time units
        expected_params = CurrentAmygdalaParameters(0.5, 0.3, 0.2, 0.1, 'fight')
        assert self.amygdala.anticipated_parameters_at_time(5) == expected_params

        # Test anticipated parameters after 10 time units
        expected_params = CurrentAmygdalaParameters(0.5, 0.3, 0.2, 0.1, 'fight')
        assert self.amygdala.anticipated_parameters_at_time(10) == expected_params


    def test_update_parameters(self):       
        # Test when message is empty
        message = {}
        self.amygdala.update_parameters(message)

        # Check that parameters remain unchanged
        expected_params = CurrentAmygdalaParameters(0.0, 0.0, 0.0, 0.0, None)
        assert self.amygdala.current_amygdala_parameters() == expected_params

        # Test when message contains delta values
        message = {
            'delta_pbf': 0.1,
            'delta_fight': 0.2,
            'delta_flight': 0.3,
            'delta_freeze': 0.4
        }
        self.amygdala.update_parameters(message)

        # Check that parameters are updated correctly
        expected_params = CurrentAmygdalaParameters(0.1, 0.2, 0.3, 0.4, None)
        assert self.amygdala.current_amygdala_parameters() == expected_params

        # Test when message contains delta values and dominant response
        message = {
            'delta_pbf': -0.1,
            'delta_fight': 0.2,
            'delta_flight': -0.3,
            'delta_freeze': 0.4,
            'dominant_response': 'flight'
        }
        self.amygdala.update_parameters(message)

        # Check that parameters and dominant response are updated correctly
        expected_params = CurrentAmygdalaParameters(0.0, 0.4, 0.0, 0.8, 'flight')
        assert self.amygdala.current_amygdala_parameters() == expected_params


if __name__ == "__main__":
    test_class = AmygdalaTest()
    test_class.test_current_amygdala_parameters()
    test_class.test_anticipated_parameters_at_time()
    test_class.test_update_parameters()