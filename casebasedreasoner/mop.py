from environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict

# class MOPSlot(ImprovedRomancerObject):
#     '''A structure to contain role, filler information. The reason that MOPs are not implemented with ordinary Python slots is that they can be dynamically updated and their slots have associated filler MOPs.'''

#     def __init__(self, environment, time, role, filler):
#         super().__init__(environment, time)
#         self.unlogged_attrs.append('role')
#         self.role = role # e.g., 'actor', 'object'
#         self.filler = filler # can be any MOP


def is_satisfied(constraint, filler, slots):
    '''Returns True if filler satisfies the conditions specified by constraint. A constraint is satisfied if:

    1. The contraint is False or None.
    2. The constraint is a Pattern MOP whose abstraction function returns True when called with constraint, filler, and slots.
    3. The constraint is an abstraction of the filler.
    4. The constraint is an instance MOP and the filler is empty. The slot source can inherit the instance when needed.
    5. The constraint has at least one slot, the filler is not empty, and all of the slots are satisfied by the slots of the filler.

    Slotless abstractions are treated specially, because they have no slots to constrain what can go under them.'''
    
    if not constraint:
        return True
    elif constraint.is_pattern():
        fn = constraint.inherit_filler('abst_fn')
        return fn(constraint, filler, slots)
    elif filler.is_abst(constraint):
        return True
    elif constraint.is_instance_mop() and not filler:
        return True # not right, should be equivilent of `(FILLER (SLOTS-ABSTP CONSTRAINT FILLER))`
    else:
        return False


def mop_equal(mop1, mop2):
    '''Returns mop1 if mop1 and mop2 are the same.'''
    if mop1.includes(mop2) and mop2.includes(mop1):
        return mop1
    

