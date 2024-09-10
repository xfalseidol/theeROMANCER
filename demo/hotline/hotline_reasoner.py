from romancer.agent.escalationladderreasoner import EscalationLadderRung, EscalationLadderReasoner
from typing import NamedTuple
from hotline_percept import SendPrivateMessage, SendPublicMessage, HotlineMessagePercept, HotlineActionPercept, HotlineActionROMANCERMessage, HotlinePublicROMANCERMessage, HotlineRungChangeMessage
from hotline_actions import DeterrentThreat, CompellentThreat, ConcessionOffer
from functools import reduce
from heapq import heappush, heappop
import matplotlib.pyplot as plt


# First, we define a mini-DSL for rung-matching rules
# These consist of Python immutables that are evaluated at runtime on the basis of reasoner state
# The DeterrentThreat, CompellentThreat, and ConcessionOffer classes from hotline_percept.py are also part of this mini-DSL,
# hence why they have a .eval(reasoner) method

# By nesting the terms of the DSL inside of one another, and adding new terms as necessary,one can produce *arbitrary* matching
# behavior.

# e.g. any_of((21, DeterrentThreat(23, 25, None),
#             all_of((CompellentThreat(31, 32, None),  min_adversary_resolve(0.75)))))
# matches if reasoner believes that action 21 has been taken, if it believes the adversary has threatened to retaliate with action
# 25 to action 23 (at any level of credibility), or if the adversary has made the threat to take action 32 unless the reasoner
# makes action 31, and the reasoner assesses the opponent's credibility at >= 0.75.


class any_of(tuple):

    def evaluate(self, reasoner, amygdala):
        '''Recursively evaluate contents of self until at least one top-level member evaluates to True. If a member is an integer, it is assumed to represent an action that the reasoner perceives to have been taken.'''

        taken_actions = set({percept.action_taken for percept in reasoner.digested_percepts if isinstance(percept, HotlineActionPercept)})

        def action_taken(n):
            return n in taken_actions

        # actions_taken = []  
        # for m in self:
        #     if isinstance(m, int):
        #         actions_taken.append(action_taken(m))
        #     else:
        #         actions_taken.append(m.evaluate(reasoner, amygdala))
        # return any(actions_taken)
        # returns true if any action m has been taken or if any other behavior m evaluates to true
        return any((action_taken(m) if isinstance(m, int) else m.evaluate(reasoner, amygdala) for m in self if isinstance(m, int)))


class all_of(tuple):
    
    def evaluate(self, reasoner, amygdala):
        '''Recursively evaluate contents of self, breaking if a top-level member evaluates False. Returns True if all top-level members return True. If a member is an integer, it is assumed to represent an action that the reasoner perceives to have been taken.'''

        taken_actions = set({percept.action_taken for percept in self.digested_percepts if isinstance(percept, HotlineActionPercept)})

        def action_taken(n):
            return n in taken_actions
        
        return all((action_taken(m) if isinstance(m, int) else m.evaluate(reasoner, amygdala) for m in self))


class min_adversary_resolve(NamedTuple):
    min_resolve: float

    def evaluate(self, reasoner, amygdala):
        '''Checks if current estimate of adversary resolve presently meets of exceeds self.min_resolve.'''
        return reasoner.perceived_adversary_resolve >= self.min_resolve
        

class HotlineLadderRung(EscalationLadderRung):
    '''match_attributes is assumed to be a statement in the matching DSL which as a .evaluate(reasoner, amygdala) method.'''

    
    def rung_matched(self, reasoner, amygdala):
        '''Assumes that self.match_attributes is a statement in the matching DSL.'''
        dominant_response = amygdala.dominant_response()
        if dominant_response == "freeze": # never escalate
            return False
        if dominant_response == "fight": # always escalate
            return True
        if dominant_response == "flight": # try to de-escalate
            return False
        
        return self.match_attributes.evaluate(reasoner, amygdala)


