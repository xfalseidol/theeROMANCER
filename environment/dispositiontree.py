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

        # if granularity / num_children > minimum_granularity:
        #     self.make_children()


    def make_children(self):
        latitude_width = (self.bounds[1] - self.bounds[0]) / self.num_children
        for i in range(self.num_children):
            new_bounds = (self.bounds[0] + latitude_width * i, self.bounds[0] + latitude_width * (i + 1), self.bounds[2], self.bounds[3])
            new_granularity = self.granularity / self.num_children
            child = GeographicDispositionTree(new_bounds, new_granularity, self.minimum_granularity, self, self.num_children)
            self.children.append(child)


    def make_child(self, location):
        '''
        Make a new child node containing the given location.
        Returns the new child node or the child that contains the location already.
        '''
        # TODO: loop over this node's children, check to see if the location is within
        #       the bounds of any child. if the location is contained in a child already, 
        #       return that child node.

        # TODO: we should not make a child if the new granularity will be below the minimum granularity
        #       in this case, we should return the node containing this location (use find_child)
        
        latitude_width = (self.bounds[1] - self.bounds[0]) / self.granularity_reduction_factor
        for i in range(self.granularity_reduction_factor):
            left_bound = self.bounds[0] + latitude_width * i
            right_bound = self.bounds[0] + latitude_width * (i + 1) 
            if left_bound <= location.latitude <= right_bound:
                new_bounds = (left_bound, right_bound, self.bounds[2], self.bounds[3])
        new_granularity = self.granularity / self.granularity_reduction_factor
        new_child = GeographicDispositionTree(bounds=new_bounds, granularity=new_granularity, minimum_granularity=self.minimum_granularity, parent=self, granularity_reduction_factor=self.granularity_reduction_factor)
        self.children.append(new_child)

        return new_child


    def find_child(self, location):
        '''
        Finds the lowest-level child containing this location.
        If the location is on the boundary, return this node.
        If the location is within the boundary, find and return the child containing this location.
        If the location is outside the bounds, return None.
        '''
        # location_on_boundary = False
        # if location_on_boundary:
        #     return self

        if self.location_in_bounds(location):
            if len(self.children) == 0:
                return self
            # look for the child containing this location
            child = None
            for c in self.children:
                # recursively find the child node
                child = c.find_child(location)
                if child:
                    return child 

            # otherwise, the location does not belong to any descendent, so we create a child containing the location
            # TODO: determine the size of the new child
            # TODO: determine if we should even be making new children -- how big will they be? how can we be sure they don't overlap with other children?
            # TODO: do we even need this?
            # new_child = GeographicDispositionTree()
            # self.children.append(new_child)
            return None  

        else: # location out of bounds
            return None

    def location_in_bounds(self, location):
        '''
        If the node is a root node, we need to determine if the location is within the bounds.
        If the node is a child node, we only need to determine if the location is between two latitudes.
        '''
        if self.bounds[0] <= location.latitude <= self.bounds[1] and self.bounds[2] <= location.longitude <= self.bounds[3]:
            return True

        return False


    def set_disposition(self, obj, location, granularity):
        '''
        Used for setting initial disposition of the parent node of a disposition tree.
        Shifting an object should be done with adjust_disposition.
        '''
        if self.parent:
            raise Exception('Cannot set disposition starting at non-root node.') # TODO: define appropriate Exception class for this
        else:
            # find the lowest-level node containing this location
            node = self.find_child(location)

            # find the node with the appropriate granularity:
            
            # case 1: the node we found is "too high" in the tree
            # then, make children below this node until the goal granularity is
            # between the parent's granularity and the child's granularity
            # TODO: try to reduce the complexity of this code by removing the if statement, somehow
            if granularity < node.granularity:
                child_granularity = node.granularity / node.granularity_reduction_factor
                while granularity < child_granularity:
                    node = node.make_child(location)
                    print("Added child: Node", node.id)
                    child_granularity = node.granularity / node.granularity_reduction_factor

            # case 2: the node we found is "too low" in the tree
            # traverse back up the tree from the lowest-level child
            # until the correct granularity is found
            # TODO: try to reduce the complexity of this code by removing the if statement, somehow
            if granularity > node.granularity:
                parent_granularity = node.granularity * node.granularity_reduction_factor
                while granularity > node.granularity:
                    if node.parent:
                        node = node.parent
                        parent_granularity = node.granularity * node.granularity_reduction_factor
                    else:
                        raise Exception('Specified granularity is too high: given granularity {granularity} is higher than root node granularity {node.granularity}.')

            # append the object to the correct node's contents
            node.contents.append(obj)


    def adjust_disposition(self, obj, location, granularity):
        '''
        Removes the object from this nodes contents.
        Sets the disposition of the correct new node.
        Returns the new node and a set containing the difference between old peers and new peers.
        '''
        if obj not in self.contents:
            raise Exception('Cannot adjust disposition of object not in node.')

        self.contents.remove(obj)
        old_peers = {o.id for o in self.identify_peers()}

        p = self
        while p.parent: # find root
            p = p.parent

        new_node = p.set_disposition(obj, location, granularity)
        new_peers = {o.id for o in new_node.identify_peers(obj)}
        return new_node, old_peers.difference(new_peers)


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


    def identify_peers(self):
        '''
        Finds and returns all objects that may interact with one another.
        These objects are:
          - objects contained in this node
          - objects contained in any ancestor
          - objects contained in any descendent
        '''
        peers = set()

        # include objects in this node's contents
        peers.update(self.contents)

        # include objects in this node's ancestors' contents
        p = self
        while p.parent:
            p = p.parent
            peers.update(p.contents)

        # include objects in this node's descendents' contents
        for descendent in self.descendent_nodes:
            peers.update(descendent.contents)

        return peers


    def remove(self, obj):
        '''
        Remove obj from disposition tree. 
        May only be called on the root node.
        This method assumes multiple nodes can contain the same object,
        and will remove the object from all nodes in the tree.
        '''          
        if self.parent:
            raise Exception('Cannot remove object from non-root node.') # TODO: define appropriate Exception class for this
        
        # remove the object from the contents of this node
        if obj in self.contents:
            self.contents.remove(obj)

        # remove the object from all children
        for child in self.children:
            child._remove(obj)


    def _remove(self, obj):
        '''
        Removes object from contents of node and all children.
        Should not be called outside of this class.
        '''
        if obj in self.contents:
            self.contents.remove(obj)
        for child in self.children:
            child._remove(obj)


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
        
        
    def identify_peers(self, obj):
        '''This method uses the disposition tree to identify all of an object's peers--those objects with which it might interact.'''
        peers = list() # maybe this should be a set?
        cur = self
        while cur.parent: # capture all items in curent node and its ancestors
            for o in cur.contents:
                peers.append(o)
                cur = cur.parent
        desendents = list()
        self.descendent_nodes(desendents)
        for d in desendents:
            for o in d.contents:
                peers.append(o)
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
        
