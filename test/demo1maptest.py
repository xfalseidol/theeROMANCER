from dill import load
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.geodesic as cgeodesic
import shapely
from numpy import pi, rad2deg, deg2rad

states_provinces = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_1_states_provinces_lines',
    scale='50m',
    facecolor='none')

def plot_scenario(radar, bomber, tree):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    min_lat, max_lat, min_long, max_long = [rad2deg(bound) for bound in tree.bounds]
    ax.set_extent([min_long, max_long, min_lat, max_lat], crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(states_provinces, edgecolor='gray')

    gl = ax.gridlines(draw_labels=True)
    gl.top_labels = False
    gl.left_labels = False

    radar_leg_elms = radar.plot(ax)
    bomber_leg_elms = bomber.plot(ax)

    ax.legend(handles=radar_leg_elms + bomber_leg_elms)

    plt.show()

# load supervisor and environment from demo1.py
filepath = 'demo1supervisor.pkl'

with open('demo1supervisor.pkl', 'rb') as f:
    sup = load(f)

bomber, radar = sup.environment.contents
screen = radar.children[0]
tree = sup.environment.disposition_tree

def maplogger(s):
    print('Processed watchlist item: ', s)
    if s.__class__.__name__ == 'ActivateRadar':
        plot_scenario(radar, bomber, tree)

sup.logger = maplogger

plot_scenario(radar, bomber, tree)