from typing import NamedTuple

class RomancerObject():

    '''This is the base class for objects in the ROMANCER environment.'''

    def __init__(self, environment, time):
        self.inbox = list() # list of messages awaiting processing
        self.outbox = list() # list of messages that have not yet been sent
        self.environment = enviornment # ROMANCEREnvironment instance containing object
        self.id = self.environment.register_object(self) # assign unique id to object
        # objects with children also need to register those children
        self.time = time # current time of simulated object
        self.history = list() # list of logpoints

        # self.dispositions = [self.environment.disposition_tree.set_disposition(self), self.environment.perception_engine.emplace(self)... ]


    def deliver_messages(self, messages):
        '''Place messages in object's inbox.'''
        for message in messages:
            self.inbox.append(message)


    def send_messages(self):
        '''Pass messages from outbox to environment so they can be routed to their appropriate recipients.'''
        self.environment.deliver_messages(outbox) # maybe this should send self-addressed messages directly to inbox


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
    

    def rewind(time):
        '''This method should use the object's history to revert to its state at time. As this base object has no state to manipulate, all it does is reset the object's time.'''
        self.time = time


    def forward_simulation(time):
        '''This method should evolve the object's state forward in time, logging changes as logpoints if necessary. Forward simulation can also generate messages.''' 
        if self.time > time:
            self.rewind(time)
        else:
            self.time = time


    def next_anticipated_disposition_change(self):
        '''This method should use the disposition nodes referenced in self.disposition and other available object state to predict the earliest future time at which the object will leave one of those nodes. Often this information will have been computed already and stored as a logpoint.

        As this base class cannot change state, it returns None.'''
        return None
