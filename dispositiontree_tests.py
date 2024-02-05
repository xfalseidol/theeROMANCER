from supervisor.singlethreadsupervisor import SingleThreadSupervisor, Stop
from environment.singlethreadenvironment import SingleThreadEnvironment
from environment.dispositiontree import GeographicDispositionTree
from environment.location import GeographicLocation, StationaryGeographicLocation
from environment.perceptionengine import PerceptionEngine, make_change_observer
from environment.percept import Percept
from plane import BZero
from radar import RedRadar, RadarScreen
from blueagent import BlueAgent, BlueAgentPerceptionFilter, PerceiveRedLightOn
from redagent import RedAgent, RedAgentPerceptionFilter, BlipOnRadarScreen
from dill import dump, load
from pathlib import Path
from numpy import deg2rad
from numpy.testing import assert_almost_equal
import unittest


# Step 2: Make environment
# The environment needs a disposition tree and a perception engine, so make those first

# Step 2.1:  Make disposition tree
# This minimal demo contains just a couple of items, therefore the full disposition tree isn't essential and we can use GeographicDispositionStump instead

# min_lat = deg2rad(15)
# max_lat = deg2rad(35)
# min_long = deg2rad(110)
# max_long = deg2rad(130)

# parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), granularity=1000, minimum_granularity=10, parent=None, granularity_reduction_factor=4)

# make_children is called when we create a tree, we can find out if it worked by printing the children of the tree
# print("Here is the parent tree: ")
# print(parent_tree)
# print(parent_tree.children)
# for c in parent_tree.children:
#     print(c.children)



# find_child test: find child for target location 2
# print()
# print("Testing the find_child function:")
# target_location = GeographicLocation(deg2rad(30), deg2rad(120), 0)
# target_child = parent_tree.find_child(target_location)
# print("Found target child:")
# print(target_child)
# print("with bounds:", target_child.bounds)
# print("for target location", target_location.latitude, target_location.longitude)

# # find_child test: find child for target location 3
# print()
# print("Testing the find_child function:")
# target_location = GeographicLocation(deg2rad(16), deg2rad(129), 0)
# target_child = parent_tree.find_child(target_location)
# print("Found target child:")
# print(target_child)
# print("with bounds:", target_child.bounds)
# print("for target location", target_location.latitude, target_location.longitude)

# # try to find a target location that is out of bounds
# print()
# print("Testing the find_child function:")
# target_location = GeographicLocation(deg2rad(10), deg2rad(10), 0)
# target_child = parent_tree.find_child(target_location)
# print("Found target child:")
# print(target_child)
# # print("with bound.s:", target_child.bounds)
# print("for target location", target_location.latitude, target_location.longitude)

# print()
# print("Testing make_child:")
# target_location = GeographicLocation(deg2rad(31), deg2rad(120), 0)
# parent_tree.make_child(target_location)
# print(parent_tree)
# print(parent_tree.children[0].bounds)
# print(target_location)
# target_location = GeographicLocation(deg2rad(16), deg2rad(120), 0)
# parent_tree.make_child(target_location)
# print(parent_tree)
# print(parent_tree.children[1].bounds)
# print(target_location)

# print()
# print("Test 1 set_disposition:")
# print("Root Contents Before:", parent_tree.contents)
# test_object = "test object 1"
# location = target_location
# granularity = 260
# parent_tree.set_disposition(test_object, location, granularity)
# print("Root Contents After:", parent_tree.contents)

# print()
# print("Test 2 set_disposition:")
# print("Child Contents After:", parent_tree.children[1].contents)
# test_object = "test object 2"
# location = target_location
# granularity = 240
# parent_tree.set_disposition(test_object, location, granularity)
# print("Child Contents After:", parent_tree.children[1].contents)

# print()
# print("Test 3 set_disposition:")
# print("Child Contents Before: No appropriate child")
# test_object = "test object 3"
# location = target_location
# granularity = 60
# parent_tree.set_disposition(test_object, location, granularity)
# print("Child Contents After:", parent_tree.children[1].children[0].contents)
# print(parent_tree)
# print()

# print()
# print("Test 4 set_disposition:")
# granularity = 10
# test_object = "test object 4"
# location = target_location
# granularity = 10
# parent_tree.set_disposition(test_object, location, granularity)
# print("Child Contents After:", parent_tree.children[1].children[0].children[0].contents)
# print(parent_tree)
# print()


