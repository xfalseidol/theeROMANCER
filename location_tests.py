from supervisor.singlethreadsupervisor import SingleThreadSupervisor, Stop
from environment.singlethreadenvironment import SingleThreadEnvironment
from environment.dispositiontree import GeographicDispositionTree, GranularityError
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
import unittest
import math

class LocationTests(unittest.TestCase):
	def test_find_intersection(self):
		## two locations heading in perpendicular directions
		# define two GeographicLocations, which should intersect
		location_1 = GeographicLocation(deg2rad(25), deg2rad(0), bearing=deg2rad(90))
		location_2 = GeographicLocation(deg2rad(0), deg2rad(25), bearing=deg2rad(0))

		# use location.calculate_intersection to find the intersection
		intersection = GeographicLocation.calculate_intersection(location_1, location_2)
		# print(intersection.to_decimal_degrees())

		# check our solution against https://www.movable-type.co.uk/scripts/latlong.html
		self.assertAlmostEqual(intersection.latitude, deg2rad(22.909722), places = 5) # 25* 54' 35"
		self.assertAlmostEqual(intersection.longitude, deg2rad(25), places = 5)	# 25* 0' 0"


		## two locations heading in similar direction
		# define two GeographicLocations, which should intersect
		location_1 = GeographicLocation(deg2rad(25), deg2rad(0), bearing=deg2rad(100))
		location_2 = GeographicLocation(deg2rad(0), deg2rad(0), bearing=deg2rad(80))

		# use location.calculate_intersection to find the intersection
		intersection = GeographicLocation.calculate_intersection(location_1, location_2)
		# print(intersection.to_decimal_degrees())

		# check our solution against https://www.movable-type.co.uk/scripts/latlong.html
		self.assertAlmostEqual(intersection.latitude, deg2rad(7.857222), places = 5)
		self.assertAlmostEqual(intersection.longitude, deg2rad(51.502778), places = 5)


		## two locations heading in parallel directions and at different latitudes
		## QUESTION: can you check that this test sensibly should return no intersection?
		# define two GeographicLocations, which should intersect
		location_1 = GeographicLocation(deg2rad(25), deg2rad(0), bearing=deg2rad(90))
		location_2 = GeographicLocation(deg2rad(-25), deg2rad(0), bearing=deg2rad(90))

		# use location.calculate_intersection to find the intersection
		intersection = GeographicLocation.calculate_intersection(location_1, location_2)
		# print(intersection.to_decimal_degrees())

		# check our solution against https://www.movable-type.co.uk/scripts/latlong.html
		self.assertTrue(math.isnan(intersection.latitude))
		self.assertTrue(math.isnan(intersection.longitude))
		# self.assertAlmostEqual(intersection.latitude, 0)
		# self.assertAlmostEqual(intersection.longitude, deg2rad(90))


		## two locations heading in parallel directions and not in line with other
		# This test should verify that when two paths are parallel but not aligned (i.e., they never intersect), the function should return a NaN
		location_1 = GeographicLocation(deg2rad(25), deg2rad(0), bearing=deg2rad(90))
		location_2 = GeographicLocation(deg2rad(25), deg2rad(10), bearing=deg2rad(90))


		intersection = GeographicLocation.calculate_intersection(location_1, location_2)
		# print(intersection.to_decimal_degrees())

		# Expected result: No intersection (both latitude and longitude should return NaN or similar)
		self.assertTrue(math.isnan(intersection.latitude))
		self.assertTrue(math.isnan(intersection.longitude)) #"ambiguous" on website

		## two locations already intersecting (in the same location)
		# This test checks the behavior of the function when both starting points are the same, meaning they're already intersecting.
		location_1 = GeographicLocation(deg2rad(25), deg2rad(25), bearing=deg2rad(90))
		location_2 = GeographicLocation(deg2rad(25), deg2rad(25), bearing=deg2rad(180))

		intersection = GeographicLocation.calculate_intersection(location_1, location_2)
		# print(intersection.to_decimal_degrees())

		# Expected result: The intersection is the same as the start points.
		self.assertAlmostEqual(intersection.latitude, deg2rad(25), places = 5)
		self.assertAlmostEqual(intersection.longitude, deg2rad(25), places = 5) #Failed test

		## maybe 3 more regular tests (pick random points/bearings, check their intersection on the website)
		# Pick two random points and bearings, calculate their intersection manually, and verify the results.
		# Example:
		location_1 = GeographicLocation(deg2rad(10), deg2rad(-20), bearing=deg2rad(45))
		location_2 = GeographicLocation(deg2rad(0), deg2rad(-25), bearing=deg2rad(115))

		intersection = GeographicLocation.calculate_intersection(location_1, location_2)
		# print(intersection.to_decimal_degrees())

		# Fill in the expected result after manual calculation
		self.assertAlmostEqual(intersection.latitude, deg2rad(-1.556389), places = 5)
		self.assertAlmostEqual(intersection.longitude, deg2rad(151.659722), places = 5) #Failed

		## Additional test 2
		# Another set of random points and bearings
		location_1 = GeographicLocation(deg2rad(30), deg2rad(40), bearing=deg2rad(135))
		location_2 = GeographicLocation(deg2rad(35), deg2rad(45), bearing=deg2rad(180)) #why can't I use 225 here?

		intersection = GeographicLocation.calculate_intersection(location_1, location_2)
		# print(intersection.to_decimal_degrees())

		# Expected result after manual calculation
		self.assertAlmostEqual(intersection.latitude, deg2rad(25.385), places = 5)
		self.assertAlmostEqual(intersection.longitude, deg2rad(45), places = 5) 

		## Additional test 3
		# Yet another set of points and bearings
		location_1 = GeographicLocation(deg2rad(-15), deg2rad(60), bearing=deg2rad(90))
		location_2 = GeographicLocation(deg2rad(-10), deg2rad(55), bearing=deg2rad(90))

		intersection = GeographicLocation.calculate_intersection(location_1, location_2)
		# print(intersection.to_decimal_degrees())

		# Expected result
		self.assertTrue(math.isnan(intersection.latitude))
		self.assertTrue(math.isnan(intersection.longitude)) 
		# self.assertAlmostEqual(intersection.latitude, deg2rad(2.52), places = 5)
		# self.assertAlmostEqual(intersection.longitude, deg2rad(159.453611), places = 5)

		# test from a failure in demo1:
		plane_location = GeographicLocation(0.40055306333269863, 2.060361181979306, bearing=0.7853981633974483)
		boundary_location = GeographicLocation(1.5707963267948966, 2.060361181979306, bearing=1.5707963267948966)
		print(plane_location.to_decimal_degrees())
		print(boundary_location.to_decimal_degrees())
		intersection = GeographicLocation.calculate_intersection(plane_location, boundary_location)
		print(intersection.to_decimal_degrees())

if __name__ == '__main__': 
	unittest.main() 