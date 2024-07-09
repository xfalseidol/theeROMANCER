from romancer.environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict
from romancer.agent.amygdala import UpdateAmygdalaParameters
from collections import UserList
from heapq import heapify, heappush, heappop
from scipy import optimize
import math
from collections import namedtuple


class EscalationLadder(UserList):
    '''The EscalationLadderReasoner stores its ontology in an instance of the EscalationLadder class. This is an ordered collection of Rung objects representing the ascending levels of escalation. The information about what internal perceptions (perception filter outpus) will cause the reasoner to match against these rungs and perceive that a particular rung of the escalation ladder has been reached is stored in the Rung objects, as are the actions that the reasoner considers appropriate at this rung of the escalation ladder given its intentions/internal state.

    Note that this EscalationLadder is not logged and is therefore meant to be treated as a static, unchanging object in the context of the simulation.

    A key purpose for the EscalationLadder class that is not yet implemented here is a visualization method.'''

    # default __init__ method is probably already sufficient here, although it might be appropriate to make it assert that the EscalationLadder contains only Rung objects

    def next_rung(self, current_rung):
        '''This method returns the next rung on the escalation ladder after current_rung, or None if current_rung is the top rung.'''
        cur_i = self.data.index(current_rung)
        try:
            next_rung = self.data[cur_i + 1]
        except IndexError:
            next_rung = None
        finally:
            return next_rung

    # for deliberating into the future
    def next_matched_rung(self, current_rung, reasoner, amygdala):
        matched = False
        next_rung = self.next_rung(current_rung)
        while next_rung:
            matched = next_rung.rung_matched(reasoner, amygdala)
            if matched:
                return next_rung
            next_rung = self.next_rung(next_rung)

    # for deliberaing present time
    def highest_matched_rung(self, current_rung, reasoner, amygdala):
        matched = False
        next_rung = self.next_rung(current_rung)
        highest_matched_rung = None
        while next_rung:
            matched = next_rung.rung_matched(reasoner, amygdala)
            current_rung = next_rung
            if matched:
                highest_matched_rung = next_rung
            next_rung = self.next_rung(current_rung)
        return highest_matched_rung


    def rung_number(self, rung):
        return self.data.index(rung) + 1
    