class MOP(ImprovedRomancerObject):
    '''An implementation of Roger Schank's concept of Memory Organization Packages (MOPs) designed to work with ROMANCER's simulation paradigm.

    This implementation is based on chapter three of Christopher Riesbeck and Roger Schank, _Inside Case-Based Reasoning_ (Lawrence Erlbaum, 1989).'''

    def __init__(self, environment, time, parent, mop_name, absts=None, specs=None, slots=None, mop_type='instance'):
        super().__init__(environment, time)
        if not absts:
            absts = set()   
        if not specs:
            specs = set()
        if not slots:
            slots = {} 
            
        self.unlogged_attrs.append('parent')
        self.parent = parent # parent is case-based reasoner containing collection of associated MOPs
        self.unlogged_attrs.append('mop_name')
        self.mop_name = mop_name # string giving name of MOP
        self.absts = LoggedSet(absts, self, "absts") # the immediate abstractions of this MOP--those that are exactly one abstraction link above it
        # self, data, parent, varname
        self.specs =  LoggedSet(specs, self, "specs") # the immediate specializations of this MOP--those that are exactly one abstraction link below it
        self.slots = LoggedDict(slots, self, "slots") # dict associating roles (names) with filler structures (MOPs)
        self.unlogged_attrs.append('mop_type')
        self.mop_type = mop_type # 'instance' or 'mop'


    def is_abst_mop(self):
        '''Returns True if this MOP is an abstraction MOP.'''
        return self.mop_type == 'mop'


    def is_instance_mop(self):
        '''Returns True if this MOP is an instance MOP.'''
        return self.mop_type == 'instance'


    def is_abst(self, mop):
        '''Returns True if mop is an abtraction, not necessarily immediate, of self (specialization).'''
        return mop in self.mop_all_absts


    @property
    def mop_all_absts(self):
        '''Returns all the abstractions of this MOP, not limited to immediate abstractions.'''
        all_absts = set()
        for abst in self.absts:
            all_absts.update(abst.mop_all_absts)
        return all_absts


    def calc_all_absts(self):
        '''Calculates all the abstractions of this MOP, not limited to immediate abstractions.'''
        pass
    

    def is_pattern(self):
        '''Returns True if MOP is specialization of 'M-PATTERN'. Pattern matching MOPs are used to hold pattern matching and role filling information.'''
        m_pattern = self.parent.name_mop('M-PATTERN')
        return self.is_abst(m_pattern) # Perhaps M-PATTERN should be distinct Python subclasses of MOP


    def is_group(self):
        '''Returns True if MOP is specialization of 'M-GROUP'. Group MOPs are used to hold groups of MOPs, e.g., the group of steps in a recipe or the group of events in a fight.'''
        m_pattern = self.parent.name_mop('M-GROUP')
        return self.is_abst(m_pattern) # Perhaps M-GROUP should be distinct Python subclasses of MOP


    def add_role_filler(self, role, filler):
        if not isinstance(filler, MOP):
            raise TypeError('Filler is not MOP')
        self.slots[role] = filler
        return filler


    def role_filler(self, role):
        if role not in self.slots:
            raise KeyError('MOP lacks slot: ', slot)
        else:
            return self.slots[role]


    def link_abst(self, abst):
        # assert abst.is_abst() # equivilent of "insist" macro in Schank/Riesbeck code
        assert not abst.is_abst(self) # don't create circular reference
        if not self.is_abst(abst): # abst is not currently abstract of self
            self.absts.add(abst) # make abst abstraction of self
            abst.specs.add(self) # make self specialization of abst
            return self


    def unlink_abst(self, abst):
        if self.is_abst(abst): # abst is currently an abstraction of self
            self.absts.remove(abst) # remove abst as abstraction of self
            abst.specs.remove(self) # remove self as specialization of abstract
            return self
        

    def inherit_filler(self, role):
        for abst in self.mop_all_absts:
            try:
                filler = abst.get_filler(role)
            except KeyError:
                filler = None
            if filler:
                return filler


    def get_filler(self, role):
        try:
            filler = self.role_filler(role)
        except KeyError:
            filler = None
        if filler:
            return filler
        else:
            inheritance = self.inherit_filler(role)
            if inheritance and inheritance.is_instance_mop():
                return inheritance
            elif inheritance.is_abst(self.parent.name_mop('M-FUNCTION')):
                fn = inheritance.get_filler('calc_fn')
                if fn:
                    new_filler = fn(inheritance, self)
                    if new_filler:
                        self.add_role_filler(role, new_filler)


    def path_filler(self, path):
        mop = self
        for role in path:
            mop = mop.get_filler(role)
            if not mop:
                return mop
        return mop
        

    def slots_satisfied_by(slot_source):
        '''Returns True if every slot in self is 'satisfied' by corresponding slot in slot_source. Slot_source is usually an instance, but it can also be a dict of slots. The slot fillers in self are treated as constraints on the slot fillers in slot_source. Equivilent of SLOTS-ABSTP in Schank/Riesbeck.'''
        if self.abst_mopp() and len(self.slots) > 0:
            for role, filler in self.slots.items():
                if isinstance(slot_source, MOP):
                    s = is_satisfied(filler, slot_source.get_filler(role), slot_source)
                else:
                    s = is_satisfied(filler, slot_source[role], slot_source) # slot_source is dict
                if not s:
                    return False
            return True


    def includes(self, mop2):
        '''Returns self if it is of the same mop_type and includes every slot in mop2. Self can have slots not in mop2.'''
        if self.mop_type == mop2.mop_type:
            for role in mop2.slots.keys():
                if self.get_filler(role) != mop2.slots[role]:
                    return False
            return self


    def get_twin(self):
        '''Returns the first MOP that it can find in memory that is equal to self, if any.'''
        for abst in self.absts:
            for spec in abst.specs:
                if spec is not self:
                    if mop_equal(spec, self):
                        return spec


    def refine_instance(self):
        '''Takes each abstraction of self, which should be an instance, and tries to replace it with one or more specializations of the abstraction. It repeats this process until all abstractions of self are as specialized as possible.'''
        if self.mop_type != 'instance':
            raise ValueError('Cannot refine abstraction MOP')
        else:
            for abst in self.absts:
                pass


    def mops_abstp(self, mops_list):
        '''Looks at each MOP in mops_list. If the MOP can abstract self, a link from self to the MOP is made. returns True if at least one such MOP was found.'''
        if self.mop_type != 'instance':
            raise ValueError('Cannot refine abstraction MOP')
        else:
            refinement = False
            for mop in mops_list:
                if mop.slots_satisfied_by(self):
                    refinement = True
                    self.link_abst(mop)
            return refinement

    
    def has_legal_absts(self):
        '''This method is used to support the install_instance method on the case-based reasoner class. It unlnks every immediate abstraction of instance that is not a legal place to put instance, and returns whatever immediate abstractions are left.'''
        for abst in self.absts:
            if not abst.is_legal_abst(self):
                self.unlink_abst(abst)
        return self.absts


    def is_legal_abst(self, abst):
        '''Returns True if abst is a legal place to put self, i.e., abst is not slotless and does not have abstractions below it.'''
        if len(self.slots) > 0:
            for spec in self.specs:
                if not spec.is_instance_mop():
                    return False
            return True
        else:
            return False


    def reindex_siblings(self):
        '''This method is used to support the install_abstraction method on the case-based reasoner class. It finds all instances that are immediate specializations of the immediate abstractions of self. The instances are unlinked from their abstractions and relinked to self. Returns self.'''
        for abst in self.absts:
            for spec in abst.specs:
                if spec.is_instance_mop() and self.slots_satisfied_by(spec):
                    spec.unlink_abst(abst)
                    spec.link_abst(self)
        return self


    # this is probably superfluous for this implementation
    def group_size(self):
        '''If self is a group MOP, return the number of slots it contains. Returns None otherwise.'''
        if self.is_group():
            return len(self.slots)


    def group_to_list(self):
        '''Returns a list of the members of the group.'''
        if not self.is_group():
            raise TypeError('Non-group MOP cannot be converted to list.')
        l = list()
        for i in self.slots.keys():
            l.append(self.get_filler(i))
        return l
        

    def __repr__(self):
        return self.mop_name


    def __str__(self):
        return self.mop_name


    
