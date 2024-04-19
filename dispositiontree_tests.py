from supervisor.singlethreadsupervisor import SingleThreadSupervisor, Stop
from environment.singlethreadenvironment import SingleThreadEnvironment
from environment.dispositiontree import GeographicDispositionTree, resolutionError
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
from numpy.testing import assert_almost_equal
import unittest


class GeographicDispositionTreeTests(unittest.TestCase):
    def test_make_tree(self):
        # make the test tree
        min_lat = deg2rad(15)
        max_lat = deg2rad(35)
        min_long = deg2rad(110)
        max_long = deg2rad(130)
        parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), resolution=.01, minimum_resolution=10, parent=None, resolution_reduction_factor=4)
        self.assertEqual(len(parent_tree.children), 0)
        # maybe add more (assertEqual, assertTrue, assertIsNone) to ensure the tree has created correctly
        self.assertEqual(parent_tree.resolution, .01)


    def test_make_child(self):
        # make the test tree
        min_lat = deg2rad(15) 
        max_lat = deg2rad(35) # broken into 4 equal pieces: 15-20, 20-25, 25-30, 30-35
        min_long = deg2rad(110)
        max_long = deg2rad(130) # min/max long is constant across all children
        parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), resolution=.01, minimum_resolution=10, parent=None, resolution_reduction_factor=4)

        target_location = GeographicLocation(deg2rad(21), deg2rad(120), bearing=0)
        parent_tree.make_child(target_location)
        new_child = parent_tree.children[0]
        new_bounds = (deg2rad(20), deg2rad(25), deg2rad(110), deg2rad(130))
        # the new child belongs to the parent
        self.assertEqual(len(parent_tree.children), 1)
        # test that the child has the correct bounds
        assert_almost_equal(new_child.bounds, new_bounds)
        # test that the child has correct resolution
        self.assertEqual(new_child.resolution, 250)

        # make a child at the location that the already-existing child contains
        # then the "new" child should equal that child we already made
        
        # make a child at a location that isn't already covered
        # then there should be a new child, check that there is a new child and it has the right bounds

        # make a child of a child: parent.children[0].make_child(location)

        # make a child of a child of a child: parent.children[0].children[0].make_child(location)


    def test_find_child(self):
        # make the test tree
        min_lat = deg2rad(15)
        max_lat = deg2rad(35)
        min_long = deg2rad(110)
        max_long = deg2rad(130)
        parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), resolution=.01, minimum_resolution=10, parent=None, resolution_reduction_factor=4)

        target_location = GeographicLocation(deg2rad(20), deg2rad(120), 0)
        target_child = parent_tree.find_child(target_location)
        correct_child = parent_tree
        self.assertEqual(target_child, correct_child)

        # we should make even more children and try to find them (specifically, we need to make children of children ...consider 3 levels later)


    def test_is_on_boundary(self):
        min_lat = deg2rad(15)
        max_lat = deg2rad(35)
        min_long = deg2rad(110)
        max_long = deg2rad(130)
        parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), resolution=.01, minimum_resolution=10, parent=None, resolution_reduction_factor=4)

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
        parent_tree = GeographicDispositionTree(bounds=(min_lat, max_lat, min_long, max_long), resolution=.01, minimum_resolution=10, parent=None, resolution_reduction_factor=4)
        
        # test peers of the root, with a single object added
        obj = "a"
        target_location = GeographicLocation(deg2rad(23), deg2rad(115), 0)
        resolution = 10
        parent_tree.set_disposition(obj, target_location, resolution)
        expected_results = set()
        results = parent_tree.identify_peers(obj) # should be ["a"]
        self.assertEqual(len(results), 0)
        self.assertEqual(results, expected_results)

        child = parent_tree.make_child(target_location) # create a new child
        obj = "b"
        expected_results = {"a"} # keep track of all objects added to compare them against the peers
        parent_tree.set_disposition(obj, target_location, resolution) # add obj b to the this child
        results = child.identify_peers(obj) # identify's the peers of the child node
        self.assertEqual(len(results), 1)
        self.assertEqual(results, expected_results)

        target_location = GeographicLocation(deg2rad(26), deg2rad(115), 0)
        child = parent_tree.make_child(target_location)
        obj = "c"
        expected_results = {"a"}
        parent_tree.set_disposition(obj, target_location, resolution)
        results = child.identify_peers(obj)
        self.assertEqual(len(results), 1)
        self.assertEqual(results, expected_results)


    def test_set_disposition(self):
        # create a tree
        min_lat = deg2rad(15)
        max_lat = deg2rad(35)
        min_long = deg2rad(110)
        max_long = deg2rad(130)
        bounds = (min_lat, max_lat, min_long, max_long)
        tree = GeographicDispositionTree(bounds)

        # set the disposition of an object
        obj = "a"
        target_location = GeographicLocation(deg2rad(23), deg2rad(115), 0)
        resolution = 10
        tree.set_disposition(obj, target_location, resolution)

        # TEST 1: test that the disposition was set correctly
        self.assertEqual(tree.contents, [obj])

        obj = "b"
        tree.set_disposition(obj, target_location, resolution)

        self.assertEqual(tree.contents, ["a", "b"])

        # TEST 2: add a child and set the disposition of a new object
        tree.make_child(target_location)
        obj = "c"
        tree.set_disposition(obj, target_location, resolution)

        self.assertEqual(tree.contents, ["a", "b"])
        self.assertEqual(tree.children[0].contents, ["c"])

        # TEST 3: test that bad inputs result in an error
        obj = "z"
        resolution = .010
        with self.assertRaises(resolutionError) as context:
            tree.set_disposition(obj, target_location, resolution)

        self.assertTrue('Object resolution too large. Node resolution: .01, Requested resolution: .010' in str(context.exception))



    def test_adjust_disposition(self):
        # create a tree
        min_lat = deg2rad(15)
        max_lat = deg2rad(35)
        min_long = deg2rad(110)
        max_long = deg2rad(130)
        bounds = (min_lat, max_lat, min_long, max_long)
        tree = GeographicDispositionTree(bounds)

        # set the disposition of an object
        obj = "a"
        target_location = GeographicLocation(deg2rad(23), deg2rad(115), 0)
        resolution = 10
        tree.set_disposition(obj, target_location, resolution)
        obj = "b"
        tree.set_disposition(obj, target_location, resolution)

        # create some children
        tree.make_child(target_location)
        obj = "c"
        tree.set_disposition(obj, target_location, resolution)

        # adjust the disposition of the object
        tree.adjust_disposition("b", target_location, 10)

        # check that the disposition was adjusted correctly
        self.assertEqual(set(tree.contents), set(["a"]))
        self.assertEqual(set(tree.children[0].contents), set(["b", "c"]))


if __name__ == '__main__': # this is the main function that runs the tests
    unittest.main() # this will run the tests in the file