class HotlineLadderReasoner(EscalationLadderReasoner):

    def __init__(self,  environment, time, escalation_ladder, identity, current_rung = None, planned_actions = None, actions_taken = None, digested_percepts = None, resolve = 0.5, max_resolve = 1.0, perceived_adversary_resolve = 0.5, max_adversary_resolve = 1.0):
        super().__init__(environment, time, escalation_ladder, identity, current_rung, planned_actions, actions_taken, digested_percepts)
        self.resolve = resolve # set initial resolve
        self.max_resolve = max_resolve
        self.perceived_adversary_resolve = perceived_adversary_resolve # these values are analogous to pbf, fall within a defined range
        self.max_adversary_resolve = max_adversary_resolve
        self._fulfilled_threats = 0
        self._unfulfilled_expired_threats = 0
        self._fulfilled_open_ended_threats = 0
        self._no_adversary_concessions = 0

        self._plot_msg_send = []
        self._plot_msg_rcv = []
        self._plot_resolve = []
        self._plot_perceived_resolve = []

    def deliberate(self, max_time, amygdala):
        '''This method works mostly like the equivilent from the EscalationLadderReasoner, with the additional handling of updates to the reolve and perceived_adversary_resolve attributes.'''

        # Possibly push WatchlistItems to check for whether opponent keeps their word?
        # possibly call self.update_resolve()? This may be needed at startup of main simulation loop
        
        # now call the EscalationLadderReasoner's deliberate method--self.resolve and self.perceived_adversary_resolve are passed to next_matched_rung by its second parameter referring to the reasoner object
        super().deliberate(max_time, amygdala)


    def enqueue_digested_percept(self, digested_percept, percept_time):
        '''This works like the EscalationLadderReasoner's version of this method, except that it needs to account for updates to the reasoner's estimates of its own and its opponent's resolve based upon new Percepts.'''
        if percept_time < self.most_recent_percept_time:
            self.rewind(percept_time)
            self.max_deliberation_time = percept_time
            no_digested_percepts = len(self.digested_percepts)
            # pop self.digested_percepts until percepts are earlier than the  new digested percepts
            for i in range(no_digested_percepts):
                if self.digested_percepts.time > percept_time:
                    self.digested_percepts.pop()
                else:
                    break
            self.digested_percepts.append(digested_percept)
            # check to see if self.resolve and/or self.perceived_adversary_resolve need to be updated on the basis of new evidence
            # These may change considerably even if no rungs match or escalation/de-escalation do not occur
            self.update_resolve()
        elif percept_time == self.time: # this should be the case when the percept is the "next interesting event" processed by the supervisor
            self.max_deliberation_time = percept_time
            self.digested_percepts.append(digested_percept)
            self.update_resolve()

        if percept_time > self.most_recent_percept_time:
            self.most_recent_percept_time = percept_time


    def take_next_action(self):
        '''This method is meant to be called when a WatchListItem reflecting the agent's planned action is processed by the Supervisor. It should be an internal implementation detail which is called via a method on the PersonLikeAgent, which uses the values it returns to update the Amygdala state.'''
        action_time, action, params = heappop(self.planned_actions) # This should return an iterable of messages
        print(f"Taking action {action}")
        print(f" actions take: {self.actions_taken}")
        self.forward_simulation(action_time) # make sure that Reasoner is at correct time, although in practice this should do nothing as forward_simulation should have been called on the Agent first
        # send messages to supervisor reflecting actions, if necessary
        # actions = []
        # for message in messages:
        #     actions.append(message.actions)
        # if len(messages) > 0:
        #     self.environment.supervisor.inbox.clear() # should already be empty
        #     self.environment.supervisor.deliver_messages(messages)
        #     self.environment.supervisor.process_inbox() # all messages should be at the same time, otherwise would be separate actions
        #     self.environment.supervisor.inbox.clear() # remove action messages
        # self.actions_taken.append((action_time, action))
        return params

    def update_resolve(self):
        '''This method uses the reasoner's history of digested percepts to update its estimates of its own and its opponent's resolve.

        Resolve estimates can also be updated elsewhere for other reasons, such as when rungs match. This method is meant to update resolve estimates before those estimates are needed for rung-matching purposes.'''

        # For an initial effort, we can do a simple test for whether the opponent seems to engage in "cheap talk"
        # We allow estimated resolve to increase to some sort of asymptotic maximum on the basis of whether the opponent has ever
        # made good on their deterrent or compellent threats
        actions = {percept.action_taken for percept in self.digested_percepts if isinstance(percept, HotlineActionPercept)}
        messages = set()
        # messages = reduce(messages.add, [percept.messages for percept in self.digested_percepts if isinstance(percept, HotlineMessagePercept)])
        submessages = set()
        # submessages = reduce(submessages.add, [message.contents for message in messages])
        threats = filter(lambda m: isinstance(m, DeterrentThreat) or isinstance(m, CompellentThreat), submessages)
        # filter deterrent threats where provocation never took place
        threats = filter(lambda m: isinstance(m, DeterrentThreat) and m.provocation not in actions, threats)
        # filter compellent threats where demanded action was taken
        threats = filter(lambda m: isinstance(m, CompellentThreat) and m.demanded_action in actions, threats)
        if self.identity == 'red':
            adversary_threats = {threat for threat in threats if threat.threat % 2 != 0} # red actions assumed to be odd
        elif self.identity == 'blue':
            adversary_threats = {threat for threat in threats if threat.threat % 2 == 0} # blue actions assumed to be even
        open_ended_threats = {threat for threat in adversary_threats if not threat.deadline}
        expired_threats = {threat for threat in adversary_threats if threat.deadline and threat.deadline <= self.time}
        # add to adversary resolve based on number of fulfilled threats
        fulfilled_threats = len(actions & {threat.threat for threat in adversary_threats})
        delta_fulfilled = fulfilled_threats - self._fulfilled_threats
        delta_fulfilled_open_ended_threats = len(actions & {threat.threat for threat in open_ended_threats}) - self._fulfilled_open_ended_threats
        delta_unfulfilled_expired_threats = len({threat.threat for threat in expired_threats} - actions) - self._unfulfilled_expired_threats
        # We do an opposite adjustment on the basis of whether the opponent has ever made any concessions (resolve cannot fall below 0)
        concessions = filter(lambda m: isinstance(m, ConcessionOffer), submessages)
        if self.identity == 'red':
            adversary_concessions = [concession for concession in concessions if concession.quid % 2 != 0]
        elif self.identity == 'blue':
            adversary_concessions = [concession for concession in concessions if concession.quid % 2 == 0]
        delta_adversary_concessions = len(adversary_concessions) - self._no_adversary_concessions
        if delta_adversary_concessions != 0:
            self._no_adversary_concessions = len(adversary_concessions)
        delta_resolve = (delta_fulfilled_open_ended_threats - delta_fulfilled) * 0.3 + (delta_fulfilled - delta_fulfilled_open_ended_threats) * 0.1 - delta_unfulfilled_expired_threats * 0.1 - delta_adversary_concessions * 0.3
        if delta_resolve != 0.0:
            self.perceived_adversary_resolve = self.perceived_adversary_resolve + delta_resolve
            if self.perceived_adversary_resolve > self.max_adversary_resolve:
                self.perceived_adversary_resolve = self.max_adversary_resolve
            if self.perceived_adversary_resolve < 0:
                self.perceived_adversary_resolve = 0
        # Now for an analogous procedure to update the agent's own internal resolve. Unlike the estimate of adversary resolve, this is a "true" value
        # A simple way to implement this can be to use current Amygdala parameters to adjust an current float value
        # Fight responses increase resolve, Flight and Freeze responses reduce it
        # Higher pbf exaggerates these effects
        most_recent_params = self.digested_percepts[-1].amygdala_params
        delta_self_resolve = (most_recent_params.current_fight * 0.3 - most_recent_params.current_flight * 0.3 - most_recent_params.current_freeze * 0.2) * most_recent_params.current_pbf
        if delta_self_resolve != 0:
            self.resolve = self.resolve + delta_self_resolve
            if self.resolve > self.max_resolve:
                self.resolve = self.max_resolve
            elif self.resolve < 0:
                self.resolve = 0
        self._plot_resolve.append( (self.time, self.resolve) )
        self._plot_perceived_resolve.append((self.time, self.perceived_adversary_resolve) )

    def export_plot(self):
        filename = self.identity + "_resolve.png"
        fig, ax = plt.subplots(figsize=(10, 6))
        my_resolve_x = [tup[0] for tup in self._plot_resolve]
        my_resolve_x.append(self.environment.time)
        print(f"Time in reasoner during plot: {self.environment.time}")
        my_resolve_y = [tup[1] for tup in self._plot_resolve]
        my_resolve_y.append(my_resolve_y[-1])
        plt.step(my_resolve_x, my_resolve_y,
                 where="post", label="My Resolve", marker="o")

        their_resolve_x = [tup[0] for tup in self._plot_perceived_resolve]
        their_resolve_x.append(self.environment.time)
        their_resolve_y = [tup[1] for tup in self._plot_perceived_resolve]
        their_resolve_y.append(their_resolve_y[-1])
        plt.step(their_resolve_x, their_resolve_y ,
                 where="post", label="Perceived Resolve", marker="o")
        plt.xlabel("Time (s)")
        plt.ylabel("Resolve")
        plt.title(f"{self.identity} Resolve")
        ax.set_ylim(ymin=0)
        plt.legend()
        # plt.savefig(filename)
        plt.show()

        super().export_plot("escladder_" + filename, f"Escladder {self.identity}")
    
    def _escalate(self, next_rung, amygdala):
        previous_rung = self.current_rung
        super()._escalate(next_rung, amygdala)
        message = HotlineRungChangeMessage(uid=self.new_message_index(),
                                               time = self.time,
                                               sender=(self.environment.uid, self.compute_self_uid()),
                                               recipient=(1,1),
                                               messagetype='HotlineRungChangeMessage',
                                               old_rung=previous_rung,
                                               new_rung=self.current_rung)
        heappush(self.planned_actions, (self.time, message, None))


    def _deescalate(self, amygdala):
        super()._deescalate(amygdala)
        next_rung = self.escalation_ladder.next_rung(self.current_rung)
        message = HotlineRungChangeMessage(uid=self.new_message_index(),
                                               time = self.time,
                                               sender=(self.environment.uid, self.compute_self_uid()),
                                               recipient=(1,1),
                                               messagetype='HotlineRungChangeMessage',
                                               old_rung=next_rung,
                                               new_rung=self.current_rung)
        heappush(self.planned_actions, (self.time, message, None))

    def _enqueue_actions(self):
        '''Need to override this to account for more compact action descriptions.'''
        if self.identity == 'blue':
            actions = self.current_rung.blue_actions
        elif self.identity == 'red':
            actions = self.current_rung.red_actions

        # Loop through actions
        for action in actions:
            # action_messages = list()
            delta_t, action_or_message, update_params = action # unpack 3-tuple
            action_time = self.time + delta_t
            if isinstance(action_or_message, int): # Convert integers to actions
                action_message = HotlineActionROMANCERMessage(uid=self.new_message_index(),
                                                                    time=action_time,
                                                                    sender=(self.environment.uid, self.compute_self_uid()),
                                                                    recipient=(1, 1),
                                                                    messagetype = 'HotlineActionROMANCERMessage',
                                                                    action_id = action_or_message) # send action message to supervisor
            elif isinstance(action_or_message, SendPrivateMessage):
                action_message = action_or_message.coerce_to_message(uid=self.new_message_index(), time=action_time, sender=(self.environment.uid, self.compute_self_uid()), recipient=(1, 1), addressee=self.compute_opponent_uid())
            elif isinstance(action_or_message, SendPublicMessage):
                action_message = action_or_message.coerce_to_message(uid=self.new_message_index(), time=action_time, sender=(self.environment.uid, self.compute_self_uid()), recipient=(1, 1))
            else:
                action_message = action_or_message.coerce_to_message(**{'uid': self.new_message_index(), 'time': action_time, 'sender': (self.environment.uid, self.compute_self_uid()), 'recipient': (1, 1)})
            heappush(self.planned_actions, (action_time, action_message, update_params))
    

    def _enqueue_deescalation_actions(self):
        '''Need to override this to account for more compact action descriptions.'''
        if self.identity == 'blue':
            actions = self.current_rung.blue_deescalation_actions
        elif self.identity == 'red':
            actions = self.current_rung.red_deescalation_actions

        # Loop through actions
        for action in actions:
            action_messages = list()
            delta_t, action_or_message, update_params = action # unpack 3-tuple
            action_time = self.time + delta_t
            if isinstance(action_or_message, int): # Convert integers to actions
                action_message = HotlineActionROMANCERMessage(uid=self.new_message_index(),
                                                                    time=action_time,
                                                                    sender=(self.environment.uid, self.compute_self_uid()),
                                                                    recipient=(1, 1),
                                                                    messagetype = 'HotlineActionROMANCERMessage',
                                                                    action_id = action_or_message) # send action message to supervisor
                heappush(self.planned_actions, (action_time, action_message, update_params))
            # else:
            #     action_message = action_or_message.coerce_to_message(**{'uid': self.new_message_index(), 'time': action_time, 'sender': (self.environment.uid, self.compute_self_uid()), 'recipient': (1, 1)})
            # elif isinstance(action_or_message, SendPrivateMessage) or isinstance(action_or_message, SendPublicMessage):
            #     action_message = action_or_message.coerce_to_message(uid=self.new_message_index(), time=action_time, sender=(self.environment.uid, self.compute_self_uid()), recipient=(1, 1), addressee=self.compute_opponent_uid())


    def compute_opponent_uid(self):
        # quick and dirty: assume only two agents exist in simulation; return uid for other
        for agent in self.environment.agents:
            if agent.reasoner.identity != self.identity:
                return agent.uid


    def compute_self_uid(self):
        for agent in self.environment.agents:
            if agent.reasoner.identity == self.identity:
                return agent.uid
