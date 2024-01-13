from dill import load
from numpy import pi, rad2deg, deg2rad, arange
from numpy.random import randint, uniform, default_rng
from redagent import BlipOnRadarScreen
from environment.location import GeographicLocation
from plane import BZeroLogpoint
from redagent import RedAgentLogpoint
from copy import copy
import matplotlib.pyplot as plt

filepath = 'demo1supervisor.pkl'

low_time = 100
high_time = 500

min_speed = 700
max_speed = 1000

min_bearing = 30
max_bearing = 60

min_lat = 21.5
max_lat = 23.5

min_long = 117.5
max_long = 119.5

no_rollouts = 1000


def rebuild_scenario(radar_time, bomber_speed, bomber_bearing, bomber_latitude, bomber_longitude):
    with open('demo1supervisor.pkl', 'rb') as f:
        sup = load(f)

    bomber, radar = sup.environment.contents
    red_agent = radar.children[1]
    bomber_logpoint = bomber.loglist[0]
    bomber.speed = bomber_speed
    bomber.location = GeographicLocation(latitude=bomber_latitude, longitude=bomber_longitude, bearing=bomber_bearing)
    bomber_logpoint.speed = bomber.speed
    bomber_logpoint.location = copy(bomber.location)
    red_agent_logpoint = red_agent.loglist[0]
    red_agent.intended_radar_activation_time = radar.time
    red_agent_logpoint.intended_radar_activation_time = red_agent.intended_radar_activation_time
    # maybe vary random seed too

    return sup, radar

outcomes = list()

for _ in range(no_rollouts):
    blip_count = 0
    contact_attempt_count = 0
    
    radar_time = randint(low_time, high_time)
    bomber_speed = randint(min_speed, max_speed)
    bomber_bearing = deg2rad(randint(min_bearing, max_bearing))
    bomber_latitude = deg2rad(uniform(min_lat, max_lat))
    bomber_longitude = deg2rad(uniform(min_long, max_long))

    sup, radar = rebuild_scenario(radar_time=radar_time, bomber_speed=bomber_speed, bomber_bearing=bomber_bearing, bomber_latitude=bomber_latitude, bomber_longitude=bomber_longitude)

    screen = radar.children[0]

    def histogramlogger(s):
        global blip_count, contact_attempt_count
        if s.__class__.__name__ == 'DisplayBlip':
            blip_count += 1
        elif s.__class__.__name__ == 'ContactSuperior':
            contact_attempt_count += 1

    sup.logger = histogramlogger
    sup.rng = default_rng()

    sup.run()
    
    outcomes.append((blip_count, contact_attempt_count))


# print(outcomes)

fig, axs = plt.subplots(ncols=2)

axs[0].hist([outcome[0] for outcome in outcomes], bins=arange(26)-0.5, density=True, color='blue')
axs[0].set_title('number of radar blips displayed')
axs[0].set_xticks(range(25))

axs[1].hist([outcome[1] for outcome in outcomes], bins=arange(26)-0.5, density=True, color='red')
axs[1].set_title('number of attempts to contact superior')
axs[1].set_xticks(range(25))

plt.show()
