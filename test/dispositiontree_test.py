from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor, Stop
from romancer.environment.location import GeographicLocation
from numpy import deg2rad, rad2deg
from romancer.environment.dispositiontree import *
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from romancer.environment.object import RomancerObject
from romancer.environment.plane import BZero
from dill import dump, load


if __name__ == "__main__":
    # create a test disp tree object
    disp_tree_center = GeographicLocation(deg2rad(20), deg2rad(115), 0)
    disp_tree_resolution = 0.01
    centers, disp_tree_radius = generate_centers((-90, 90, -180, 180), disp_tree_resolution)
    disp_tree_radius = compute_radius_for_resolution(disp_tree_resolution)
    disp_tree_bounds = compute_bounds(disp_tree_center, disp_tree_radius)
    disp_tree = GeographicDispositionTree(center=disp_tree_center, radius=disp_tree_radius, bounds=disp_tree_bounds, resolution=disp_tree_resolution)

    disp_tree.make_child(GeographicLocation(deg2rad(20.6), deg2rad(113), 0), 0.003)
    disp_tree.make_child(GeographicLocation(deg2rad(20.6), deg2rad(113), 0), 0.003)
    disp_tree.children[0].make_children(0.0003)

    sup = SingleThreadSupervisor()
    env = SingleThreadEnvironment(supervisor=sup, disposition_tree=disp_tree, perception_engine=None)

    # test set disposition
    bomber_location = GeographicLocation(deg2rad(23.5), deg2rad(120.5), 30)
    bomber = BZero(environment=env, time=0, location=bomber_location, speed=600)
    disp_tree.set_disposition(bomber, bomber_location, resolution=0.01)

    bomber2_location = GeographicLocation(deg2rad(25), deg2rad(115), 30)
    # bomber2 = PlottableObject(location=bomber2_location)
    # disp_tree.set_disposition(bomber2, bomber2_location, resolution=0.0003)

    # bomber3_location = GeographicLocation(deg2rad(18), deg2rad(113), 30)
    # bomber3 = PlottableObject(location=bomber3_location)
    # disp_tree.set_disposition(bomber3, bomber3_location, resolution=0.0003)

    # bomber4_location = GeographicLocation(deg2rad(18.5), deg2rad(109), 30)
    # bomber4 = PlottableObject(location=bomber4_location)
    # disp_tree.set_disposition(bomber4, bomber4_location, resolution=0.0003)

    # bomber5_location = GeographicLocation(deg2rad(17.6), deg2rad(112.3), 60)
    # bomber5 = PlottableObject(location=bomber5_location)
    # disp_tree.set_disposition(bomber5, bomber5_location, resolution=0.0003)

    # test adjust disposition
    # disp_tree.children[0].children[7].adjust_disposition(bomber5, bomber5_location, 0.003)
    peers = disp_tree.identify_peers()

    # disp_tree.children[0].children[1].adjust_disposition(bomber2, bomber2_location, 0.01)
    # disp_tree.adjust_disposition(bomber2, bomber2_location, 0.003)
    print("Contents from Root:", disp_tree.contents)
    print("Peers from Root:", peers)

    # for child in disp_tree.children[0].children:
    #     print(child.id, child.contents)

    for node in disp_tree.descendent_nodes():
        print(f"Contents for Node {node.id}: {node.contents}")
        print(f"Peers for Node {node.id}: {node.identify_peers()}")

    filepath = Path.cwd() / 'sample_disptree.pkl'

    with open(filepath, 'wb') as f:
        dump(disp_tree, f)