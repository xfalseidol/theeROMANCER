import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.geodesic as cgeodesic
import shapely
from numpy import pi

min_long = 110
max_long = 130
min_lat = 15
max_lat = 35

# Create a feature for States/Admin 1 regions at 1:50m from Natural Earth
states_provinces = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_1_states_provinces_lines',
    scale='50m',
    facecolor='none')
    
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
ax.set_extent([min_long, max_long, min_lat, max_lat], crs=ccrs.PlateCarree())

ax.add_feature(cfeature.LAND)
ax.add_feature(cfeature.OCEAN)
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(states_provinces, edgecolor='gray')
# ax.add_feature(cfeature.LAKES, alpha=0.5)
# ax.add_feature(cfeature.RIVERS)

lon = 118.5517
lat = 24.7816

def plot_radar(lon, lat, outer_radius=250, inner_radius=50, n_points=1000):
    ax.plot(lon, lat, marker='o', color='red', linestyle='')
    circle_points = cgeodesic.Geodesic().circle(lon=lon, lat=lat, radius=outer_radius * 1000, n_samples=n_points, endpoint=False)
    geom = shapely.geometry.Polygon(circle_points)
    ax.add_geometries((geom,), crs=ccrs.PlateCarree(), facecolor='orange', alpha=0.4, edgecolor='none', linewidth=0)
    circle_points = cgeodesic.Geodesic().circle(lon=lon, lat=lat, radius=inner_radius * 1000, n_samples=n_points, endpoint=False)
    geom = shapely.geometry.Polygon(circle_points)
    ax.add_geometries((geom,), crs=ccrs.PlateCarree(), facecolor='red', alpha=0.4, edgecolor='none', linewidth=0)

triangle = Path([[-0.5, 0], [0.5, 0], [0, 0.5]])

plot_radar(lon, lat)

rotated_triangle = MarkerStyle(triangle).rotated(rad=-pi / 4)

ax.plot(119.43, 24.19, marker=rotated_triangle, color='blue', markersize=11, linestyle='')

ax.plot([118.75, 119.43], [23.5, 24.19], color='blue', linewidth=2, linestyle=':', transform=ccrs.Geodetic())
ax.plot([118.05, 118.75], [22.95, 23.5], color='blue', linewidth=2, transform=ccrs.Geodetic())

gl = ax.gridlines(draw_labels=True)
gl.top_labels = False
gl.left_labels = False

legend_elements = [Line2D([0], [0], color=(0, 0, 0, 0), marker='o', markerfacecolor='red', markeredgecolor='red', label='radar'),
                   Patch(facecolor='red', edgecolor='r', alpha=0.4, label='detection radius with ECMs'),
                   Patch(facecolor='orange', edgecolor='r', alpha=0.4, label='detection radius w/o ECMs'),
                   Line2D([0], [0], color=(0, 0, 0, 0), marker=triangle, markerfacecolor='blue', markersize=15, label='bomber'),
                   Line2D([0], [0], color='blue', linewidth=2, label='traversed flight path'),
                   Line2D([0], [0], color='blue', linewidth=2, linestyle=':', label='prospective flight path')]

ax.legend(handles=legend_elements)
    
plt.show()
