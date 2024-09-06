import context
from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor, Stop
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from romancer.environment.location import GeographicLocation
from romancer.environment.dispositiontree import GeographicDispositionStump
from romancer.agent.amygdala import UpdateAmygdalaParameters, Amygdala
from romancer.agent.personlikeagent import push_personlike_action
from romancer.agent.escalationladderreasoner import EscalationLadder
from romancer.agent.escalationladderagent import EscalationLadderAgent
from hotline_reasoner import HotlineLadderRung, HotlineLadderReasoner, any_of, all_of, min_adversary_resolve
from hotline_percept import HotlinePerceptionEngine, HotlinePerceptionFilter, SendPrivateMessage, SendPublicMessage, HotlineActionROMANCERMessage, HotlinePrivateROMANCERMessage, HotlinePublicROMANCERMessage
from hotline_actions import DeterrentThreat, CompellentThreat, ConcessionOffer, hotline_action_dispatcher, hotline_public_message_dispatcher, hotline_private_message_dispatcher, hotline_deliberate_action, hotline_deterministic_action, hotline_rung_change_dispatcher
from numpy import deg2rad, rad2deg


# TODO: 
# 1. and test implement SendPublicMessage, SendPrivateMessage
# 2. test any_of, all_of, HotlineRung
# 3. write translation dictionary for action-description
# 4. implement "script generation" of the simulation:
### - write custom print/log behavior that logs interactions: "RED: Do this or I'll do this.", "BLUE: I concede, I'll do this."

# We assume that the universe of possible actions is represented by a set of unique integers {1, ... 60}
# We should add a mechanism for associating these numbers with human-readable descriptions, but that isn't essential to get this
# initial demo working.

# Each action is associated with one of the two sides (red can take odd-numbered actions, blue can take even-numbered actions)
# Actions can also be of different types. The first group consists of punishments or costs that can be imposed upon the opponent
# (e.g., attacking them with nuclear weapons.) The second consists of actions that the agent might be compelled to take by the
# opponent (e.g., retreating from a position). The third are possible concessions that the agent might make to the opponent. These
# might be the same things as the compelled actions (e.g., retreating from the same position), but because it is psychologically
# very different to do something because one freely chose to and to do the same thing because someone coerced one to, we treat them
# as distinct for the purposes of matching actions.

# We keep these three categories distinct by alternating them: 1 and 2 are threatened punishments by Red and Blue respectively, 3
# and 4 are compelled actions, 5 and 6 are possible concessions, after which the pattern repeats. To give flexibility in designing
# alternative ladders, we assume the pattern repeats twice per ladder rung ({1, ... 12} is the first rung, {13, ..., 24} is the
# second, and so on)

# To start we construct two mirror-imaged escalation ladders:

