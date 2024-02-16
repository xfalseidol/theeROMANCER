# NH Custom Exceptions
class DispositionError(Exception):
    """Base class for errors in the disposition tree."""
    pass

class LocationError(Exception):
    """Raised when a location is outside the bounds or on an invalid boundary."""
    pass

class GranularityError(Exception):
    """Raised when an operation would result in a granularity that doesn't make sense."""
    pass

class DispositionStump():

    '''A disposition tree consisting solely of one (root) node, but adhering to the intended API. A placeholder during development but also potentially useful for scenarios that either largely discount physical space or are so simple as to not require full functionality.'''

    def __init__(self, bounds):
        self.bounds = bounds # tuple containing the left and right bounds of the one-dimensional space
        self.parent = None
        self.contents = list() # objects currently stored in root


    def set_disposition(self, obj, location, granularity):
        if self.bounds[0] <= location <= self.bounds[1]:
            self.contents.append(obj)
            return self
        else:
            raise ValueError('Location outside bounds.')


    def adjust_disposition(self, obj, location, granularity):
        if self.bounds[0] <= location <= self.bounds[1]:
            return self
        else:
            raise ValueError('Location outside bounds.')

        
    def identify_peers(self, obj):
        peers = self.contents.copy()
        peers.remove(obj)
        return peers
        

    def remove(self, obj):
        self.contents.remove(obj)

        
class GeographicDispositionStump(DispositionStump):
    '''Like DispositionStump, but with latitude and longitude bounds to work with GeographicLocation. GeographicDispositionStump.bounds takes the form of a (low_latitude, high_latitude, low_longitude, high_longitude) tuple with locations in radians.'''

    def set_disposition(self, obj, location, granularity):
        lowlat, highlat, lowlong, highlong = self.bounds
        if lowlat <= location.latitude <= highlat and  lowlong <= location.longitude <= highlong:
            self.contents.append(obj)
            return self
        else:
            raise ValueError('Location outside bounds.')


    def adjust_disposition(self, obj, location, granularity):
        lowlat, highlat, lowlong, highlong = self.bounds
        if lowlat <= location.latitude <= highlat and  lowlong <= location.longitude <= highlong:
            return self
        else:
            raise ValueError('Location outside bounds.')


