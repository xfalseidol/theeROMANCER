from environment import Environment


class TemporalROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    time: float # simulation time

    
class SingleThreadEnvironment(Environment):

    def __init__(self, supervisor, disposition_tree, perception_engine):
        self.super().__init__(supervisor, disposition_tree, perception_engine)
        self.dispatch_table = {'DeterministicActionsBeforeTime': lambda o, m: o.deterministic_events_before_time(m.time)
                               'StochasticActionsBeforeTime': lambda o, m: 0.stochastic_events_before_time(m.time),
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                               } # dict of functions for processing messages


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the environment's inbox. It should return functions with an (obj, message) call signature. Raises an exception if no appropriate dispatch function is found.'''
        try:
            f = self.dispatch_table.get(message.messagetype)
        except KeyError:
            print('No dispatch found for message type:', message.messagetype)
        finally:
            return f


    def forward_simulation(self, time):
        '''Run forward simulation on all objects in the environment by recurising through the heirarchical representation. Objects with children are expected to advance the forward simulation of thise child items as part of their forward_simulation() method.'''
        for item in self.contents:
            item.forward_simulation(time)
        self.time = time


    def process_all_inboxes(self):
        
        def process_all_inboxes_inner(o):
            o.process_inbox()
            o.send_messages()
            self.deliver_messages(self.outbox)
            self.outbox.clear()
            try:
                children = o.children
            except AttributeError:
                children = []
            finally:
                for child in children:
                    process_all_inboxes_inner(child)
            
        for item in self.contents:
            process_all_inboxes_inner(item)
            

    def forward_to_all(self, messages):
        '''Send messages to every object in the envionment.'''

        def forward_to_all_inner(o):
            o.deliver_messages(messages)
            try:
                children = o.children
            except AttributeError:
                children = []
            finally:
                for child in children:
                    forward_to_all_inner(child)

        for item in self.contents:
            forward_to_all_inner(item)
            
        
    def deterministic_events_before_time(self, next_time):
        message = TemporalROMANCERMessage(uid=self.new_message_index(), sender=(self.uid, self.uid), recipient=(self.uid, 0), messagetype='DeterministicActionsBeforeTime', time=next_time)
        self.forward_to_all([message])
        self.process_all_inboxes()


    def stochastic_events_before_time(self, next_time):
        message = TemporalROMANCERMessage(uid=self.new_message_index(), sender=(self.uid, self.uid), recipient=(self.uid, 0), messagetype='StochasticActionsBeforeTime', time=next_time)
        self.forward_to_all([message])
        self.process_all_inboxes()


    


    
