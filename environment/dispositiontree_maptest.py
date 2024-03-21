from dill import load
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Patch
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.geodesic as cgeodesic
import shapely
from dispositiontree import GeographicDispositionTree, generate_centers, compute_bounds
from location import GeographicLocation
from object import PlottableObject, RomancerObject
from numpy import pi, rad2deg, deg2rad
import unittest
import matplotlib.patheffects as pe
from matplotlib.patches import Circle
from scipy.optimize import root_scalar


states_provinces = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_1_states_provinces_lines',
    scale='50m',
    facecolor='none')

def plot_point(ax, location, color):
        lon = rad2deg(location.longitude)
        lat = rad2deg(location.latitude)
        ax.plot(lon, lat, marker='o', color=color, linestyle='')

def plot_line_to(ax, loc1, loc2):
	lon1 = rad2deg(loc1.longitude)
	lat1 = rad2deg(loc1.latitude)
	lon2 = rad2deg(loc2.longitude)
	lat2 = rad2deg(loc2.latitude)	
	ax.plot([lon1, lon2], [lat1, lat2], color='black', alpha=0.3, linestyle='dashed')

def plot_scenario(map_bounds, disp_tree):
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
	
	ax.set_extent(map_bounds, crs=ccrs.PlateCarree())

	ax.add_feature(cfeature.LAND)
	ax.add_feature(cfeature.OCEAN)
	ax.add_feature(cfeature.COASTLINE)
	ax.add_feature(cfeature.BORDERS, linestyle=':')
	ax.add_feature(states_provinces, edgecolor='gray')
	gl = ax.gridlines(draw_labels=True)

	# test plot all
	disp_tree.plot_all(ax)

	# test plot peers
	# disp_tree.children[0].plot_peers(ax, color='darkgreen')

	# test next_anticipated_disp_change
	## test 1
	obj_of_interest = disp_tree.contents[0]
	disp_change_t = obj_of_interest.next_anticipated_disposition_change()
	# plot the next anticipated disposition change
	delta_t = disp_change_t - obj_of_interest.time
	distance_traveled = obj_of_interest.speed / 3600 * delta_t
	future_location = obj_of_interest.location.destination_point(distance_traveled)
	plot_point(ax, future_location, 'black')
	plot_line_to(ax, obj_of_interest.location, future_location)

	## test 2
	obj_of_interest = disp_tree.children[0].contents[0]
	disp_change_t = obj_of_interest.next_anticipated_disposition_change()
	# plot the next anticipated disposition change
	delta_t = disp_change_t - obj_of_interest.time
	distance_traveled = obj_of_interest.speed / 3600 * delta_t
	future_location = obj_of_interest.location.destination_point(distance_traveled)
	plot_point(ax, future_location, 'black')
	plot_line_to(ax, obj_of_interest.location, future_location)

	## test 3
	obj_of_interest = disp_tree.children[0].children[7].contents[0]
	disp_change_t = obj_of_interest.next_anticipated_disposition_change()
	# plot the next anticipated disposition change
	delta_t = disp_change_t - obj_of_interest.time
	distance_traveled = obj_of_interest.speed / 3600 * delta_t
	future_location = obj_of_interest.location.destination_point(distance_traveled)
	plot_point(ax, future_location, 'black')
	plot_line_to(ax, obj_of_interest.location, future_location)
	
	gl.top_labels = False
	gl.left_labels = False

	plt.show()


def to_decimal_degrees(tuple_in_radians):
	list_in_degrees = [0] * len(tuple_in_radians)
	for i in range(len(tuple_in_radians)):
		list_in_degrees[i] = rad2deg(tuple_in_radians[i])
	return tuple(list_in_degrees)


def map_test_main():
	map_bounds = (100, 130, 7.5, 30)

	filepath = 'sample_disptree.pkl'

	with open(filepath, 'rb') as f:
	    disp_tree = load(f)

	plot_scenario(map_bounds, disp_tree)


# class PeerTests(unittest.TestCase):
# 	def 

if __name__ == '__main__': 
	do_maptest = True
	if do_maptest:
		map_test_main()
