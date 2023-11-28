from dispositiontree import 1DimensionalDispositionTree
import numpy as np

class Environment():

    def __init__(self, supervisor, disposition_tree, perception_engine):
        self.inbox = list() # list of messages awaiting processing
        self.outbox = list() # list of messages that have not yet been sent
        self.id = 2 # toplevel environment always has id of 1
        self.time = 0 # supervisor initializes to simulation time of 0
        self.supervisor = supervisor
        self.message_index = 1 # increments with each message to assign unique ids
        self.disposition_tree = disposition_tree
        self.perception_engine = perception_engine
        self.agents = list() # collection of objects (not  necessarily toplevel) in environment that possess agency
        self.contents = list() # collection of toplevel items in the simulated environment
        self.object_count = 2 # used to assign ids to new objects
        self.message_dispatch_table = dict() # dict used to map object ids to references--used for delivering messages
        

    def new_message_index(self):
        '''This method is used to obtain unique integer ids for messages.'''
        cur = self.message_index
        self.message_index += 1 # increase message index
        return cur


    def new_object_index(self):
        '''This method produces unique integer ids for registering objects.'''
        self.object_count += 1
        return self.object_count

    
    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the environment's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature.'''
        return lambda obj, message: None


    def deliver_messages(self, messages):
        '''Place messages in the inbox of the addressed recipient objects.'''
        for message in messages:
            if message.recipient[0] == 2: # self-addressed
                self.inbox.append(message)
            elif message.recipient[0] = 1: # supervisor
                self.supervisor.inbox.append(message)
            else: # all other messages
                self.message_dispatch_table[message.recipient[0]).inbox.append(message)

    def send_messages(self, messages):
        '''Send the messages in the supervisor's inbox to their intended recipients. Note that this does not cause either the supervisor or the environment to process any of those messages.'''
        for message in self.outbox:
            if recipient[0] == 2: # self-addressed
                self.inbox.append(message)
            else:
                self.environment.append(message) # send message to environment for forwarding


    def register_object(self, obj):
        new_id = self.new_object_index()
        obj.id = new_id
        self.message_dispatch_table[new_id] = obj
        return new_id


    def add_object(self, obj):
        pass


    def add_agent(self, agent):
        pass
