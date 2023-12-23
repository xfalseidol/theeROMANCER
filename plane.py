from typing import NamedTuple
from environment.object import RomancerObject
from loglist import Logpoint

# Introducing the B-0: a plane that really, really sucks

class BZeroLogpoint(Logpoint):
    '''This logpoint is used to track the evolution of the state of the plane through time. For simplicity's sake it simply stores all plane variables that can change.'''

    def __init__(self, time, location, speed, ecm):
        self.time = time
        self.location = location
        self.speed = speed
        self.ecm = ecm


    def __repr__(self):
        return 'BZeroLogpoint(time={}, location={}, speed={}, ecm={})'.format(self.time, self.location, self.speed, self.ecm)


class TemporalROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    time: float # simulation time


class SpeedROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    speed: float # speed (km/hr)


def next_deterministic_action(o, m):
    '''This method sends a message to the supervisor indicating the time of the next deterministic action that the plane will take. As the only such action the plane can take on its own is traversing into a different disposition node, it simply sends a message indicating when this is predicated to take place.'''
    t = o.next_anticipated_disposition_change()
    message = TemporalROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(m.sender[0], m.sender[1]), messagetype='AnticipatedDispositionChange', time=t)
    self.outbox.append(message)


def stochastic_actions_before_time(o, m):
    pass

    
class BZero(RomancerObject):

    def __init__(self, environment, time, location, speed, ecm=False, granularity=100):
        super().__init__(environment, time) # set up standard object slots
        self.children = list() # pilot and red light go here
        self.location = location # one-dimensional, this plane can't steer!
        self.speed = speed # speed along trajectory in km/hr
        self.ecm = ecm # electronic countermeasures that can confound adversary radar; boolean
        self.granularity = granularity # used for disposition tree
        self.dispositions = [self.environment.disposition_tree.set_disposition(self, self.granularity)]
        self.dispatch_table = {'DeterministicActionsBeforeTime': next_deterministic_action, 
                               'StochasticActionsBeforeTime': lambda o, m: None,
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                               'ActivateECM': lambda o, m: o.activate_ecm(),
                               'DeactivateECM': lambda o, m: o.deactivate_ecm(),
                               'SetAircraftSpeed': lambda o, m: set_aircraft_speed(o, m.speed)
                               } # dict of functions for processing messages
        self.repr_list = super().repr_list + ['location', 'speed', 'ecm', 'granularity']
        # initial logpoint


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the plane's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature. Raises an exception if no appropriate dispatch function is found.'''
        f = self.dispatch_table.get(message.messagetype)
        if f:
            return f
        else:
            raise Exception('No dispatch set for ', message)


    def next_anticipated_disposition_change(self):
        '''Identify future time at which plane will leave its current disposition tree node based on its current speed and trajectory.'''
        low, high = self.dispositions[0].bounds
        if speed = 0: # disposition will never change
            return None
        elif speed > 0:
            delta_d = high - self.location
        else:
            delta_d = -(self.location - low) # convert to negative to match negative speed
        delta_t = delta_d / self.speed    
        return self.time + delta_t


    def update_disposition(self):
        '''Update the disposition of the plane. This method assumes that the time of the disposition change has already been identified with self.next_anticipated_disposition_change() and that the state of the plane has been evolved forward to that time using self.forward_simulation().'''
        cur = self.dispositions[0]
        self.dispositions[0] = self.environment.disposition_tree.adjust_disposition(self, self.granularity)
        if self.dispositions[0] is not cur:
            new_logpoint = BZeroLogpoint(time = self.time, location = self.location, speed = self.speed , ecm = self.ecm)
            self.loglist.append(new_logpoint)
        

    def forward_simulation(self, time):
        '''Evolve the plane's state forward in time. Except when rewinding, this ought not be called on an interval that will result in a changed disposition.'''
        delta_t = time - self.time
        new_location = self.location + self. speed * delta_t
        self.location = new_location
        self.time = time
        for child in self.children:
            child.forward_simulation(time)

        
    def rewind(self, time):
        '''Rewind the state of the B-0 to what it was at time using information stored in loglist.'''
        if self.time == time:
            pass
        low, high = self.loglist.temporal_bounds()
        elif low <= time:
            self.loglist.truncate_to_time(time) # maybe this shouldn't truncate
            latest = self.loglist[-1] # most recent logpoint < time
            self.time = latest.time # set plane time to logpoint time
            self.location = latest.location # set plane location to logpoint location
            self.speed = latest.speed # set plane speed to logpoint speed
            self.ecm = latest.ecm # set plane ecm to logpoint ecm
            self.forward_simulation(time)
            self.update_disposition(self) # reset plane disposition, if necessary


    def activate_ecm(self):
        if self.ecm:
            pass
        else:
            self.ecm = True
            new_logpoint = BZeroLogpoint(time = self.time, location = self.location, speed = self.speed , ecm = self.ecm)
            self.loglist.append(new_logpoint)


    def deactivate_ecm(self):
        if not self.ecm:
            pass
        else:
            self.ecm = False
            new_logpoint = BZeroLogpoint(time = self.time, location = self.location, speed = self.speed, ecm = self.ecm)
            self.loglist.append(new_logpoint)
        

    def set_aircraft_speed(self, speed):
        if speed = self.speed:
            pass
        else:
            self.speed = speed
            new_logpoint = BZeroLogpoint(time = self.time, location = self.location, speed = self.speed, ecm = self.ecm)
            self.loglist.append(new_logpoint)
        