red_rung_1 = HotlineLadderRung(match_attributes = any_of([1, 2, 7, 8,
                                                          DeterrentThreat(14, 13, None),
                                                          all_of((DeterrentThreat(20, 19, None), min_adversary_resolve(0.85))),
                                                          all_of((CompellentThreat(2, 3, None), min_adversary_resolve(0.5))),
                                                          all_of((CompellentThreat(8, 9, None), min_adversary_resolve(0.2))),
                                                          DeterrentThreat(13, 14, None),
                                                          all_of((DeterrentThreat(19, 20, None), min_adversary_resolve(0.85))),
                                                          all_of((CompellentThreat(4, 1, None), min_adversary_resolve(0.5))),
                                                          all_of((CompellentThreat(10, 7, None), min_adversary_resolve(0.2)))]), # the characteristics mapped from the percepts the agent has digested that map to this rung
                                red_actions = [(1000, SendPublicMessage(DeterrentThreat(14, 13, None)), UpdateAmygdalaParameters(0.1, 0.1, 0, 0)),
                                               (2000, 1, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)),
                                               (10000, SendPrivateMessage(DeterrentThreat(20, 19, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0)),
                                               (20000, 7, UpdateAmygdalaParameters(0.2, 0.3, 0, 0))], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_actions = [(1000, SendPublicMessage(DeterrentThreat(13, 14, None)), UpdateAmygdalaParameters(0.1, 0.1, 0, 0)),
                                               (2000, 2, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)),
                                               (10000, SendPrivateMessage(DeterrentThreat(19, 20, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0)),
                                               (20000, 8, UpdateAmygdalaParameters(0.2, 0.3, 0, 0)),], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(6, 5, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (25000, 6, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(12, 11, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 12, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(5, 6, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (25000, 5, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(11, 12, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 11, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Low-level theater conventional conflict")
    

blue_rung_1 = red_rung_1 # mirror-imaged rung can literally be same object!


# here's the flow when an agent takes 
red_rung_2 = HotlineLadderRung(match_attributes = any_of([13, 14, 19, 20,
                                                          DeterrentThreat(26, 25, None),
                                                          all_of((DeterrentThreat(31, 32, None), min_adversary_resolve(0.85))),
                                                          all_of((CompellentThreat(15, 14, None), min_adversary_resolve(0.5))),
                                                          all_of((CompellentThreat(21, 20, None), min_adversary_resolve(0.2))),
                                                          DeterrentThreat(25, 26, None),
                                                          all_of((DeterrentThreat(32, 31, None), min_adversary_resolve(0.85))),
                                                          all_of((CompellentThreat(16, 13, None), min_adversary_resolve(0.5))),
                                                          all_of((CompellentThreat(22, 19, None), min_adversary_resolve(0.2)))]), # the characteristics mapped from the percepts the agent has digested that map to this rung
                                red_actions = [(1000, SendPublicMessage(DeterrentThreat(26, 25, None)), UpdateAmygdalaParameters(0.1, 0.1, 0, 0)),
                                                (2000, 13, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)),
                                                (10000, SendPrivateMessage(DeterrentThreat(32, 31, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0)),
                                                (20000, 25, UpdateAmygdalaParameters(0.1, 0.2, 0, 0))], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_actions = [(1100, SendPublicMessage(DeterrentThreat(25, 26, None)), UpdateAmygdalaParameters(0.1, 0.1, 0, 0)),
                                                (2000, 14, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)),
                                                (10000, SendPrivateMessage(DeterrentThreat(31, 32, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0)),
                                                (20000, 20, UpdateAmygdalaParameters(0.6, 0.3, 0.3, 0))], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(18, 17, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (25000, 18, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(24, 23, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 24, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(17, 18, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (25000, 17, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(23, 24, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 23, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Mid-level theater conventional conflict")


blue_rung_2 = red_rung_2

# repeat this pattern for rungs 3-5

red_rung_3 = HotlineLadderRung(match_attributes = any_of([25, 26, 31, 32,
                                                          DeterrentThreat(38, 37, None),
                                                          all_of((DeterrentThreat(43, 44, None), min_adversary_resolve(0.85))),
                                                          all_of((CompellentThreat(27, 26, None), min_adversary_resolve(0.5))),
                                                          all_of((CompellentThreat(33, 32, None), min_adversary_resolve(0.2))),
                                                          DeterrentThreat(37, 38, None),
                                                          all_of((DeterrentThreat(44, 43, None), min_adversary_resolve(0.85))),
                                                          all_of((CompellentThreat(28, 25, None), min_adversary_resolve(0.5))),
                                                          all_of((CompellentThreat(34, 31, None), min_adversary_resolve(0.2)))]), # the characteristics mapped from the percepts the agent has digested that map to this rung
                                red_actions = [(1000, SendPublicMessage(DeterrentThreat(38, 37, None)), UpdateAmygdalaParameters(0.1, 0.1, 0, 0)),
                                                (2000, 25, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)),
                                                (10000, SendPrivateMessage(DeterrentThreat(44, 43, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0)),
                                                (20000, 31, UpdateAmygdalaParameters(0.2, 0.3, 0, 0))], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_actions = [(1000, SendPublicMessage(DeterrentThreat(37, 38, None)), UpdateAmygdalaParameters(0.1, 0.1, 0, 0)),
                                                (2000, 26, UpdateAmygdalaParameters(0.2, 0.2, 0, 0)), # this really scares Blue agent
                                                (10000, SendPrivateMessage(DeterrentThreat(43, 44, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0)),
                                                (20000, 32, UpdateAmygdalaParameters(0.2, 0.3, 0, 0))], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(30, 29, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (25000, 30, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(36, 35, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 36, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(29, 30, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (25000, 29, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(35, 36, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 35, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "High-level theater conventional conflict")


blue_rung_3 = red_rung_3


red_rung_4 = HotlineLadderRung(match_attributes = any_of([37, 38, 43, 44,
                                                          DeterrentThreat(50, 49, None),
                                                          all_of((DeterrentThreat(55, 56, None), min_adversary_resolve(0.5))),
                                                          all_of((CompellentThreat(39, 38, None), min_adversary_resolve(0.5))),
                                                          all_of((CompellentThreat(45, 44, None), min_adversary_resolve(0.2))),
                                                          DeterrentThreat(49, 50, None),
                                                          all_of((DeterrentThreat(56, 55, None), min_adversary_resolve(0.5))),
                                                          all_of((CompellentThreat(40, 37, None), min_adversary_resolve(0.5))),
                                                          all_of((CompellentThreat(46, 43, None), min_adversary_resolve(0.2)))]), # the characteristics mapped from the percepts the agent has digested that map to this rung
                                red_actions = [(1000, SendPublicMessage(DeterrentThreat(50, 49, None)), UpdateAmygdalaParameters(0.1, 0.1, 0, 0)),
                                                (2000, 37, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)),
                                                (10000, SendPrivateMessage(DeterrentThreat(56, 55, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0)),
                                                (20000, 43, UpdateAmygdalaParameters(0.2, 0.3, 0, 0))], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_actions = [(1000, SendPublicMessage(DeterrentThreat(49, 50, None)), UpdateAmygdalaParameters(0.1, 0.1, 0, 0)),
                                                (2000, 38, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)),
                                                (10000, SendPrivateMessage(DeterrentThreat(55, 56, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0)),
                                                (20000, 44, UpdateAmygdalaParameters(0.2, 0.3, 0, 0))], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(42 ,41, None)), UpdateAmygdalaParameters(-1.0, -0.5, 0.5, 0.2)),
                                                             (25000, 42, UpdateAmygdalaParameters(-1.0, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(48, 47, None)), UpdateAmygdalaParameters(-0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 48, UpdateAmygdalaParameters(-0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(41, 42, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (25000, 41, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(47, 48, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 47, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Limited homeland conventional and limited theater nuclear conflict")


blue_rung_4 = red_rung_4


red_rung_5 = HotlineLadderRung(match_attributes = any_of([49, 50, 55, 56,
                                                          all_of((DeterrentThreat(55, 56, None), min_adversary_resolve(0.85))),
                                                          all_of((CompellentThreat(51, 50, None), min_adversary_resolve(0.7))),
                                                          all_of((CompellentThreat(57, 56, None), min_adversary_resolve(0.5))),
                                                          all_of((DeterrentThreat(56, 55, None), min_adversary_resolve(0.85))),
                                                          all_of((CompellentThreat(52, 49, None), min_adversary_resolve(0.7))),
                                                          all_of((CompellentThreat(58, 55, None), min_adversary_resolve(0.5)))]), # the characteristics mapped from the percepts the agent has digested that map to this rung
                                blue_actions = [(2000, 50, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)), 
                                                (20000, 56, UpdateAmygdalaParameters(0.7, 0.3, 2.0, 0))], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                red_actions = [(2000, 49, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)),
                                               (20000, 55, UpdateAmygdalaParameters(0.2, 0.3, 0, 0))], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(54, 53, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (25000, 54, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(60, 59, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 60, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(53, 54, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (25000, 53, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(59, 60, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 59, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Large-scale nuclear and conventional conflict")


blue_rung_5 = red_rung_5

red_ladder_1 = EscalationLadder([red_rung_1, red_rung_2, red_rung_3, red_rung_4, red_rung_5])

blue_ladder_1 = EscalationLadder([blue_rung_1, blue_rung_2, blue_rung_3, blue_rung_4, blue_rung_5])

# use these ladders to construct two opposing HotlineReasoners

# from this point forward analogous to escalation ladder demo
# STEP 1: Make supervisor
# Note that the supervisor as initialized here does not have its environment set; need to set it once environment is created

start_time = 0.0

sup = SingleThreadSupervisor()
# Step 1.2: Configure logger
def hotline_logger(s):
    print(s)
    # print()

sup.logger = hotline_logger

# set dispatch functions for HotlineActionROMANCERMessage, HotlinePublicROMANCERMessage, HotlinePrivateROMANCERMessage
# dispatch value needs to be a dispatch function:
## dispatch_function(sup, message) -> WatchlistItem
## Flow: something creates a message, the supervisor dispatches the message (by the dispatcher creating a watchlist item), 
## the watchlist item goes on the watchlist, and gets processed in the simulation and may generate a percept, which may cause agents to deliberate,
## which may cause agents to take an action / send a message
sup.dispatch_table['HotlineActionROMANCERMessage'] = hotline_action_dispatcher
sup.dispatch_table['HotlinePublicROMANCERMessage'] = hotline_public_message_dispatcher
sup.dispatch_table['HotlinePrivateROMANCERMessage'] = hotline_private_message_dispatcher
sup.dispatch_table['HotlineRungChangeMessage'] = hotline_rung_change_dispatcher
# sup.dispatch_table['PersonlikeActionROMANCERMessage'] = push_personlike_action
sup.watchlist.push(Stop(time=1.21e6)) # Stop at 1.21e6 seconds (about two weeks)

min_lat = deg2rad(-180)
max_lat = deg2rad(180)
min_long = deg2rad(-180)
max_long = deg2rad(180)

stump = GeographicDispositionStump(bounds = (min_lat, max_lat, min_long, max_long)) # whole Earth

engine = HotlinePerceptionEngine()

env = SingleThreadEnvironment(supervisor=sup, disposition_tree=stump, perception_engine=engine)
sup.environment = env
engine.environment = env

red_fight_weight = 1.0
red_flight_weight = 1.0
red_freeze_weight = 1.0
red_initial_fight = 0.0
red_initial_flight = 0.0
red_initial_freeze = 0.0
red_initial_pbf = 0.0001
red_pbf_halflife = 100.0
red_max_pbf = 1.0
red_response_threshhold = 0.7    

red_amygdala = Amygdala(environment = env, time = env.time, fight_weight = red_fight_weight, flight_weight = red_flight_weight,
                        freeze_weight = red_freeze_weight, initial_fight = red_initial_fight, initial_flight = red_initial_flight,
                        initial_freeze = red_initial_freeze, initial_pbf = red_initial_pbf, pbf_halflife = red_pbf_halflife,
                        max_pbf = red_max_pbf, response_threshhold = red_response_threshhold)

red_cur_rung = None # change to different rung to start above bottom of escalation ladder (implicitly rung1)
red_planned_actions = [(1000, 13, None), (25000, 31, None)] # change to force planned red actions, this will be heapified so it needs to be (time, action) tuples
red_actions_taken = None # change to give Red NCA history of actions taken
red_digested_percepts = None # change to give Red NCA history of digested percepts

red_reasoner = HotlineLadderReasoner(environment = env, time = env.time, escalation_ladder = red_ladder_1, identity = 'red', current_rung = red_cur_rung, planned_actions = red_planned_actions, actions_taken = red_actions_taken, digested_percepts = red_digested_percepts)

red_perception_filter = HotlinePerceptionFilter(agent=None, known = {i for i in range(61)}, substitutions = {}, wildcard=-1)

red_nca = EscalationLadderAgent(environment = env, time = start_time, perception_filter = red_perception_filter, amygdala = red_amygdala, reasoner = red_reasoner, name="Red NCA")
# red_nca.dispatch_table['NextDeliberateAction'] = hotline_deliberate_action
red_nca.dispatch_table['DeterministicActionsBeforeTime'] = hotline_deterministic_action
red_perception_filter.agent = red_nca
env.register_object(red_nca)
env.add_agent(red_nca)


blue_fight_weight = 1.0
blue_flight_weight = 2.0
blue_freeze_weight = 1.0
blue_initial_fight = 0.0
blue_initial_flight = 0.0
blue_initial_freeze = 0.0
blue_initial_pbf = 0.0001
blue_pbf_halflife = 100000.0
blue_max_pbf = 1.0
blue_response_threshhold = 0.2 # this is the *only* difference between Red and Blue NCAs!  

blue_amygdala = Amygdala(environment = env, time = env.time, fight_weight = blue_fight_weight, flight_weight = blue_flight_weight,
                        freeze_weight = blue_freeze_weight, initial_fight = blue_initial_fight, initial_flight = blue_initial_flight,
                        initial_freeze = blue_initial_freeze, initial_pbf = blue_initial_pbf, pbf_halflife = blue_pbf_halflife,
                        max_pbf = blue_max_pbf, response_threshhold = blue_response_threshhold)

blue_cur_rung = None # change to different rung to start above bottom of escalation ladder (implicitly rung1)
blue_planned_actions = [] # change to force planned blue actions, this will be heapified so it needs to be (time, action) tuples
blue_actions_taken = None # change to give Blue NCA history of actions taken
blue_digested_percepts = None # change to give Blue NCA history of digested percepts

blue_reasoner = HotlineLadderReasoner(environment = env, time = env.time, escalation_ladder = blue_ladder_1, identity = 'blue', current_rung = blue_cur_rung, planned_actions = blue_planned_actions, actions_taken = blue_actions_taken, digested_percepts = blue_digested_percepts)

blue_perception_filter = HotlinePerceptionFilter(agent=None, known = {i for i in range(61)}, substitutions = {}, wildcard=-1)

blue_nca = EscalationLadderAgent(environment = env, time = start_time, perception_filter = blue_perception_filter, amygdala = blue_amygdala, reasoner = blue_reasoner, name="Blue NCA")
# blue_nca.dispatch_table['NextDeliberateAction'] = hotline_deliberate_action
blue_nca.dispatch_table['DeterministicActionsBeforeTime'] = hotline_deterministic_action
blue_perception_filter.agent = blue_nca
env.register_object(blue_nca)
env.add_agent(blue_nca)


# an agent has a list of planned actions, which will get queried whenever someone wants the agent's next_deliberate_action (the next deliberate action gets transformed into a message)
sup.run(verbose = True)

# introduce ladders with asymmetries for comparison; start with minor asymmetry (e.g. associating a few actions with a rung above or
# below its initial position)

red_rung_1a = HotlineLadderRung(match_attributes = any_of([2, 8,
                                                          DeterrentThreat(14, 13, None),
                                                          all_of((DeterrentThreat(20, 19, None), min_adversary_resolve(0.3))),
                                                          all_of((CompellentThreat(2, 3, None), min_adversary_resolve(0.1))),
                                                          all_of((CompellentThreat(8, 9, None), min_adversary_resolve(0.1)))]), # the characteristics mapped from the percepts the agent has digested that map to this rung
                                blue_actions = [(1000, SendPublicMessage(DeterrentThreat(14, 13, None)), UpdateAmygdalaParameters(0.1, 0.1, 0, 0)),
                                               (2000, 2, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)),
                                               (10000, SendPrivateMessage(DeterrentThreat(20, 19, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0)),
                                               (20000, 8, UpdateAmygdalaParameters(0.2, 0.3, 0, 0))], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                red_actions = [(1000, SendPublicMessage(DeterrentThreat(13, 14, None)), UpdateAmygdalaParameters(0.1, 0.1, 0, 0)),
                                               (2000, 1, UpdateAmygdalaParameters(0.1, 0.2, 0, 0)),
                                               (10000, SendPrivateMessage(DeterrentThreat(19, 20, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0)),
                                               (20000, 7, UpdateAmygdalaParameters(0.2, 0.3, 0, 0)),
                                               (25000, SendPrivateMessage(DeterrentThreat(25, 26, None)), UpdateAmygdalaParameters(0.2, 0.2, 0, 0))], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [(600, SendPrivateMessage(ConcessionOffer(6, 5, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (25000, 6, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (35000, SendPrivateMessage(ConcessionOffer(12, 11, None)), UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2)),
                                                             (45000, 12, UpdateAmygdalaParameters(0.2, -0.5, 0.5, 0.2))], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [], # can't even imagine how to de-escalate if it wants to
                                name = "Low-level theater conventional conflict") # with this rung, Red will engage in blustering private threat that should make Blue believe significant escalation has occured

red_ladder_2 = EscalationLadder([red_rung_1a, red_rung_2, red_rung_3, red_rung_4, red_rung_5])

