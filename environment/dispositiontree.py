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
        if self.gap[0] < location < self.gap[1]:
            return self
        else:
            for child in children:
                if child.bounds[0] < location < child.bounds[1]:
                    return child
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
        '''This method can be called from the node in which an object is currently stored to change its disposition, returning a new_node, set tuple in which the set contains the unique integer ids of those objects with which the object could interact based on their former disposition with which the object no longer can in its new disposition.'''
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
        
