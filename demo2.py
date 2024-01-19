from supervisor.singlethreadsupervisor import SingleThreadSupervisor, Stop
from environment.singlethreadenvironment import SingleThreadEnvironment
from environment.dispositiontree import GeographicDispositionTree
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

parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), granularity=1000, minimum_granularity=10, parent=None, granularity_reduction_factor=4)

# make_children is called when we create a tree, we can find out if it worked by printing the children of the tree
# print("Here is the parent tree: ")
# print(parent_tree)
# print(parent_tree.children)
# for c in parent_tree.children:
#     print(c.children)

# find_child test: find child for target location 1
print()
print("Testing the find_child function:")
target_location = GeographicLocation(deg2rad(20), deg2rad(120), 0)
target_child = parent_tree.find_child(target_location)
print("Found target child:")
print(target_child)
print("with bounds:", target_child.bounds)
print("for target location", target_location.latitude, target_location.longitude)

# find_child test: find child for target location 2
print()
print("Testing the find_child function:")
target_location = GeographicLocation(deg2rad(30), deg2rad(120), 0)
target_child = parent_tree.find_child(target_location)
print("Found target child:")
print(target_child)
print("with bounds:", target_child.bounds)
print("for target location", target_location.latitude, target_location.longitude)

# find_child test: find child for target location 3
print()
print("Testing the find_child function:")
target_location = GeographicLocation(deg2rad(16), deg2rad(129), 0)
target_child = parent_tree.find_child(target_location)
print("Found target child:")
print(target_child)
print("with bounds:", target_child.bounds)
print("for target location", target_location.latitude, target_location.longitude)

# try to find a target location that is out of bounds
print()
print("Testing the find_child function:")
target_location = GeographicLocation(deg2rad(10), deg2rad(10), 0)
target_child = parent_tree.find_child(target_location)
print("Found target child:")
print(target_child)
# print("with bound.s:", target_child.bounds)
print("for target location", target_location.latitude, target_location.longitude)

print()
print("Testing make_child:")
target_location = GeographicLocation(deg2rad(31), deg2rad(120), 0)
parent_tree.make_child(target_location)
print(parent_tree)
print(parent_tree.children[0].bounds)
print(target_location)
target_location = GeographicLocation(deg2rad(16), deg2rad(120), 0)
parent_tree.make_child(target_location)
print(parent_tree)
print(parent_tree.children[1].bounds)
print(target_location)

print()
print("Test 1 set_disposition:")
print("Root Contents Before:", parent_tree.contents)
test_object = "test object 1"
location = target_location
granularity = 260
parent_tree.set_disposition(test_object, location, granularity)
print("Root Contents After:", parent_tree.contents)

print()
print("Test 2 set_disposition:")
print("Child Contents After:", parent_tree.children[1].contents)
test_object = "test object 2"
location = target_location
granularity = 240
parent_tree.set_disposition(test_object, location, granularity)
print("Child Contents After:", parent_tree.children[1].contents)

print()
print("Test 3 set_disposition:")
print("Child Contents Before: No appropriate child")
test_object = "test object 3"
location = target_location
granularity = 60
parent_tree.set_disposition(test_object, location, granularity)
print("Child Contents After:", parent_tree.children[1].children[0].contents)
print(parent_tree)
print()

print()
print("Test 4 set_disposition:")
granularity = 10
test_object = "test object 4"
location = target_location
granularity = 10
parent_tree.set_disposition(test_object, location, granularity)
print("Child Contents After:", parent_tree.children[1].children[0].children[0].contents)
print(parent_tree)
print()