class GeographicDispositionTreeTests(unittest.TestCase):
    def test_make_tree(self):
        # make the test tree
        min_lat = deg2rad(15)
        max_lat = deg2rad(35)
        min_long = deg2rad(110)
        max_long = deg2rad(130)
        parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), granularity=1000, minimum_granularity=10, parent=None, granularity_reduction_factor=4)
        self.assertEqual(len(parent_tree.children), 0)
        self.assertEqual(parent_tree.granularity, 1000)


    def test_make_child(self):
        # make the test tree
        min_lat = deg2rad(15) 
        max_lat = deg2rad(35) # broken into 4 equal pieces: 15-20, 20-25, 25-30, 30-35
        min_long = deg2rad(110)
        max_long = deg2rad(130) # min/max long is constant across all children
        parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), granularity=1000, minimum_granularity=10, parent=None, granularity_reduction_factor=4)

        target_location = GeographicLocation(deg2rad(21), deg2rad(120), bearing=0)
        parent_tree.make_child(target_location)
        new_child = parent_tree.children[0]
        new_bounds = (deg2rad(20), deg2rad(25), deg2rad(110), deg2rad(130))
        # the new child belongs to the parent
        self.assertEqual(len(parent_tree.children), 1)
        # test that the child has the correct bounds
        assert_almost_equal(new_child.bounds, new_bounds)
        # test that the child has correct granularity
        self.assertEqual(new_child.granularity, 250)

        # try to make a child at the location that the already-existing child contains
        # then the "new" child should equal that child we already made
        
        # try to make a child at a location that isn't already covered
        # then there should be a new child, check that there is a new child and it has the right bounds

        # try to make a child of a child: parent.children[0].make_child(location)

        # try to make a child of a child of a child: parent.children[0].children[0].make_child(location)


    # our tests go here, each function should test something different from the GeographicDispositionTree
    def test_find_child(self):
        # make the test tree
        min_lat = deg2rad(15)
        max_lat = deg2rad(35)
        min_long = deg2rad(110)
        max_long = deg2rad(130)
        parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), granularity=1000, minimum_granularity=10, parent=None, granularity_reduction_factor=4)

        target_location = GeographicLocation(deg2rad(20), deg2rad(120), 0)
        target_child = parent_tree.find_child(target_location)
        correct_child = parent_tree
        self.assertEqual(target_child, correct_child)

        # I need to make more children and try to find them (specifically, we need to make children of children etc)


    def test_is_on_boundary(self):
        min_lat = deg2rad(15)
        max_lat = deg2rad(35)
        min_long = deg2rad(110)
        max_long = deg2rad(130)
        parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), granularity=1000, minimum_granularity=10, parent=None, granularity_reduction_factor=4)

        target_location = GeographicLocation(deg2rad(20), deg2rad(120), 0)
        result = parent_tree.is_on_boundary(target_location)
        # test that a point really is on the boundary
        self.assertFalse(result)

        target_location = GeographicLocation(deg2rad(23), deg2rad(115), 0)
        result = parent_tree.is_on_boundary(target_location)
        # test that a point is not on the boundary
        self.assertFalse(result)

        target_location = GeographicLocation(deg2rad(10), deg2rad(90), 0)
        result = parent_tree.is_on_boundary(target_location)
        # test that a point is not on the boundary
        self.assertFalse(result)

        target_location = GeographicLocation(deg2rad(15), deg2rad(110), 0)
        result = parent_tree.is_on_boundary(target_location)
        # test that a point is not on the boundary
        self.assertTrue(result)


    def test_identify_peers(self):
        # to test this, we must:
        # 1. create a tree
        # 2. add objects to the tree (call set_disposition), parent_tree.set_disposition(blah, blah, blah)
        # 3. check the results of identify_peers
        min_lat = deg2rad(15)
        max_lat = deg2rad(35)
        min_long = deg2rad(110)
        max_long = deg2rad(130)
        parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), granularity=1000, minimum_granularity=10, parent=None, granularity_reduction_factor=4)
        
        # test peers of the root, with a single object added
        obj = "a"
        target_location = GeographicLocation(deg2rad(23), deg2rad(115), 0)
        granularity = 10
        parent_tree.set_disposition(obj, target_location, granularity)
        expected_results = {obj}
        results = parent_tree.identify_peers() # should be ["a"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results, expected_results)

        child = parent_tree.make_child(target_location) # create a new child
        obj = "b"
        expected_results = {"a", "b"} # keep track of all objects added to compare them against the peers
        parent_tree.set_disposition(obj, target_location, granularity) # add obj b to the this child
        results = child.identify_peers() # identify's the peers of the child node
        self.assertEqual(len(results), 2)
        self.assertEqual(results, expected_results)

        target_location = GeographicLocation(deg2rad(26), deg2rad(115), 0)
        child = parent_tree.make_child(target_location)
        obj = "c"
        expected_results = {"a", "c"}
        parent_tree.set_disposition(obj, target_location, granularity)
        results = child.identify_peers()
        self.assertEqual(len(results), 2)
        self.assertEqual(results, expected_results)


    def test_set_disposition(self):
        pass

if __name__ == '__main__': # this is the main function that runs the tests
    unittest.main() # this will run the tests in the file