from supervisor.singlethreadsupervisor import SingleThreadSupervisor, Stop
from environment.singlethreadenvironment import SingleThreadEnvironment
from environment.dispositiontree import GeographicDispositionStump
from environment.location import GeographicLocation, StationaryGeographicLocation
from environment.perceptionengine import PerceptionEngine, make_change_observer
from environment.percept import Percept
from plane import BZero, RedLight
from radar import RedRadar, RadarScreen
from blueagent import BlueAgent, BlueAgentPerceptionFilter, PerceiveRedLightOn
from redagent import RedAgent, RedAgentPerceptionFilter, BlipOnRadarScreen
from dill import dump, load
from pathlib import Path
from numpy import deg2rad


# STEP 1: Make supervisor
# Note that the supervisor as initialized here does not have its environment set; need to set it once environment is created
sup = SingleThreadSupervisor()

# Step 1.1: Set simulation stop time
stop = Stop(time=600.0) # simulation duration 10 minutes
sup.watchlist.push(stop) # push stop time onto watchlist

# Step 1.2: Configure logger

def demologger(s):
    print('Processed watchlist item: ', s)

sup.logger = demologger

# Step 2: Make environment
# The environment needs a disposition tree and a perception engine, so we make those first

# Step 2.1:  Make disposition tree
# This minimal demo contains just a couple of items, therefore the full disposition tree isn't essential and we can use GeographicDispositionStump instead

min_lat = deg2rad(15)
max_lat = deg2rad(35)
min_long = deg2rad(110)
max_long = deg2rad(130)

stump = GeographicDispositionStump(bounds=(min_lat, max_lat, min_long, max_long)) # bounds represent Taiwan strait, Taiwan

# Step 2.2: Make perception engine
# Note that the perception engine needs to be configured, but this needs to wait until agents and environmental objects have been created
engine = PerceptionEngine()

# Step 2.3: Make environment
env = SingleThreadEnvironment(supervisor=sup, disposition_tree=stump, perception_engine=engine)
engine.environment = env # set perception engine's environment attribute

sup.environment = env # set supervisor's environment attribute

# Step 3: Create environmental objects

# Step 3.1: Create and configure plane
bomber = BZero(environment=env, time=0.0, location=GeographicLocation(latitude=deg2rad(22.95), longitude=deg2rad(118.05), bearing=deg2rad(45)), speed=800.0)
env.register_object(bomber)
env.add_object(bomber)

# The red warning light in the cockpit turns on to indicate adversary radar detected
light = RedLight(environment=env, time=0.0, location=bomber.location)
env.register_object(light)
env.add_object(light, parent_object=bomber)

# Step 3.2: Create and configure red radar
radar = RedRadar(environment=env, time=0.0, location=StationaryGeographicLocation(latitude=deg2rad(24.7816), longitude=deg2rad(118.5517)))
env.register_object(radar)
env.add_object(radar)

screen = RadarScreen(environment=env, time=0.0, location=radar.location)
env.register_object(screen)
env.add_object(screen, parent_object=radar)

# Step 4: Create and configure agents

# Step 4.1: Create blue agent
pilot = BlueAgent(environment=env, time=0.0, perception_filter=None, ecm=False, red_light_on=False, intended_ecm_activation_time=None)
pilot.perception_filter = BlueAgentPerceptionFilter(agent=pilot)
env.register_object(pilot)
env.add_agent(pilot, parent_object=bomber) # place blue agent in bomber

# Step 4.2: Create red agent

operator = RedAgent(environment=env, time=0.0, perception_filter=None, intended_radar_activation_time=400.0, blip_count=0, believed_radar_state=False)
operator.perception_filter = RedAgentPerceptionFilter(agent=operator)
env.register_object(operator)
env.add_agent(operator, parent_object=radar) # associate red agent with radar

# Step 5: Configure perception engine

# This simple perception engine consists of two observer functions, one for each of the agents.

# The first of these observer functions, for blue, generates a percept whenever the state of a particular variable--
# that representing the warning light in the bomber cockpit that indicates possible detection by adversary radar--
# has changed from the last seen value.

blue_observer = make_change_observer(light, 'on', PerceiveRedLightOn)

engine.add_observer(agent_id=pilot.uid, observer=blue_observer)

# The second observer function, for red, checks to see if the value of a particular variable--that representing whether
# the radar screen has a blip to display--is True. If so it generates a possible percept and then resets that variable to False.

def red_observer():
    if screen.blip_to_display:
        percept = BlipOnRadarScreen(uid=screen.uid, attr='blips_to_display', val=True, time=screen.time)
        screen.blip_to_display = False
        return percept

engine.add_observer(agent_id=operator.uid, observer=red_observer)

# Now that everything is set up, we can save the configuration for future tests

# Step 6: Save configured environment

filepath = Path.cwd() / 'demo1supervisor.pkl'

with open(filepath, 'wb') as f:
    dump(sup, f)

# Step 7: Run simulation

# Step 7.1: Step through simulation?

sup.process_inbox() # probably unnecessary
print("Initial watchlist: ", sup.watchlist)
    
while len(sup.watchlist) > 0:
    sup.bring_watchlist_up_to_date()
    print("Updated watchlist: ", sup.watchlist)
    # sup.process_inbox() # needed?
    sup.process_next_watchlist_item()
    # sup.process_inbox() # needed?

# Step 8: analyze results of simulation

# analyze logfile?
