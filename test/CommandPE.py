import context
from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from environment.location import GeographicLocation
from environment.dispositiontree import GeographicDispositionStump
from romancer.commandpe.watchlist import CommandPEWatchlist, CommandPEWatchlistItem
from romancer.commandpe.perceptionengine import CommandPEPerceptionEngine, CommandPEPerceptionFilter
from romancer.agent.personlikeagent import push_personlike_action, DraftROMANCERMessage
from romancer.agent.escalationladderagent import EscalationLadderAgent
from romancer.agent.escalationladderreasoner import EscalationLadder, EscalationLadderRung, EscalationLadderReasoner
from romancer.agent.amygdala import Amygdala, UpdateAmygdalaParameters
from dill import dump, load
from pathlib import Path
from numpy import deg2rad
from collections import namedtuple



cpeoutputfolder = cpeinputfolder = "data/orwaca_sample" 

# STEP 1: Make supervisor
# Note that the supervisor as initialized here does not have its environment set; need to set it once environment is created
sup = SingleThreadSupervisor()

# set dispatch function for PersonlikeActionROMANCERMessage
sup.dispatch_table['PersonlikeActionROMANCERMessage'] = push_personlike_action

watchlist = CommandPEWatchlist(weapon_class_csv = f"{cpeinputfolder}/weaponClass.csv", target_class_csv = f"{cpeinputfolder}/targetClass.csv", target_unit_csv = f"{cpeinputfolder}/targetUnitClass.csv", weapon_fired_csv = f"{cpeoutputfolder}/WeaponFired.csv", weapon_endgame_csv = f"{cpeoutputfolder}/WeaponEndgame.csv")

start_time = 0.0 # watchlist.peek().time # time at which simulated events from CommandPE start

sup.watchlist = watchlist # replace default SingleThreadSupervisor watchlist with populated CommandPE watchlist

sup.watchlist.data = sup.watchlist.data[0:3] # make this manageably short for debugging purposes
WeaponEvent = namedtuple('WeaponEvent', ['event_type', 'weapon', 'target'])
sup.watchlist.push(CommandPEWatchlistItem(time=1810, events_list=[WeaponEvent('other', '5', '3')])) # third eventful watchlist item
sup.watchlist.push(CommandPEWatchlistItem(time=1820, events_list=[])) # hack to trigger fight response 
sup.watchlist.push(CommandPEWatchlistItem(time=1821, events_list=[])) # hack to trigger fight escalation
sup.watchlist.push(CommandPEWatchlistItem(time=1822, events_list=[])) # hack to trigger flight de-escalation
sup.watchlist.push(CommandPEWatchlistItem(time=2200, events_list=[])) # arbitrary end of simulation

# Step 1.2: Configure logger

def demologger(s):
    print('Processed watchlist item: ', s)
    print()

sup.logger = demologger

# Step 2: Make environment

# Step 2.1: Make disposition stump
min_lat = deg2rad(-180)
max_lat = deg2rad(180)
min_long = deg2rad(-180)
max_long = deg2rad(180)

stump = GeographicDispositionStump(bounds = (min_lat, max_lat, min_long, max_long)) # whole Earth

# Step 2.2: Make perception engine
# The CommandPEPerceptionEngine is designed to work with the percepts produced by the scheduled items in the populated CommandPEWatchlist
# Note that this implies that the CommandPEPerceptionEngine may need to have little functionality of its own, possibly merely passing percepts to the RedAgent

engine = CommandPEPerceptionEngine()

# Step 2.3: Make environment
env = SingleThreadEnvironment(supervisor=sup, disposition_tree=stump, perception_engine=engine)

sup.environment = env # set supervisor's environment attribute
engine.environment = env # set perception engine's environment attribute

# Step 3: create and add red agent

# Step 3.1: Create amygdala

# Step 3.1.1: Define Red NCA temperament
# These may need to be set to "crazy" values to get dramatic effects from the demo
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

# Step 3.1.2: 
red_amygdala = Amygdala(environment = env, time = start_time, fight_weight = red_fight_weight, flight_weight = red_flight_weight, freeze_weight = red_freeze_weight, initial_fight = red_initial_fight, initial_flight = red_initial_flight, initial_freeze = red_initial_freeze, initial_pbf = red_initial_pbf, pbf_halflife = red_pbf_halflife, max_pbf = red_max_pbf, response_threshhold = red_response_threshhold)

# Step 3.2: Create perception filter
# The pre-processed percepts generated from the Command PE output files may require little/no filtering, so this is just a pass-through except for maybe accessing amygdala parameters
red_perception_filter = CommandPEPerceptionFilter(agent = None)

# Step 3.3: Create reasoner

