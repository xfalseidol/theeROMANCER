from typing import NamedTuple
from environment.loglist import Loglist
from numpy import rad2deg
from matplotlib.path import Path
from matplotlib.markers import MarkerStyle
import matplotlib.patheffects as pe


class RomancerObject():

    '''This is the base class for objects in the ROMANCER environment.'''

    def __init__(self, environment, time, location=None):
        self.inbox = list() # list of messages awaiting processing
        self.outbox = list() # list of messages that have not yet been sent
        # self.location = location
        self.environment = environment # ROMANCEREnvironment instance containing object
        self.uid = self.environment.register_object(self) # assign unique id to object
        self.message_index = 1 # increments with each message to assign unique ids
        # objects with children also need to register those children
        self.time = time # current time of simulated object
        self.loglist = Loglist() # list of logpoints
        self.repr_list = ['inbox', 'outbox', 'uid', 'message_index', 'time', 'loglist'] # used for __repr__ with keywords

        # self.dispositions = [self.environment.disposition_tree.set_disposition(self), self.environment.perception_engine.emplace(self)... ]

        
    def new_message_index(self):
        '''This method is used to obtain unique integer ids for messages.'''
        cur = self.message_index
        self.message_index += 1 # increase message index
        return cur

    
    def deliver_messages(self, messages):
        '''Place messages in object's inbox.'''
        for message in messages:
            self.inbox.append(message)


    def send_messages(self):
        '''Pass messages from outbox to environment so they can be routed to their appropriate recipients.'''
        self.environment.deliver_messages(self.outbox) # maybe this should send self-addressed messages directly to inbox
        self.outbox.clear()


    def get_children(self):
        '''Many items will have children. This method is supposed to return all children of all subsidiary objects recursively. As this default class has no children, it returns None.'''
        return None


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the object's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature.'''
        return lambda obj, message: None


    def process_inbox(self):
        '''This method acts on all the messages currently in the inbox using the functions returned by the dispatcher. These functions can alter the state of the object or its children, send one or more messages to various recipients, or simply be ignored.'''
        while len(self.inbox) > 0:
            message = self.inbox.pop()
            f = self.dispatcher(message)
            f(self, message)
        self.send_messages() # send outgoing messages if necessary
    

    def rewind(self, time):
        '''This method should use the object's history to revert to its state at time. As this base object has no state to manipulate, all it does is reset the object's time.'''
        self.time = time


    def forward_simulation(self, time):
        '''This method should evolve the object's state forward in time, logging changes as logpoints if necessary. Forward simulation can also generate messages.''' 
        if self.time > time:
            self.rewind(time)
        else:
            self.time = time


    def next_anticipated_disposition_change(self):
        '''This method should use the disposition nodes referenced in self.disposition and other available object state to predict the earliest future time at which the object will leave one of those nodes. Often this information will have been computed already and stored as a logpoint.

        As this base class cannot change state, it returns None.'''
        return None

        
    def plot(self, ax):
        print(f"Object {self.uid} does not have a location or does not know how to plot itself.")


    def __repr__(self):
        '''This method is designed to print representations useful in experimental programming on the repl.

        Printing the Environment is a problem as it contains recursive references. Maybe it should be defined to some convenient global name by default to make printing convenient?'''
        class_name = self.__class__.__name__
        results = {key: self.__getattribute__(key) for key in self.repr_list}
        return f"{class_name}({', '.join([f'{k}={v.__repr__()}' for k,v in results.items()])})"


class PlottableObject():
    id_counter = 0

    def __init__(self, location):
        self.location = location # GeographicLocation representing plane latitude, longitude, and bearing
        PlottableObject.id_counter += 1
        self.uid = PlottableObject.id_counter
        self.speed = 100 # km/hr
        self.time = 0


    def plot(self, ax):
        lon = rad2deg(self.location.longitude)
        lat = rad2deg(self.location.latitude)
        ber = rad2deg(self.location.bearing)
        triangle = Path([[-0.5, 0], [0.5, 0], [0, 0.5]])
        rotated_triangle = MarkerStyle(triangle).rotated(deg=-ber)
        ax.plot(lon, lat, marker=rotated_triangle, color='blue', markersize=11, linestyle='')
        txt = ax.text(lon, lat, self.uid,
              size=8,
              color='white',
              path_effects=[pe.withStroke(linewidth=1, foreground="black")])

 
    def __repr__(self):
        return "PlottableObject" + str(self.uid)