class GeographicDispositionTree():
    '''
    The nodes of a geographic disposition tree. 
    Helps provide efficient clustering of items which may have interactions.
    '''
    id_number = 1

    def __init__(self, bounds, granularity = 1000, minimum_granularity = 10, parent = None, granularity_reduction_factor = 4):
        self.bounds = bounds # bounds has form (low_latitude, high_latitude, low_longitude, high_longitude)
        self.parent = parent
        self.children = list()
        self.contents = list()
        self.id = GeographicDispositionTree.id_number
        GeographicDispositionTree.id_number += 1

        self.granularity = granularity # this represents the diameter of the geographic region in meters
        self.minimum_granularity = minimum_granularity # this represents the width of the smallest possible child region in meters
        self.granularity_reduction_factor = granularity_reduction_factor # this determines the granularity of the child of a node


    def is_on_boundary(self, location): #NH implement the is_on_boundary method
        """
        Determines if the given location is within a tolerance beyond the boundary of this node.
        :param location: The location to check.        
        :return: True if on the boundary or close enough past it; False otherwise.
        """
        # a direct change to the lower and upper bounds for latitude/longitude (to account for something being "just over the border")
        ## TODO: brainstorm with Ed how to calculate tolerance
        tolerance = self.granularity / self.granularity_reduction_factor * 0.001 # tolerance is a number of radians, scaled by the next smallest granularity
        lat_on_boundary = (self.bounds[0] - tolerance <= location.latitude <= self.bounds[0]) or (self.bounds[1] <= location.latitude <= self.bounds[1] + tolerance)
        lat_in_boundary = (self.bounds[0] - tolerance <= location.latitude <= self.bounds[1] + tolerance)
        long_on_boundary = (self.bounds[2] - tolerance <= location.longitude <= self.bounds[2]) or (self.bounds[3] <= location.longitude <= self.bounds[3] + tolerance)
        long_in_boundary = (self.bounds[2] - tolerance <= location.longitude <= self.bounds[3] + tolerance)
        return (lat_on_boundary and long_in_boundary) or (lat_in_boundary and long_on_boundary)
        
        
    def make_children(self):
        latitude_width = (self.bounds[1] - self.bounds[0]) / self.num_children
        for i in range(self.num_children):
            new_bounds = (self.bounds[0] + latitude_width * i, self.bounds[0] + latitude_width * (i + 1), self.bounds[2], self.bounds[3])
            new_granularity = self.granularity / self.granularity_reduction_factor #NH
            if new_granularity < self.minimum_granularity or self.is_on_boundary(location):
                # Avoid creating a new child if below minimum granularity or if the location is on a boundary.
                return self.find_child(location) #NH
            child = GeographicDispositionTree(new_bounds, new_granularity, self.minimum_granularity, self, self.num_children)
            self.children.append(child)


    def make_child(self, location):
        '''
        Makes and returns a new child node containing the given location, or returns the highest-level child already containing the node
        '''
        # NH Check existing children first: if a child of this node already contains the location, return it
        for child in self.children:
            if child.location_in_bounds(location):
                return child

        # NH Ensure not to create a child below minimum granularity: if the new granularity would be too small, this node is the child we want
        new_granularity = self.granularity / self.granularity_reduction_factor
        if new_granularity < self.minimum_granularity: # or self.is_on_boundary(location):
            return self
        
        # Create a new child if needed.
        latitude_width = (self.bounds[1] - self.bounds[0]) / self.granularity_reduction_factor
        for i in range(self.granularity_reduction_factor):
            left_bound = self.bounds[0] + latitude_width * i
            right_bound = self.bounds[0] + latitude_width * (i + 1) #NH
            if left_bound <= location.latitude <= right_bound:
                new_bounds = (left_bound, right_bound, self.bounds[2], self.bounds[3])
                new_child = GeographicDispositionTree(new_bounds, new_granularity, self.minimum_granularity, self, self.granularity_reduction_factor) #NH                
                self.children.append(new_child) #NH
                return new_child #NH

        # Error handling if no valid child is found (should not happen). #NH
        raise LocationError("Location couldn't be placed in any child segment.") 


    def find_child(self, location): #NH commented out orignal code
        '''
        Tries to find the lowest-level child containing this location.

        If the location is on/near the boundary, return this node.
        If the location is within the boundary, find and return the child containing this location.
        If the location is outside the bounds, return None.
        '''
        # the tolerance will be the next smallest granularity from this node
        for child in self.children:
            if child.location_in_bounds(location):
                return child.find_child(location)

        if self.is_on_boundary(location) or self.location_in_bounds(location):
            return self

        if not self.location_in_bounds(location):
            raise LocationError(f"Requested location {location} falls too far outside bounds {self.bounds} of this node.")

        return None


    def location_in_bounds(self, location):
        '''
        If the node is a root node, we need to determine if the location is within the bounds.
        If the node is a child node, we only need to determine if the location is between two latitudes.
        '''
        if self.bounds[0] <= location.latitude <= self.bounds[1] and self.bounds[2] <= location.longitude <= self.bounds[3]:
            return True

        return False


    def set_disposition(self, obj, location, granularity): #NH commented out original code
        '''
        Used for setting initial disposition of the parent node of a disposition tree.
        The obj will be place in the contents of the currently existing, lowest-granularity node, whose granularity is higher than granularity
        Shifting an object should be done with adjust_disposition.
        :param obj: object to place into the disposition tree
        :param location: location of the object, used to place the object at the right node
        :param granularity: minimum acceptable granularity for the node obj will belong to
        Returns the node we attach the object to
        '''
        if self.parent:
            raise DispositionError('Cannot set disposition starting at non-root node.')

        # Find or create the node with the appropriate granularity
        try:
            node = self.find_child(location)
        except LocationError:
            print("The object ", obj.uid, " is outside the bounds of this disposition tree.")
            print("TODO: send a message to alert the supervisor")
            return

        # walk up the tree until the node's granularity is smaller than granularity, or stop at the root node
        while node and node.granularity < granularity and node.parent:
            node = node.parent # if the node's granularity is too small, walk up the tree

        if node.granularity < granularity:
            raise GranularityError(f'Object granularity too large. Node granularity: {node.granularity}, Requested granularity: {granularity}')
        
        node.contents.append(obj)
        return node


    def adjust_disposition(self, obj, location, granularity): #entire bottom changed
        '''
        Removes the object from this nodes contents.
        Sets the disposition of the correct new node, if a correct node exists.
        Returns the new node and a set containing the difference between old peers and new peers.
        Otherwise, it returns None.
        '''
        if obj not in self.contents:
            raise LocationError('Object not found in the current node.')
            
        old_peers = self.identify_peers(obj)

        self.remove(obj)
        new_node = self.set_disposition(obj, location, granularity)

        new_peers = self.identify_peers(obj)
        peer_difference = old_peers.difference(new_peers)

        return new_node, peer_difference


    def descendent_nodes(self):
        '''
        Collects and returns all descendents of this node.
        '''
        descendents = []

        for child in self.children:
            # append this child
            descendents.append(child)
            # append this child's children
            descendents += child.descendent_nodes()

        return descendents


    def identify_peers(self, obj):
        '''
        Finds and returns all objects that may interact with one another.
        These objects are:
          - objects contained in this node
          - objects contained in any ancestor
          - objects contained in any descendent
        '''
        peers = set()

        # Include objects in this node's contents.
        peers.update(self.contents)

        # Include objects in this node's ancestors' contents.
        ancestor = self.parent
        while ancestor:
            peers.update(ancestor.contents)
            ancestor = ancestor.parent

        # Include objects in this node's descendants' contents.
        descendents = self.descendent_nodes()
        for descendent in descendents:
            peers.update(descendent.contents)

        # Ensure the original object is not considered its own peer.
        peers.discard(obj)

        return peers


    def remove(self, obj):
        '''
        Remove obj from disposition tree. 
        May only be called on the root node.
        This method assumes multiple nodes can contain the same object,
        and will remove the object from all nodes in the tree.
        '''          
        if self.parent:
            raise LocationError('Cannot remove object from non-root node.')  # NH Use custom exception for clarity
        
        self._remove(obj)  # NH Call the internal _remove method to handle actual removal process


    def _remove(self, obj): #NH changed all
        '''
        Removes object from contents of node and all children.
        Should not be called outside of this class.
        '''
        if obj in self.contents:
            self.contents.remove(obj)
        for child in self.children:
            child._remove(obj)  # Recursively remove obj from all descendants


    def next_anticipated_disposition_change(self, obj):
        '''Identify future time at which obj will leave this disposition tree node based on its current speed and trajectory.'''
        if obj.speed == 0: # disposition will never change
            return None
        actual_speed = obj.speed / 3600.0 # speed in km/s
        
        # use bearing to determine which boundaries plane will cross first
        lowlat, highlat, lowlong, highlong = obj.dispositions[0].bounds
        if obj.location.bearing > pi: # heading west
            longbound = lowlong
        elif obj.location.bearing < pi: # heading east
            longbound = highlong
        elif obj.location.bearing == 0 or obj.location.bearing == pi: # heading north or south
            longbound = None
        if obj.location.bearing < pi / 2 or 1.5 * pi < obj.location.bearing: # heading north
            latbound = highlat
        elif  pi / 2 < obj.location.bearing < 1.5 * pi: # heading south
            latbound = lowlat
        elif obj.location.bearing == pi / 2 or obj.location.bearing == 1.5 * pi: # heading east or west
            latbound = None

        # use scipy to find root

        if latbound:
            x0 = obj.location.distance(GeographicLocation(latitude=latbound, longitude=obj.location.longitude, bearing=obj.location.bearing))
            delta_d1 = root_scalar(lambda d: obj.location.destination_point(d).latitude - latbound, x0 = x0, x1 = x0 + x0 * 0.01).root
        else:
            delta_d1 = inf
        if longbound:
            x0 = obj.location.distance(GeographicLocation(latitude=obj.location.latitude, longitude=longbound, bearing=obj.location.bearing))
            delta_d2 = root_scalar(lambda d: obj.location.destination_point(d).longitude - longbound, x0 = x0, x1 = x0 + x0 * 0.01).root
        else:
            delta_d2 = inf

        delta_d = min(delta_d1, delta_d2)
        
        delta_t = delta_d / actual_speed    
        return obj.time + delta_t


    def __repr__(self):
        return_str = ""
        return_str += f"Parent: {self.id}\n"
        children_ids = ""
        for c in self.children:
            children_ids += str(c.id)
            children_ids += " "
        return_str += f"Children: {children_ids}\n"
        return_str += "\n"

        for c in self.children:
            return_str += str(c)

        return return_str


