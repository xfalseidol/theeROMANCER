from romancer.environment.object import ImprovedRomancerObject
from typing import NamedTuple
import math

class CurrentAmygdalaParameters(NamedTuple):
    current_pbf: float
    current_fight: float
    current_flight: float
    current_freeze: float
    current_dominant_response: any # can be 'fight', 'flight', 'freeze', or None


class UpdateAmygdalaParameters(NamedTuple):
    delta_pbf: float
    delta_fight: float
    delta_flight: float
    delta_freeze: float
    

class Amygdala(ImprovedRomancerObject):
    '''The purpose of this class is to represent the neuroendocrine and limbic systems in a modular way that can be employed with different kinds of reasoners within 'person-like' agents.

    As a rudimentary approximation of the neuroendocrine system, the Amygdala object provides a 'precious bodily fluid' parameter that represents the role of cortisol in human cognition. The reasoner can use the pbf level as a proxy for 'stress' or 'desperation', in turn using it to approximate resulting cognitive impairment. Cortisol is presumed to drop over time unless new stressors cause it to be replenished, and it can only rise up to a biological maximum represented by max_pbf.

    To represent 'lizard brain' types of responses, the Amygdala object provides proxies for fight, flight, or freeze responses. The agent's reasoner can either act on the basis of these responses or not as it sees fit. The reasoner also needs to incorporate funtionality to update these parameters on the basis of its evolving state--otherwise, they are ignored.
    '''

    def __init__(self, environment, time, fight_weight = 1.0, flight_weight = 1.0, freeze_weight = 1.0, initial_fight = 0.0, initial_flight = 0.0, initial_freeze = 0.0, initial_pbf = 0.0001, pbf_halflife = 100, max_pbf = 1.0, response_threshhold = 1.0):
        super().__init__(environment, time)
        self.fight_weight = fight_weight # used to update/predict fight response
        self.flight_weight = flight_weight # used to update/predict flight response
        self.freeze_weight = freeze_weight # used to update/predict freeze response
        self.fight = initial_fight # fight response level
        self.flight = initial_flight # flight response level
        self.freeze = initial_freeze # freeze response level
        self.pbf = initial_pbf # initial cortisol level
        self.last_pbf_update_time = self.time # used to calculate pbf decay
        self.pbf_decay_rate = (1 / math.log(2)) * pbf_halflife # rate at which cortisol is metabolized
        self.max_pbf = max_pbf # maximum possible cortisol level
        self.response_threshhold = response_threshhold # below this threshold, fight/flight/freeze responses do not activate ('business as usual')


    def current_amygdala_parameters(self):
        '''This method returns a CurrentAmygdalaParameters object reflecting the present cortisol level and dominant reseponse, if any. Not that it does not update and log self.pbf.'''
        delta_t = self.time - self.last_pbf_update_time # maybe check for negative value and raise exception if so
        cur_pbf = self.pbf * math.e**(-self.pbf_decay_rate * delta_t)
        # determine dominant response, if any
        responses = [('fight', self.fight * self.fight_weight), ('flight', self.flight * self.flight_weight), ('freeze', self.freeze * self.freeze_weight)]
        dominant_response = max(responses, key = lambda n: n[1])
        if cur_pbf < self.response_threshhold: # if unstressed
            dominant_response = None
        else: # otherwise, too stressed
            dominant_response = dominant_response[0]
        return CurrentAmygdalaParameters(current_pbf = cur_pbf, current_fight = self.fight * self.fight_weight, current_flight = self.flight * self.flight_weight, current_freeze = self.freeze * self.freeze_weight, current_dominant_response = dominant_response)
        
        
    def anticipated_parameters_at_time(self, time):
        '''As part of the agent's deliberation process, it needs to be able to anticipate the state of the amygdala at arbitrary points in the future prsuming no additional outside influences in the interim. This method returns a CurrentAmygdalaParameters object reflecting anticipated parameters at the future time, but leaves the Amygdala object at the same state as when it was called.'''
        if time == self.time:
            return self.current_amygdala_parameters() # return current state
        elif time < self.time: # may need this for deliberation
            cur_time = self.time
            self.rewind(time)
            state = self.current_amygdala_parameters() # return current state
            self.forward_simulation(cur_time) # revert state
            return state # return past state
        else:
            cur_time = self.time
            self.forward_simulation(cur_time)
            state = self.current_amygdala_parameters() # return current state
            self.rewind(cur_time) # revert state
            return state # return past state


    def update_parameters(self, parameters):
        '''The purpose of this method is to update the amygdala parameters that takes into account the decay of pbf while ensuring proper logging. Note that it returns the amygdala object to its initial time, while logging anticipated future changes if needed.'''
        # update parameters if needed
        update_parameters = parameters # UpdateAmygdalaParameters object
        cur_parameters = self.current_amygdala_parameters()
        if update_parameters.delta_pbf > 0:
            self.last_pbf_update_time = self.time
            self.pbf = cur_parameters.current_pbf + update_parameters.delta_pbf
            if self.pbf > self.max_pbf:
                self.pbf = self.max_pbf
        if update_parameters.delta_fight > 0:
            self.fight += update_parameters.delta_fight
        if update_parameters.delta_flight > 0:
            self.flight += update_parameters.delta_flight
        if update_parameters.delta_freeze > 0:
            self.freeze += update_parameters.delta_freeze

        self.last_pbf_update_time = self.time # update last pbf update time

    def dominant_response(self):
        dominant_response = self.current_amygdala_parameters().current_dominant_response
        return dominant_response