# Step 3.3.1: Create and populate escalation ladder
test_action = (0.1, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), UpdateAmygdalaParameters(0, 0, 0, 0))
low_stress_action = (0.5, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), UpdateAmygdalaParameters(0.1, 0.2, 0.3, 0.4))
high_stress_freeze_action = (0.3, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), UpdateAmygdalaParameters(0.8, 0.6, 0.7, 0.8))
high_stress_fight_action = (0.1, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), UpdateAmygdalaParameters(0.8, 2.0, 0, 0))
high_stress_flight_action = (0.2, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), UpdateAmygdalaParameters(0.8, 0, 5.0, 0))
deescalate_action = (0.6, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), UpdateAmygdalaParameters(-0.3, 0, 0, 0))

# agents start on rung1:
## first watchlist item escalates to rung2, stressing out agent just a bit
## second watchlist item escalates to rung3, stressing out agent to point of freezing
## third watchlist item should escalate to rung4, but doesn't since agent is frozen
## agent destresses enough to unfreeze and escalates to rung4, which stresses agent out to point of fighting
## agent automatically escalates to rung5 despite no match, due to fight stress response
## rung5 stresses agent out to point of flight and agent attempts to deescalate

# Intended Schedule:
## 600: New WatchlistItem causes agent to escalate from Rung1 to Rung2
## 600.5:   Agent takes low_stress_action
## 1800:    New WatchlistItem causes agent to escalate from Rung2 to Rung3
## 1800.3:  Agent takes high_stress_freeze_action, freezes
## 1810:    New WatchlistItem should cause agent to escalate from Rung3 to Rung4, doesn't happen due to freeze
## 1819.57: Agent should un-freeze and escalate
## 1819.67: Agent takes high_stress_fight_action
## ????+0.1: Agent automatically escalates from Rung4 to Rung5
## ????+0.3: Agent takes high_stress_flight_action
## ????+0.3: Agent de-escalates

rung1 = EscalationLadderRung(match_attributes = {'event_type': 'deployed', 'weapon': '2'}, # the characteristics mapped from the percepts the agent has digested that map to this rung
                             blue_actions = [], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                             red_actions = [test_action], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                             blue_deescalation_actions = [], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                             red_deescalation_actions = [], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                             name = "Calm")

rung2 = EscalationLadderRung(match_attributes = {'event_type': 'fired', 'weapon': '3'}, # the characteristics mapped from the percepts the agent has digested that map to this rung
                             blue_actions = [], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                             red_actions = [low_stress_action], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                             blue_deescalation_actions = [], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                             red_deescalation_actions = [], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                             name = "Irritated")
# While Herman Kahn's escalation ladder had 44 rungs, for our purposes here far fewer are needed, as we only need a subsection of a full ladder appropriate for the situation decribed in the Command PE model run used to generate the watchlist

rung3 = EscalationLadderRung(match_attributes = {'event_type': 'hit', 'weapon': '4'},
                             blue_actions = [],
                             red_actions = [high_stress_freeze_action],
                             blue_deescalation_actions = [],
                             red_deescalation_actions = [],
                             name = "Annoyed")

rung4 = EscalationLadderRung(match_attributes = {'weapon': '5'},
                             blue_actions = [],
                             red_actions = [high_stress_fight_action],
                             blue_deescalation_actions = [],
                             red_deescalation_actions = [],
                             name = "Agitated"
                             )

rung5 = EscalationLadderRung(match_attributes = {'weapon': '6'},
                             blue_actions = [],
                             red_actions = [high_stress_flight_action],
                             blue_deescalation_actions = [],
                             red_deescalation_actions = [deescalate_action],
                             name = "Angry"
                             )



red_escalation_ladder = EscalationLadder([rung1, rung2, rung3, rung4, rung5])

red_cur_rung = None # change to different rung to start above bottom of escalation ladder (implicitly rung1)

red_planned_actions = None # change to force planned red actions, this will be heapified so it needs to be (time, action) tuples

red_actions_taken = None # change to give Red NCA history of actions taken

red_digested_percepts = None # change to give Red NCA history of digested percepts

red_reasoner = EscalationLadderReasoner(environment = env, time = start_time, escalation_ladder = red_escalation_ladder, identity = 'red', current_rung = red_cur_rung, planned_actions = red_planned_actions, actions_taken = red_actions_taken, digested_percepts = red_digested_percepts)

# Step 3.3.2: Create Red NCA and add to environment
red_nca = EscalationLadderAgent(environment = env, time = start_time, perception_filter = red_perception_filter, amygdala = red_amygdala, reasoner = red_reasoner, name="Red NCA")
red_perception_filter.agent = red_nca
env.register_object(red_nca)
env.add_agent(red_nca)

# Step 4: Set up the perception engine 

# Step 5 Save configured environment

# filepath = Path.cwd() / 'commandpedemosupervisor.pkl'

# with open(filepath, 'wb') as f:
#     dump(sup, f)

# Step 6: Run simulation

sup.run(verbose = True)
