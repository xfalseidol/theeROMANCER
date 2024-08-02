import context
from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from environment.location import GeographicLocation
from environment.dispositiontree import GeographicDispositionStump
from romancer.commandpe.watchlist import CommandPEWatchlist, CommandPEWatchlistItem
from CommandPEscenarios import scenarios, scenario_names
from romancer.commandpe.perceptionengine import CommandPEPerceptionEngine, CommandPEPerceptionFilter
from romancer.agent.personlikeagent import push_personlike_action
from romancer.agent.escalationladderagent import EscalationLadderAgent
from dill import dump, load
from pathlib import Path
from numpy import deg2rad
from collections import namedtuple
import matplotlib.pyplot as plt


def plot_escalations(times, rungs):
    plt.figure(figsize=(10, 6))
    # plt.step(times[0], rungs[0], where="post", marker="o", alpha=0.3)
    for i in range(len(times)-1, -1, -1):
        plt.step(times[i], rungs[i], where="post", label=scenario_names[i], marker="o", alpha=1.0)
    plt.xlabel("Time (s)")
    plt.ylabel("Ladder")
    plt.title("Escalation Ladder")
    plt.legend()

    rung_labels = ["Calm", "Irritated", "Annoyed", "Agitated", "Angry"]
    plt.yticks(range(len(rung_labels)), labels=rung_labels)
    plt.show()

cpeoutputfolder = cpeinputfolder = "data/orwaca_sample" 

runs = 1


plot_times = []
plot_rungs = []

for scenario in scenarios:
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
    sup.watchlist.push(CommandPEWatchlistItem(time=3000, events_list=[])) # arbitrary end of sim

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
    # Step 3.1: Load amygdala and reasoner
    red_amygdala, red_reasoner = scenario(env)

    # Step 3.2: Create perception filter
    # The pre-processed percepts generated from the Command PE output files may require little/no filtering, so this is just a pass-through except for maybe accessing amygdala parameters
    red_perception_filter = CommandPEPerceptionFilter(agent = None)

    # Step 3.3: Create and add agent
    red_nca = EscalationLadderAgent(environment = env, time = start_time, perception_filter = red_perception_filter, amygdala = red_amygdala, reasoner = red_reasoner, name="Red NCA")
    red_perception_filter.agent = red_nca
    env.register_object(red_nca)
    env.add_agent(red_nca)

    # Step 4: Set up perception engine

    # Step 5: Save configured environment

    # filepath = Path.cwd() / 'commandpedemosupervisor.pkl'

    # with open(filepath, 'wb') as f:
    #     dump(sup, f)

    # Step 6: Run simulation
    sup.run(verbose = True)
    # red_nca.reasoner.export_plot()
    plot_times.append(red_nca.reasoner.plot_time)
    plot_rungs.append(red_nca.reasoner.plot_rungs)
    # plot_escalations([red_nca.reasoner.plot_time], [red_nca.reasoner.plot_rungs])

plot_escalations(plot_times, plot_rungs)