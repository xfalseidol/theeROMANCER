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
    id: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    time: float # simulation time


class SpeedROMANCERMessage(NamedTuple):
    id: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    speed: float # speed (km/hr)


def next_deterministic_action(o, m):
    '''This method sends a message to the supervisor indicating the time of the next deterministic action that the plane will take. As the only such action the plane can take on its own is traversing into a different disposition node, it simply sends a message indicating when this is predicated to take place.'''
    t = o.next_anticipated_disposition_change()
    message = TemporalROMANCERMessage(id=o.new_message_index, sender=(o.environment.id, o.id), recipient=(m.sender[0], m.sender[1]), messagetype='AnticipatedDispositionChange', time=t)
    self.outbox.append(message)


def stochastic_actions_before_time(o, m):
    pass

    
class BZero(RomancerObject):

    def __init__(self, environment, time, location, speed, ecm=False, granularity=100):
        super().__init__(environment, time) # set up standard object slots
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

        
    def rewind(self, time):
        '''Rewind the state of the B-0 to what it was at time using information stored in loglist.'''
        if self.time == time:
            pass
        low, high = self.loglist.temporal_bounds()
        elif low <= time:
            self.loglist.truncate_to_time(time)
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
            new_logpoint = BZeroLogpoint(time = self.time, location = self.location, speed = self.speed , ecm = self.ecm)
            self.loglist.append(new_logpoint)
        

    def set_aircraft_speed(self, speed):
        if speed = self.speed:
            pass
        else:
            self.speed = speed
            new_logpoint = BZeroLogpoint(time = self.time, location = self.location, speed = self.speed , ecm = self.ecm)
            self.loglist.append(new_logpoint)
        
