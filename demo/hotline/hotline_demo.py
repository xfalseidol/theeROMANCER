from casebasedreasoner.escalationladderreasoner import EscalationLadderCBR
from casebasedreasoner.MOP_comparer_sorter import HLRComparerSorter
from hotline_rules import load_ladder_inputs
from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor, Stop
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from romancer.environment.dispositiontree import GeographicDispositionStump
from romancer.agent.amygdala import Amygdala
from romancer.agent.escalationladderreasoner import EscalationLadder
from romancer.agent.escalationladderagent import EscalationLadderAgent
from hotline_reasoner import HotlineLadderRung, HotlineLadderReasoner
from hotline_percept import HotlinePerceptionEngine, HotlinePerceptionFilter
from hotline_actions import hotline_action_dispatcher, hotline_public_message_dispatcher, hotline_private_message_dispatcher, hotline_deterministic_action, hotline_rung_change_dispatcher
from numpy import deg2rad


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

blue_mapping = { "Self": "Blue", "Adversary": "Red"}
red_mapping = { "Self": "Red", "Adversary": "Blue"}

# To start we construct two mirror-imaged escalation ladders:
def run_hotline(
        blue_initial_fight = 0.0, blue_initial_flight = 0.0, blue_initial_freeze = 0.8,
        blue_initial_pbf = 0.3, blue_pbf_halflife = 10000.0, blue_max_pbf = 1.0,
        blue_response_threshhold = 0.2, blue_amyg=None, blue_elcbr=None, blue_train_elcbr=True, blue_run_elcbr=False,
        blue_ladder_file = "data/ladder.csv",

        red_initial_fight = 0.0, red_initial_flight = 0.0, red_initial_freeze = 0.5,
        red_initial_pbf = 0.0001, red_pbf_halflife = 100.0, red_max_pbf = 1.0,
        red_response_threshhold = 0.7, red_amyg=None, red_elcbr=None, red_train_elcbr=True, red_run_elcbr=False,
        red_ladder_file = "data/ladder.csv"
    ):

    blue_action_lexicon, blue_ladder_rung_inp, blue_matching_rules, blue_actions, blue_deescalate_actions = load_ladder_inputs(blue_ladder_file, blue_mapping)
    red_action_lexicon, red_ladder_rung_inp, red_matching_rules, red_actions, red_deescalate_actions = load_ladder_inputs(red_ladder_file, red_mapping)
    actionlexicon = blue_action_lexicon

    blue_ladder_rungs = []
    red_ladder_rungs = []
    for (rungnum, rungname) in blue_ladder_rung_inp:
        blue_ladder_rungs.append(HotlineLadderRung(match_attributes = blue_matching_rules[rungnum],
                                                   actions = blue_actions[rungnum],
                                                   deescalation_actions = blue_deescalate_actions[rungnum],
                                                   name = rungname))
    for (rungnum, rungname) in red_ladder_rung_inp:
        red_ladder_rungs.append(HotlineLadderRung(match_attributes=red_matching_rules[rungnum],
                                                   actions=red_actions[rungnum],
                                                   deescalation_actions=red_deescalate_actions[rungnum],
                                                   name= rungname))

    blue_ladder_1 = EscalationLadder(blue_ladder_rungs)
    red_ladder_1 = EscalationLadder(red_ladder_rungs)

    # use these ladders to construct two opposing HotlineReasoners

    # from this point forward analogous to escalation ladder demo
    # STEP 1: Make supervisor
    # Note that the supervisor as initialized here does not have its environment set; need to set it once environment is created

    start_time = 0.0

    sup = SingleThreadSupervisor()
    # Step 1.2: Configure logger
    def hotline_logger(s):
        print(s)
        pass
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
    days = 1
    sup.watchlist.push(Stop(time=86400 * days))

    min_lat = deg2rad(-180)
    max_lat = deg2rad(180)
    min_long = deg2rad(-180)
    max_long = deg2rad(180)

    stump = GeographicDispositionStump(bounds = (min_lat, max_lat, min_long, max_long)) # whole Earth

    engine = HotlinePerceptionEngine()

    env = SingleThreadEnvironment(supervisor=sup, disposition_tree=stump, perception_engine=engine)
    sup.environment = env
    engine.environment = env

    red_amyg_class = red_amyg
    if red_amyg_class is None:
        red_amyg_class = Amygdala
    red_amygdala = red_amyg_class(environment = env, time = env.time, name="Red")
    # Only take these if an amygdala class hasn't been specified [because specifying usually means archetype]
    if red_amyg is None:
        red_amygdala.set_response_values(initial_fight = red_initial_fight,
                                     initial_flight = red_initial_flight,
                                     initial_freeze = red_initial_freeze)
    red_amygdala.set_pbf(initial_pbf = red_initial_pbf, pbf_halflife = red_pbf_halflife,
                     max_pbf = red_max_pbf, response_threshhold = red_response_threshhold)

    red_cur_rung = None # change to different rung to start above bottom of escalation ladder (implicitly rung1)
    red_actions_taken = None # change to give Red NCA history of actions taken
    red_digested_percepts = None # change to give Red NCA history of digested percepts

    red_reasoner = HotlineLadderReasoner(environment = env, time = env.time, escalation_ladder = red_ladder_1,
                                         identity = 'Red', current_rung = red_cur_rung, planned_actions = None,
                                         actions_taken = red_actions_taken, digested_percepts = red_digested_percepts,
                                         cbr=red_elcbr, cbr_train=red_train_elcbr, cbr_run=red_run_elcbr)

    red_perception_filter = HotlinePerceptionFilter(agent=None, known = {i for i in range(61)}, substitutions = {}, wildcard=-1)

    red_nca = EscalationLadderAgent(environment = env, time = start_time, perception_filter = red_perception_filter, amygdala = red_amygdala, reasoner = red_reasoner, name="Red NCA")
    # red_nca.dispatch_table['NextDeliberateAction'] = hotline_deliberate_action
    red_nca.dispatch_table['DeterministicActionsBeforeTime'] = hotline_deterministic_action
    red_perception_filter.agent = red_nca
    env.register_object(red_nca)
    env.add_agent(red_nca)

    blue_amyg_class = blue_amyg
    if blue_amyg_class is None:
        blue_amyg_class = Amygdala
    # Only take these if an amygdala class hasn't been specified [because specifying usually means archetype]
    blue_amygdala = blue_amyg_class(environment = env, time = env.time, name="Blue")
    if blue_amyg is None:
        blue_amygdala.set_response_values(initial_fight = blue_initial_fight,
                                     initial_flight = blue_initial_flight,
                                     initial_freeze = blue_initial_freeze)
    blue_amygdala.set_pbf(initial_pbf = blue_initial_pbf, pbf_halflife = blue_pbf_halflife,
                     max_pbf = blue_max_pbf, response_threshhold = blue_response_threshhold)


    blue_cur_rung = None # change to different rung to start above bottom of escalation ladder (implicitly rung1)
    blue_planned_actions = [] # change to force planned blue actions, this will be heapified so it needs to be (time, action) tuples
    blue_actions_taken = None # change to give Blue NCA history of actions takencd
    blue_digested_percepts = None # change to give Blue NCA history of digested percepts

    blue_reasoner = HotlineLadderReasoner(environment = env, time = env.time, escalation_ladder = blue_ladder_1,
                                          identity = 'Blue', current_rung = blue_cur_rung, planned_actions = blue_planned_actions,
                                          actions_taken = blue_actions_taken, digested_percepts = blue_digested_percepts,
                                          cbr=blue_elcbr, cbr_train=blue_train_elcbr, cbr_run=blue_run_elcbr)

    blue_perception_filter = HotlinePerceptionFilter(agent=None, known = {i for i in range(61)}, substitutions = {}, wildcard=-1)

    blue_nca = EscalationLadderAgent(environment = env, time = start_time, perception_filter = blue_perception_filter, amygdala = blue_amygdala, reasoner = blue_reasoner, name="Blue NCA")
    # blue_nca.dispatch_table['NextDeliberateAction'] = hotline_deliberate_action
    blue_nca.dispatch_table['DeterministicActionsBeforeTime'] = hotline_deterministic_action
    blue_perception_filter.agent = blue_nca
    env.register_object(blue_nca)
    env.add_agent(blue_nca)

    # if blue_elcbr is not None:
    #     blue_elcbr.reset_romancer_object(environment = env, time = env.time)
    # if red_elcbr is not None:
    #     red_elcbr.reset_romancer_object(environment = env, time = env.time)

    red_planned_actions = [(1000, actionlexicon.get_actionnum("Red", "Threat", "3"), None),
                           (25000, actionlexicon.get_actionnum("Red", "Threat", "6"),
                            None)]  # change to force planned red actions, this will be heapified so it needs to be (time, action) tuples
    red_reasoner._enqueue_actions(red_planned_actions)

    # an agent has a list of planned actions, which will get queried whenever someone wants the agent's next_deliberate_action (the next deliberate action gets transformed into a message)
    sup.run(verbose = True)

    blue_reasoner.export_plot()
    blue_amygdala.export_plot()

    red_reasoner.export_plot()
    red_amygdala.export_plot()
    # introduce ladders with asymmetries for comparison; start with minor asymmetry (e.g. associating a few actions with a rung above or
    # below its initial position)

