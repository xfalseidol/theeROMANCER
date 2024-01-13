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
from redagent import BlipOnRadarScreen

states_provinces = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_1_states_provinces_lines',
    scale='50m',
    facecolor='none')

def plot_radar(rad, ax, n_points=1000):
    lon = rad2deg(rad.location.longitude)
    lat = rad2deg(rad.location.latitude)
    outer_radius=250
    inner_radius=50
    ax.plot(lon, lat, marker='o', color='red', linestyle='')
    if rad.on:
        outer_facecolor='orange'
        outer_edgecolor=None
        inner_facecolor='red'
        inner_edgecolor=None
        alpha=0.4
        linewidth=0
        linestyle=''
        leg_elms=[Line2D([0], [0], color=(0, 0, 0, 0), marker='o', markerfacecolor='red', markeredgecolor='red', label='radar'),
                    Patch(facecolor='red', edgecolor='r', alpha=0.4, label='detection radius with ECMs'),
                    Patch(facecolor='orange', edgecolor='r', alpha=0.4, label='detection radius w/o ECMs')]
        
    else:
        outer_facecolor='none' # None != 'none' in this context!
        outer_edgecolor='orange'
        inner_facecolor='none'
        inner_edgecolor='red'
        alpha=1.0
        linewidth=2.0
        linestyle='--'
        leg_elms=[Line2D([0], [0], color=(0, 0, 0, 0), marker='o', markerfacecolor='red', markeredgecolor='red', label='radar'),
                  Line2D([0], [0], color='red', linestyle='--', linewidth=2, label='radar (inactive) detection \nradius with ECMs'),
                  Line2D([0], [0], color='orange', linestyle='--', linewidth=2, label='radar (inactive) detection \nradius w/o ECMs')]
    circle_points = cgeodesic.Geodesic().circle(lon=lon, lat=lat, radius=outer_radius * 1000, n_samples=n_points, endpoint=False)
    geom = shapely.geometry.Polygon(circle_points)
    ax.add_geometries((geom,), crs=ccrs.PlateCarree(), facecolor=outer_facecolor, alpha=alpha, edgecolor=outer_edgecolor, linewidth=linewidth, linestyle=linestyle)
    circle_points = cgeodesic.Geodesic().circle(lon=lon, lat=lat, radius=inner_radius * 1000, n_samples=n_points, endpoint=False)
    geom = shapely.geometry.Polygon(circle_points)
    ax.add_geometries((geom,), crs=ccrs.PlateCarree(), facecolor=inner_facecolor, alpha=alpha, edgecolor=inner_edgecolor, linewidth=linewidth, linestyle=linestyle)

    return leg_elms


def plot_bomber(bom, ax):
    lon = rad2deg(bom.location.longitude)
    lat = rad2deg(bom.location.latitude)
    ber = rad2deg(bom.location.bearing)
    triangle = Path([[-0.5, 0], [0.5, 0], [0, 0.5]])
    rotated_triangle = MarkerStyle(triangle).rotated(deg=-ber)
    ax.plot(lon, lat, marker=rotated_triangle, color='blue', markersize=11, linestyle='')
    traj_longs = [rad2deg(l.location.longitude) for l in bom.loglist] + [lon]
    traj_lats = [rad2deg(l.location.latitude) for l in bom.loglist] + [lat]
    ax.plot(traj_longs, traj_lats, color='blue', linewidth=2, transform=ccrs.Geodetic())
    leg_elms = [Line2D([0], [0], color=(0, 0, 0, 0), marker=triangle, markerfacecolor='blue', markeredgecolor='blue', markersize=15, label='bomber')]
    if len(traj_longs) > 2:
        leg_elms.append(Line2D([0], [0], color='blue', linewidth=2, label='traversed flight path'))
    return leg_elms


def plot_scenario(radar, bom, disposition):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    min_lat, max_lat, min_long, max_long = [rad2deg(bound) for bound in disposition.bounds]
    ax.set_extent([min_long, max_long, min_lat, max_lat], crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(states_provinces, edgecolor='gray')

    gl = ax.gridlines(draw_labels=True)
    gl.top_labels = False
    gl.left_labels = False

    radar_leg_elms = plot_radar(radar, ax)
    bomber_leg_elms = plot_bomber(bomber, ax)

    ax.legend(handles=radar_leg_elms + bomber_leg_elms)
    
    plt.show()
    
# load supervisor and environment from demo1.py
filepath = 'demo1supervisor.pkl'

with open('demo1supervisor.pkl', 'rb') as f:
    sup = load(f)

bomber, radar = sup.environment.contents
screen = radar.children[0]
stump = sup.environment.disposition_tree

stump.bounds = deg2rad(21), deg2rad(27.5), deg2rad(115), deg2rad(122.5)

def maplogger(s):
    print('Processed watchlist item: ', s)
    if s.__class__.__name__ == 'ActivateRadar':
        plot_scenario(radar, bomber, stump)

sup.logger = maplogger

plot_scenario(radar, bomber, stump)

while len(sup.watchlist) > 0:
    sup.bring_watchlist_up_to_date()
    print("Updated watchlist: ", sup.watchlist)
    sup.process_next_watchlist_item()

plot_scenario(radar, bomber, stump)
    