class RedLightLogpoint(Logpoint):
    def __init__(self, time, blip_to_display):
        self.time = time
        self.on = on # bool

    
    def __repr__(self):
        return 'RedLightLogpoint(time={}, on={})'.format(self.time, self.on)

    
def red_light_stochastic_actions_before_time(o, m):
    
    messages = list()
    initial_time = peer.time
    peers = {d.peers() for d in self.dispositions} # Use disposition tree to identify objects radar might detect (e.g., plane)
    delta_t = 5.0 # 5 second detection interval
    times = list(range(o.time, m.time, delta_t))
    if self.on:
        for peer in peers:
            for t in times:
                if peer.__class__.__name__ == 'RedRadar':
                    peer.forward_simulation(t)
                    distance = abs(peer.location - o.location)
                    # check to see if adversary radar is now off or out of range and turn off light
                    if peer.on = False or distance > 250.0:
                        message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptRedLightOff', time=t, probability=0.95)
                        messages.append(message)
            peer.rewind(initial_time)
        # possibly turn off at random
        for t in times:
            message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptRedLightOff', time=t, probability=0.001)
            messages.append(message)
    else:
        # check to see if adversary radar is now on or in range and turn on light
        for peer in peers:
            for t in times:
                if peer.__class__.__name__ == 'RedRadar':
                    peer.forward_simulation(t)
                    distance = abs(peer.location - o.location)
                    # check to see if adversary radar is now on and in range and turn off light if so
                    if peer.on = True and distance < 250.0:
                        message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptRedLightOn', time=t, probability=0.95)
                        messages.append(message)
            peer.rewind(initial_time)
            # possibly turn on at random
        for t in times:
            message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptRedLightOn', time=t, probability=0.001)
            messages.append(message)
    self.send_messages(messages)

    
class RedLight(RomancerObject):
    '''This red light can turn on to indicate possible detection by adversary radar. It can also turn on by random chance due to stochastic malfunctions.'''
     def __init__(self, environment, time, location):
        super().__init__(environment, time) # set up standard object slots
        self.parent = None
        self.on = False # used to generate percept
        self.dispatch_table = {'DeterministicActionsBeforeTime': lambda o, m: None, # light generates no autonomous deterministic actions
                               'StochasticActionsBeforeTime': red_light_stochastic_actions_before_time,
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                               'RedLightOn': lambda o, m: o.red_light_on(),
                               'RedLightOff': lambda o, m: o.red_light_off()}
        self.repr_list = super().repr_list + ['parent', 'on']


    @property
    def location(self):
        '''The light is part of the plane, so its location is the same as that of the plane.'''
        return self.parent.location


    def red_light_on(self):
        if not self.on:
            self.on = True
            new_logpoint = RedLightLogpoint(time = self.time, on = self.on)
            self.loglist.append(new_logpoint)


    def red_light_off(self):
        if self.on:
            self.on = False
            new_logpoint = RedLightLogpoint(time = self.time, on = self.on)
            self.loglist.append(new_logpoint)
