from supervisor import Supervisor
from watchlist import WatchlistItem


# define WatchlistItems

# Stop

class Stop(WatchlistItem):
    '''This WatchlistItem halts the supervisor once simulation is complete. It defines the simulated time at which simulation will be terminated.'''

    def process(self, supervisor):
        print('Simulation terminated at time = {}', supervisor.time)


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={})'.format(self.__class__.__name__, self.time)

# Pause

class Pause(WatchlistItem):
    '''This WatchlistItem pauses the supervisor in a way that permits it to be restarted.'''

    def process(self, supervisor):
        supervisor.paused = True

    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={})'.format(self.__class__.__name__, self.time)

# define functions used by SingleThreadSupervisor's dispatch table


class SingleThreadSupervisor(Supervisor):


    def __init__(self, environment=None, random_seed=12345):
        super().__init__(self, environment=None, random_seed=12345)
        self.paused = False # is supervisor currently paused?
        self.check_for_percepts = False # flag indicating whether percept-generating event may have occured
        self.dispatch_table = {} # dict of functions for processing messages


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the supervisor's inbox. It should return functions with an (obj, message) call signature. Raises an exception if no appropriate dispatch function is found.'''
        try:
            f = self.dispatch_table.get(message.messagetype)
        except KeyError:
            print('No dispatch found for message type:', message.messagetype)
        finally:
            return f
       


    def bring_watchlist_up_to_date(self):
        '''This method ensures that the lead item on the watchlist is in fact the next one that should be executed. It should work by checking the simulated time of the lead item on the watchlist and then asking relevant objects in the environment (agents, etc.) whether they will or might cause an event of interest in that timeframe.'''
        # check if already at watchlist item time
        next_time = self.watchlist.peek.time
        if self.environment.time = next_time: # no opportunity for next event not to be correct
            return None # nothing to do, watchlist is up to date
        # deterministic events?
        self.environment.deterministic_events_before_time(next_time) # SingleThreadSupervisor can simply tell environment to do this rather than sending message
        # this method should send messages regarding the next deterministic event(s) to the supervisor
        # if multiple deterministic events are scheduled for the same time, send them all
        # examine inbox to see if new deterministic events have been identified prior to next_time
        # if so, store them as possible_next_events, next_time == new_next_time
        
        # stochastic events?
        self.environment.stochastic_events_before_time(next_time) # SingleThreadSupervisor can simply tell environment to do this rather than sending message
        # this method should send messages regarding possible stochastic event(s) to the supervisor
        # sort possible stochastic events by time
        # use rng to test whether each possible stochastic event turns into a watchlist item
        # if so, this event becomes next watchlist item, next_time=that item's time
        # if no stochastic event has occured, then push the deterministic events in possible_next_events onto watchlist

        # advance simulation time to next_time
        self.environment.forward_simulation(next_time)
        

    def process_next_watchlist_item(self):
        '''This method processes the next item on the watchlist. It assumes that the watchlist is up to date and that enviornment state is synchronized to the same time as that event.'''
        item = self.watchlist.peek()
        item.process(self) # run code associated with WatchlistItem; this can cause arbitrary changes to environment and supervisor state
        self.logger(self.watchlist.pop()) # pop the just-processed item off of the watchlist and log it if desired
        if self.check_for_percepts:
            self.perceive_and_deliberate()
            self.check_for_percepts = False


    def perceive_and_deliberate(self):
        '''This method is supposed to be called as part of process_next_watchlist_item(), in cases where new percepts have been generated and agents need to deliberate about those percepts.'''
        pass


    def send_messages(self, messages):
        '''Send the messages in the supervisor's inbox to their intended recipients. Note that this does not cause either the supervisor or the environment to process any of those messages.'''
        for message in self.outbox:
            if recipient[0] == 1: # self-addressed
                self.inbox.append(message)
            # TODO: deliver messages with a unitary recipient directly to inboxes
            else:
                self.environment.inbox.append(message) # send message to environment for forwarding
                # Tell environment to send messages?


    def process_inbox(self):

        # check for current status message(s) and call appropriate submethod
        # but maybe bring_watchlist_up_to_date and process_next_watchlist_item should just
        # call those methods directly


    def run(self):
        while len(self.watchlist) > 0 and not self.paused: # loop as long as watchlist items remain and self.paused is False
            self.bring_watchlist_up_to_date() # ensure current head of watchlist is actual next event
            self.process_next_watchlist_item() # process next watchlist event