class OneDimensionalDispositionTree():

    '''The root node for a one-dimensional disposition tree. The purpose of disposition trees is to provide efficient clustering of items that may have interactions.'''

    def __init__(self, bounds, granularity, gap_width, parent, granularity_reduction_factor = 10, gap_reduction_factor = 1):
        self.bounds = bounds # tuple containing the left and right bounds of the one-dimensional space
        self.parent = parent
        self.children = list() # child nodes of root
        self.contents = list() # objects currently stored in root
        self.granularity = granularity
        self.gap = ((bounds[1] - bounds[0]) / 2 - gap_width / 2, (bounds[1] - bounds[0]) / 2 + gap_width / 2) # gap in which objects that would otherwise be lower in the tree are contents of this node


    def find_or_make_child(self, location):
        '''Find the child into which a location falls, or if it does not exist, create it. Returns that child node.'''
        # check to see if the location of interest lies on the border
        # if it does, then the location belongs to this tree
        if self.gap[0] < location < self.gap[1]:
            return self
        # if it doesn't lie on the border, the location may belong to an existing child or we may need to make a new one
        else:
            # check if the location is within the bounds of any of the children
            for child in children:
                if child.bounds[0] < location < child.bounds[1]:
                    return child
            # location is 
            if location <= self.gap[0]:
                new_bounds = (self.bounds[0], self.gap[0]) # left
            else:
                new_bounds = (self.bounds[1], self.gap[1]) # right
            # new_gap = ((new_bounds[1] - new_bounds[0]) / 2 - (gap_width / gap_reduction_factor) / 2, (new_bounds[1] - new_bounds[0]) / 2 + (gap_width / gap_reduction_factor) / 2)
            new_child = OneDimensionalDispositionTree(new_bounds, granularity / granularity_reduction_factor, gap_width / gap_reduction_factor, self, granularity_reduction_factor, gap_reduction_factor)
            self.children.append(new_child)
            return new_child


    def set_disposition(self, obj, location, granularity):
        '''This method is intended to accomplish initial placement of an object in the disposition tree. Shifting an object that already exists in the disposition tree should be accomplished using adjust_disposition.'''
        if self.parent:
            raise Exception('Cannot set location starting at non-root node.') # TODO: define appropriate Exception class for this
        else:
            if self.gap[0] < location < self.gap[1]:
                self.contents.append(obj)
                return self
            else:
                while child.granularity > granularity:
                    child = self.find_or_make_child(location, granularity) # returns current node 
                    if granularity > child.granularity or child.gap[0] < location < child.gap[1]:
                        child.contents.append(obj)
                        return child
                    else:
                        child = child.find_or_make_child(location)

                        
    def descendent_nodes(self, nodes):
        '''Collects all descendent nodes that currently exist of this node.'''
        nodes = list()
        for c in self.children:
            nodes.append(c)
            c.dependent_nodes(nodes)
        return nodes
        
        
    def identify_peers(self, obj): #NH Implement the logic for identifying peers based on the definition provided
        '''This method uses the disposition tree to identify all of an object's peers--those objects with which it might interact.'''
        peers = set()

        # Include objects in this node's contents.
        peers.update(self.contents)

        # Include objects in this node's ancestors' contents.
        ancestor = self.parent
        while ancestor:
            peers.update(ancestor.contents)
            ancestor = ancestor.parent

        # Include objects in this node's descendants' contents.
        descendents = self.descendent_nodes()
        for descendent in descendents:
            peers.update(descendent.contents)

        # Ensure the original object is not considered its own peer.
        peers.discard(obj)

        return peers
        
        
    def adjust_disposition(self, obj, location, granularity):
        if obj in self.contents:
            if location in self.gap:
                return self, set() # same node
            else:
                self.contents.remove(obj)
                old_peers = {o.id for o in self.identify_peers(obj)}
        else:
            raise Exception('Cannot adjust disposition of object not in node.')
        p = self.parent
        while p.parent: # find root
            p = p.parent
        new_node = p.set_disposition(obj, location, granularity)
        new_peers = {o.id for o in new_node.identify_peers(obj)}
        return new_node, old_peers.difference(new_peers)
        
            
    def remove(self, obj):
        '''Remove obj from disposition tree. This method should only be called on the root node.'''
        def remove_inner(node):
            if obj in node.contents:
                node.contents.remove(obj)
            else:
                for child in node.children:
                    remove_inner(child)
                    
        if self.parent:
            raise Exception('Cannot set location starting at non-root node.') # TODO: define appropriate Exception class for this
        else:
            remove_inner(self)
        