if __name__ == "__main__":
    print("Training Blue ELCBR using HLR decisions...")
    sup = SingleThreadSupervisor()
    env = SingleThreadEnvironment(sup, None, None)
    blue_elcbr = EscalationLadderCBR(env, 0.0, comparer_sorter=HLRComparerSorter())
    env = SingleThreadEnvironment(sup, None, None)
    red_elcbr = EscalationLadderCBR(env, 0.0, comparer_sorter=HLRComparerSorter())
    run_hotline(blue_elcbr=blue_elcbr, red_elcbr=red_elcbr, blue_train_elcbr=True, red_train_elcbr=True) # HLR vs HLR (training an ELCBR)
    blue_elcbr.serialize("trainedHLR.pkl")
    print()
    blue_elcbr.display_memory()
    print("Rerunning simulation with trained Blue ELCBR...")
    # run_hotline(blue_elcbr=blue_elcbr, red_elcbr=red_elcbr, blue_train_elcbr=False, blue_run_elcbr=True) # HLR-ECLBR vs HLR
    # run_hotline(blue_elcbr=blue_elcbr, red_elcbr=red_elcbr, blue_train_elcbr=False, blue_run_elcbr=True, red_train_elcbr=False, red_run_elcbr=True) # HLR-ECLBR vs HLR-ELCBR
    blue_elcbr.display_memory()
    # export_cbr_sqlite(blue_train_elcbr, "hotline_demo_blue_cbr.sqlite")


# make_graphviz_graph(blue_elcbr, "blue_elcbr.dot")
# export_cbr_sqlite(blue_elcbr, "blue_elcbr.sqlite")
