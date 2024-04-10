from environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict
from supervisor.singlethreadsupervisor import SingleThreadSupervisor, Stop
from environment.location import GeographicLocation
from environment.singlethreadenvironment import SingleThreadEnvironment
import unittest

class TestImprovedRomancerObject(ImprovedRomancerObject):

    def __init__(self, environment, time): # any new object can have any number of attributes, which could be any type of data, including sets/lists/dictionaries
        super().__init__(environment, time)
        self.unlogged_attrs.append('unlogged')
        self.unlogged = 'eggs' # setting an unlogged attribute
        logged_1 = 'hat' # a logged attribute defined at initialization time
        # self.unlogged_attrs.append('locations_visited')
        self.locations_visited = LoggedList(list(), self, 'locations_visited') # a logged list, can contain duplicates
        # self.unlogged_attrs.append('actions_available')
        self.actions_available = LoggedSet(set(), self, 'actions_available') # a logged set, a set contains no duplicates
        # self.unlogged_attrs.append('objects_encountered_by_location')
        self.objects_encountered_by_location = LoggedDict(dict(), self, 'objects_encountered_by_location') # a logged dict
        self.repr_list += ["locations_visited", "actions_available", "objects_encountered_by_location"]


class DoubleDerivedTestObject(TestImprovedRomancerObject):
    def __init__(self, environment, time):
        super().__init__(environment, time)

# STEP 1: Make supervisor
# Note that the supervisor as initialized here does not have its environment set; need to set it once environment is created
sup = SingleThreadSupervisor()

env = SingleThreadEnvironment(supervisor=sup, disposition_tree=None, perception_engine=None) # env is only needed to initialize TestImprovedRomancerObject

test_object = DoubleDerivedTestObject(env, env.time)

# print or save test_object?

test_object.forward_simulation(2.0) # advance object time to 2.0 seconds

# suppose we visit a new location, get refueled, gain a new action, and encounter a new object at t = 2.0
test_object.unlogged = 'bacon'
test_object.locations_visited.append('a') # append new location to test_object.locations_visited
test_object.actions_available.add("Take Off")
test_object.objects_encountered_by_location['Airfield'] = 'a'

# print or save test_object?

test_object.forward_simulation(3.0) # advance object time to 3.0 seconds

test_object.locations_visited.append('b')
test_object.actions_available.add('Drop Aid Package')
test_object.actions_available.intersection_update({'Drop Aid Package'})
test_object.objects_encountered_by_location['RedAgent'] = 'c'
# print or save test_object?

test_object.forward_simulation(5.0) # advance object time to 5.0 seconds

test_object.locations_visited.pop()
test_object.locations_visited.append('c')
# test_object.actions_available.add('Intercept')

# print or save test_object?
print('Sim Time: 5.0')
print(test_object)
print()

test_object.forward_simulation(6.0) # advance object time to 6.0 seconds

# test_object.logged_1 = 12345 # test_object.logged_1 re-added with a value of a different type
test_object.tail_number = "F204"
test_object.locations_visited.append('d') # change test_object.l[1] from 1 to 2
test_object.objects_encountered_by_location['RedAgent'] = 'd' # change test_object.d['two] from 2 to 3
test_object.objects_encountered_by_location['Alien'] = 'c'
test_object.actions_available.discard('Drop Aid Package') # discard 1 from test_object.s

# print or save test_object?
print('Sim Time: 6.0')
print(test_object)
print()

test_object.forward_simulation(8.0)
test_object.actions_available.update({"Take Off", "Drop Aid Package", "Crash"})
test_object.actions_available.difference_update({"Drop Aid Package", "Crash"})
test_object.tail_number = "Z600"
test_object.objects_encountered_by_location.pop('Alien')
test_object.objects_encountered_by_location.popitem()
test_object.objects_encountered_by_location.update({'BlueAgent': 'b', 'Base': 'f'})

print('Sim Time: 8.0')
print(test_object)
print()

test_object.forward_simulation(10.0)
test_object.actions_available.add("Drop Aid Package")
test_object.actions_available.symmetric_difference_update({"Drop Aid Package", "Crash"})
del test_object.tail_number # delete an attribute

print('Sim Time: 10.0')
print(test_object)
print()

test_object.rewind(6.0)
print('Sim Time: 6.0')
print(test_object)
print()

test_object.rewind(5.5)

test_object.actions_available.update({'Eject Pilot', 'Contact Base'})
# redefine actions_available using the union operation
test_object.actions_available = test_object.actions_available.intersection({'Eject Computer'})
test_object.locations_visited += ['x', 'y', 'z']
# test_object.locations_visited.insert(3, 'w')

# is test_object now identical to what it was before time = 6.0?
# print or save test_object?
print('Sim Time: 5.5')
print(test_object)
print()

test_object.forward_simulation(6.0)
# test_object.locations_visited.reverse()

print('Sim Time: 6.0')
print(test_object)
print()

test_object.rewind(5.5)
# test_object.actions_available.clear()
test_object.locations_visited.clear()
# test_object.objects_encountered_by_location.clear()

print('Sim Time: 5.5')
print(test_object)
print()

# test_object.forward_simulation(6)

# del test_object.locations_visited[0:2]
# test_object.locations_visited[2:4] = ['q', 'r']

# print('Sim Time: 6.0')
# print(test_object)
# print()

test_object.rewind(2.0)
print('Sim Time: 2.0')
print(test_object)
print()

# is test_object now identical to what it was when time = 2.0?
# print or save test_object?

# explore alternate futures via forward simulation?