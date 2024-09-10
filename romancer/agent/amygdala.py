from romancer.environment.object import ImprovedRomancerObject
from typing import NamedTuple
import math
import matplotlib.pyplot as plt

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

    # Constants.
    FIGHT_STR = "fight"
    FLIGHT_STR = "flight"
    FREEZE_STR = "freeze"

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
        self.pbf_halflife = pbf_halflife # half-life of cortisol
        self.max_pbf = max_pbf # maximum possible cortisol level
        self.response_threshhold = response_threshhold # below this threshold, fight/flight/freeze responses do not activate ('business as usual')

        # Eventually capture from the logged object, but for now capture these synchronously as they change.
        self.plot_time = []
        self.plot_fight = []
        self.plot_flight = []
        self.plot_freeze = []
        self.plot_pbf = []
        self.capture_plot()

    def capture_plot(self):
        params = self.current_amygdala_parameters()
        self.plot_time.append(self.time)
        self.plot_fight.append(params.current_fight)
        self.plot_flight.append(params.current_flight)
        self.plot_freeze.append(params.current_freeze)
        self.plot_pbf.append(params.current_pbf)

    def export_plot(self, filename=None, title=None):
        if filename is None:
            filename = "amygdala.png"

        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.plot(self.plot_time, self.plot_fight, label="Fight", color="r")
        ax1.plot(self.plot_time, self.plot_flight, label="Flight", color="g")
        ax1.plot(self.plot_time, self.plot_freeze, label="Freeze", color="b")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Response")
        ax1.legend(loc="upper left")

        ax2 = ax1.twinx()
        ax2.plot(self.plot_time, self.plot_pbf, label="PBF", color="grey")
        ax2.set_ylabel("PBF")
        ax2.legend(loc="upper right")

        plt.title("Mood Meter" if title is None else title)
        plt.savefig(filename)
#        plt.show()


    def current_amygdala_parameters(self):
        '''This method returns a CurrentAmygdalaParameters object reflecting the present cortisol level and dominant reseponse, if any. Note that it does not update and log self.pbf.'''
        delta_t = self.time - self.last_pbf_update_time # maybe check for negative value and raise exception if so
        halflife_eps = 0.0000001
        if self.pbf_halflife < halflife_eps:
            self.pbf_halflife = halflife_eps
        cur_pbf = self.pbf * 2**(-delta_t / self.pbf_halflife)
        self.pbf = cur_pbf
        self.last_pbf_update_time = self.time
        # determine dominant response, if any
        responses = [(self.FIGHT_STR, self.fight * self.fight_weight),
                     (self.FLIGHT_STR, self.flight * self.flight_weight),
                     (self.FREEZE_STR, self.freeze * self.freeze_weight)]
        dominant_response = max(responses, key = lambda n: n[1])
        if cur_pbf > self.response_threshhold: # if too stressed
            dominant_response = dominant_response[0]
        else: # otherwise, not srtressed
            dominant_response = None
        current_fight = self.fight * self.fight_weight
        current_flight = self.flight * self.flight_weight
        current_freeze = self.freeze * self.freeze_weight
        params = CurrentAmygdalaParameters(current_pbf = cur_pbf, current_fight = self.fight * self.fight_weight, current_flight = self.flight * self.flight_weight, current_freeze = self.freeze * self.freeze_weight, current_dominant_response = dominant_response)
        # self.capture_plot(params)
        return params

        
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
        # cause the parameters to decay
        cur_parameters = self.current_amygdala_parameters()
        if update_parameters.delta_pbf != 0:
            self.last_pbf_update_time = self.time
            self.pbf = cur_parameters.current_pbf + update_parameters.delta_pbf
            # self.pbf += update_parameters.delta_pbf
            if self.pbf > self.max_pbf:
                self.pbf = self.max_pbf
            if self.pbf < 0:
                self.pbf = 0
        if update_parameters.delta_fight > 0:
            self.fight += update_parameters.delta_fight
        if update_parameters.delta_flight > 0:
            self.flight += update_parameters.delta_flight
        if update_parameters.delta_freeze > 0:
            self.freeze += update_parameters.delta_freeze
        self.capture_plot()
        self.last_pbf_update_time = self.time # update last pbf update time

    def dominant_response(self):
        dominant_response = self.current_amygdala_parameters().current_dominant_response
        return dominant_response


''' An Amygdala class that doesn't change over time'''
class FixedAmgydala(Amygdala):
    def update_parameters(self, parameters):
        # Override update so no responses change
        nothingupdate = UpdateAmygdalaParameters(0.0, 0.0, 0.0, 0.0)
        super().update_parameters(nothingupdate)

''' Fighter archetype '''
class Amygdala_Fight(FixedAmgydala):
    def __init__(self, environment, time):
        super().__init__(environment, time)
        self.fight_weight = 1.0
        self.flight_weight = 0.0
        self.freeze_weight = 0.0
        self.fight = 1.0
        self.flight = 0.0
        self.freeze = 0.0
        self.response_threshhold = -1.0

    def dominant_response(self):
        return self.FIGHT_STR

''' Runner archetype '''
class Amygdala_Flight(FixedAmgydala):
    def __init__(self, environment, time):
        super().__init__(environment, time)
        self.fight_weight = 0.0
        self.flight_weight = 1.0
        self.freeze_weight = 0.0
        self.fight = 0.0
        self.flight = 1.0
        self.freeze = 0.0
        self.response_threshhold = -1.0

    def dominant_response(self):
        return self.FLIGHT_STR


''' Runner archetype '''
class Amygdala_Freeze(FixedAmgydala):
    def __init__(self, environment, time):
        super().__init__(environment, time)
        self.fight_weight = 0.0
        self.flight_weight = 0.0
        self.freeze_weight = 1.0
        self.fight = 0.0
        self.flight = 0.0
        self.freeze = 1.0
        self.response_threshhold = -1.0

    def dominant_response(self):
        return self.FREEZE_STR

''' Purely Analytic brain feels no emotion '''
class Amygdala_StoneCold(FixedAmgydala):
    def __init__(self, environment, time):
        super().__init__(environment, time)
        self.fight_weight = 0.0
        self.flight_weight = 0.0
        self.freeze_weight = 0.0
        self.fight = 0.0
        self.flight = 0.0
        self.freeze = 0.0
        self.response_threshhold = 1e9

    def dominant_response(self):
        return None