class EscalationLadderRung():
    '''Much of the logic of the EscalationLadderReasoner is stored in EscalationLadderRung instances. This permits these rungs to exhibit custom behavior if necessary.'''
    rung_id = 1

    def __init__(self, match_attributes, blue_actions, red_actions, blue_deescalation_actions, red_deescalation_actions, pbf_threshold = 1.0, amygdala_update=UpdateAmygdalaParameters(0, 0, 0, 0)):
        self.match_attributes = match_attributes # a sequence of patterns that are used to check whether agent believes that this rung has been reached
        self.pbf_threshold = pbf_threshold # what stress level would trigger this rung regardless of match_attributes
        self.red_actions = red_actions # collection of actions that reasoner believes Red will take at this rung, associated with amount of time that must pass before/between those actions
        self.blue_actions = blue_actions # collection of actions that reasoner believes Blue will take at this rung, associated with amount of time that must pass before/between those actions
        self.red_deescalation_actions = red_deescalation_actions # collection of actions that reasoner believes Red will take at this rung if it is attempting to de-escalate the situation, associated with amount of time that must pass before/between those actions
        self.blue_deescalation_actions = blue_deescalation_actions  # collection of actions that reasoner believes Blue will take at this rung if it is attempting to de-escalate the situation, associated with amount of time that must pass before/between those actions
        self.amygdala_update = amygdala_update 
        self.id = EscalationLadderRung.rung_id
        EscalationLadderRung.rung_id += 1

    def rung_matched(self, reasoner, amygdala):
        dominant_response = amygdala.dominant_response()
        if dominant_response == "freeze": # always escalate
            return False
        if dominant_response == "fight": # always escalate
            return True
        if dominant_response == "flight": # never escalate ??
            return False
        
        # ANY attribute in match_attributes matches a digested percept
        for attribute, value in self.match_attributes.items():
            for percept in reasoner.digested_percepts:
                try:
                    percept_value = getattr(percept, attribute)
                    if value == percept_value:
                        return True # an attribute matched
                except AttributeError:
                    pass # not a problem
        return False
    

    def coerce_attribues_to_matcher(self, attributes):
        '''This method uses the information stored in match_attributes to return a Python callable with an EscalationLadderReasoner, Amygdala call signature. Returns True if these attributes are met based on current state of reasoner and amygdala, False otherwise.'''
        def matcher(reasoner, amygdala_params): # possibly create lexical closure storing information for use by matcher
            return False

        return matcher


    def update_planned_actions(self, reasoner):
        '''This method mutates the passed reasoner's planned_actions attribute. Defaults to simply resetting planned action queue. This method assumes that all matchers associated with this rung have been evaluated.'''
        reasoner.planned_actions.clear()


    def untaken_actions(self, actions, reasoner):
        '''This method returns a set of actions that are not in the reasoner's actions_taken list. It may be handy to override this method to get more subtle, custom behavior from certain rungs.'''
        return set(reasoner.actions_taken).difference(actions)
        

    def enqueue_red_actions(self, reasoner):
        '''This method enqueues the red actions associated with this rung in the reasoner's action queue.'''
        for action in self.untaken_actions(self.red_actions, reasoner):
            reasoner.planned_actions.heappush((reasoner.time + action[0], action[1], reasoner.digested_percepts[-1].time))


    def enqueue_blue_actions(self, reasoner):
        '''This method enqueues the blue actions associated with this rung in the reasoner's action queue.'''
        for action in self.untaken_actions(self.blue_actions, reasoner):
            reasoner.planned_actions.heappush((reasoner.time + action[0], action[1], reasoner.digested_percepts[-1].time))


    def enqueue_red_deescalation_actions(self, reasoner):
        '''This method enqueues the red deescalation actions associated with this rung in the reasoner's action queue.'''
        for action in self.untaken_actions(self.red_deescalation_actions, reasoner):
            reasoner.planned_actions.heappush((reasoner.time + action[0], action[1], reasoner.digested_percepts[-1].time))


    def enqueue_blue_deescalation_actions(self, reasoner):
        '''This method enqueues the blue deescalation actions associated with this rung in the reasoner's action queue.'''
        for action in self.untaken_actions(self.blue_deescalation_actions, reasoner):
            reasoner.planned_actions.heappush((reasoner.time + action[0], action[1], reasoner.digested_percepts[-1].time))
    
    def __repr__(self):
        return "Rung " + str(self.id)
    

class EscalationLadderReasoner(ImprovedRomancerObject):
    '''
    '''

    def __init__(self,  environment, time, escalation_ladder, identity, current_rung = None, planned_actions = None, actions_taken = None, digested_percepts = None):
        super().__init__(environment, time)
        self.escalation_ladder = escalation_ladder # an EscalationLadder instance
        self.identity = identity # 'blue' or 'red'
        if current_rung and current_rung in self.escalation_ladder: # rung of escalation ladder agent believes represents current state of conflict
            self.current_rung = current_rung
        elif current_rung == None:
            self.current_rung = self.escalation_ladder[0]
        else:
            raise ValueError('Current rung not in EscalationLadder')
        if planned_actions: # should planned_actions be a logged UserList?
            self.planned_actions = planned_actions # planned_actions should be a list of (planned_action_time, action) tuples representing actions that the agent plans to take in the future. These can be provided out of chronological order as EscalationLadderReasoner will heapify them into a priority queue
            # WILL BINARY HEAP PRIORITY QUEUE WORK CORRECTLY WITH LoggedList?
        else:
            self.planned_actions = list()
        heapify(self.planned_actions) # ensure planned actions are heapified
        if actions_taken: 
            self.actions_taken = LoggedList(data = sorted(actions_taken, key = lambda p: p[0]), parent = self, varname = 'actions_taken') # actions taken sorted in ascending chronological time
        else:
            self.actions_taken = LoggedList(data = list(), parent = self, varname = 'actions_taken')
        if digested_percepts:
            self.digested_percepts = LoggedList(data = digested_percepts, parent = self, varname = 'digested_percepts')
        else:
            self.digested_percepts = LoggedList(data = list(), parent = self, varname = 'digested_percepts')
        self.max_deliberation_time = self.time # maximum time to which reasoner has deliberated; should this be unlogged?
        self.most_recent_percept_time = self.time

    def enqueue_digested_percept(self, digested_percept, percept_time):
        '''This method is used to update the EscalationLadderReasoner's internal state on the basis of the output of the egent's perception filter. What this does is enque the digested percept in the history of percepts digested by the reasoner, and update the reasoner's max_deliberation_time so that the next time that its deliberate method is called, its planned future actions will be recalculated if necessary.'''
        if percept_time < self.most_recent_percept_time:
            self.rewind(percept_time) # this
            self.max_deliberation_time = percept_time
            # what, if anything, should be done with planned_actions at this juncture?
            # presumably deliberate() should check if a new percept has been received since those actions were planned and then
            # edit planned actions accordingly
            # maybe add attr to EscalationLadderReasoner to act as flag for this, containing planned action most recent percept time?
            no_digested_percepts = len(self.digested_percepts)
            # pop self.digested_percepts until percepts are earlier than the  new digested percepts
            for i in range(no_digested_percepts):
                if self.digested_percepts.time > percept_time:
                    self.digested_percepts.pop()
                else:
                    break
            self.digested_percepts.append(digested_percept)
        elif percept_time == self.time: # this should be the case when the percept is the "next interesting event" processed by the supervisor
            self.max_deliberation_time = percept_time
            self.digested_percepts.append(digested_percept)

        if percept_time > self.most_recent_percept_time:
            self.most_recent_percept_time = percept_time

    def deliberate(self, max_time, amygdala):
        '''This method causes the agent to cogitate and predict how its mental state and intentions will evolve up until max_time in the future, presuming that it receives no additional percepts after the current time. One of the purposes of this method is to establish the evolution of the internal mental state of the agent. These changes can be stored on the loglist and then used to account for how a new percept can interrupt the agent's 'chain of thought.'
        '''
        pres_time = self.time

        # determine if a higher rung is matched now and escalate accordingly
        next_rung = self.escalation_ladder.highest_matched_rung(self.current_rung, self, amygdala)
        if next_rung:
            self.__escalate(next_rung, amygdala)
            return pres_time

        # determine if a higher rung will be matched in the future
        self.forward_simulation(max_time)
        amygdala.forward_simulation(max_time)
        next_rung = self.escalation_ladder.next_matched_rung(self.current_rung, self, amygdala)
        if next_rung: # there is a match in the future
            return self.__find_approximate_match_time(pres_time, max_time, next_rung, amygdala)
        self.max_deliberation_time = max_time


        # what is the point of this situation?
        # if max_time <= self.max_deliberation_time:
        #     self.forward_simulation(max_time)
        #     amygdala.forward_simulation(max_time)
        # else:
        #     amygdala.forward_simulation(pres_time) # advance amygdala to reasoner's time
        #     self.forward_simulation(self.pres_time) # replay all available future predicted cognition
        #     next_rung = self.escalation_ladder.next_rung(self.current_rung)
        #     matched = next_rung.rung_matched(reasoner=self, amygdala=amygdala) # ask the rung if this reasoner and amygdala satisfy the rung
        #     # note that the logic of how current pbf level affects matcher outcomes is located in the matchers
        #     if matched:
        #         self.__escalate(next_rung, amygdala)
        #     else: # check to see if we match in the future
        #         # max_time_parameters = amygdala.anticipated_parameters_at_time(max_time) # should probably just forward self and amygdala to max time here?
        #         # check to see if matchers fire at max_time; if one does, it implies that the monotonic decrease of pbf level is the determinant factor
        #         ## advance reasoner and amygdala to max time ??
        #         self.forward_simulation(max_time)
        #         amygdala.forward_simulation(max_time)
        #         matched_later = next_rung.rung_matched(reasoner=self, amygdala=amygdala)


        #         if matched_later: # this should only run very ocassionally
        #             self.rewind(pres_time) # rewind state to before when matcher fired, also rewind the amygdala?
        #             amygdala.rewind(pres_time)
        #             match_time = self.__find_approximate_match_time(amygdala)
        #             self.forward_simulation(match_time)
        #             self.deliberate(pres_time, amygdala) # this should enqueue appropriate actions as needed
        #             self.max_deliberation_time = match_time
        #             self.rewind(pres_time)
        # self.max_deliberation_time = max_time # update self.max_deliberation_time to reflect new deliberation
        # self.rewind(pres_time)

        
    @property
    def next_deliberate_action(self):
        if len(self.planned_actions):
            return peek(self.planned_actions)[1]
        else:
            return None


    @property
    def next_deliberate_action_time(self):
        if len(self.planned_actions):
            return peek(self.planned_actions)[0]
        else:
            return None

        
    def take_next_action(self):
        '''This method is meant to be called when a WatchListItem reflecting the agent's planned action is processed by the Supervisor. It should be an internal implementation detail which is called via a method on the PersonLikeAgent, which uses the values it returns to update the Amygdala state.'''
        action = heappop(self.planned_actions)
        self.forward_simulation(action_time) # make sure that Reasoner is at correct time, although in practice this should do nothing as forward_simulation should have been called on the Agent first
        # send message to supervisor reflecting action, if necessary
        self.actions_taken.push((action, action_time))
        return UpdateAmygdalaParameters(delta_pbf = action.delta_pbf, delta_fight = action.delta_fight, delta_flight = action.delta.flight, delta_freeze = action.delta_freeze) # the caller should use these to update the agent's amygdala parameters; much of the time taking action should reduce pbf, inclination to fight or flight


    def __escalate(self, next_rung, amygdala):
        next_rung.update_planned_actions(self)
        self.current_rung = next_rung
        Message = namedtuple('Message', ['time', 'parameters'])
        message = Message(time=self.time, parameters=next_rung.amygdala_update)
        amygdala.update_parameters(message) # increase pbf toaccount for stress of going up escalation ladder
        parameters = amygdala.current_amygdala_parameters()
        if parameters.current_dominant_response == 'fight':
            # match and/or escalate
            if self.identity == 'blue':
                next_rung.enqueue_blue_actions(self)
                # if sufficiently angry, escalate further
                # this implies that a sufficiently angry agent will escalate uncontrollably--which is presumably the point!
                if parameters.current_pbf > 0.95: # assign this to some sesible value relative to Amygdala configuration
                    self.current_rung = self.escalation_ladder.next_rung(self.current_rung)
            elif self.identity == 'red':
                next_rung.enqueue_red_actions(self)
                # if sufficiently angry, escalate further
                if parameters.current_pbf > 0.95: # assign this to some sesible value relative to Amygdala configuration
                    self.current_rung = self.escalation_ladder.next_rung(self.current_rung)
        elif parameters.current_dominant_response == 'flight':
            # try to de-escalate
            if self.identity == 'blue':
                # enqueue actions not yet taken
                next_rung.enqueue_blue_deescalation_actions(self)
            elif self.identity == 'red':
                next_rung.enqueue_red_deescalation_actions(self)
                # enqueue actions not yet taken



    def __find_approximate_match_time(self, pres_time, max_time, matched_rung, amygdala):
        def matched_at_time(t): # adjust objects to correct time, determine if there's a match
            if t < self.time:
                self.rewind(t)
                amygdala.rewind(t)
            elif t > self.time:
                self.forward_simulation(t)
                amygdala.forward_simulation(t)
            if matched_rung.rung_matched(self, amygdala):
                return 1
            else:
                return -1
        match_time = optimize.bisect(matched_at_time, pres_time, max_time)
        return match_time

