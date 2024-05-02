from environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict
from casebasedreasoner.mop import MOP, is_satisfied
import networkx as nx

def constraint_fn(constraint, filler, slots):
    return True


def not_constraint(constraint, filler, slots):
    # ensure filler is non-null
    if not filler:
        raise ValueError('Filler in not_constraint must be non-null.')
    return not is_satisfied(constraint.get_filler('object'), filler, slots)


def get_sibling(pattern, mop):
    '''Finds a sibling of MOP. It is only defined for instance MOPs.'''
    for abst in mop.absts: # goes up one layer in abstraction
        for spec in abst.specs: # looks at all specializations
            if spec.is_instance_mop() and spec != mop and not spec.is_abst('M-FAILED-SOLUTION'):
                return spec

class CaseBasedReasoner(ImprovedRomancerObject):
    ''''''

    def __init__(self, environment, time):
        super().__init__(environment, time)
        self.unlogged_attrs.append('mops')
        self.mops = LoggedDict(dict(), self, 'mops') # collection of all MOPs used by this case-based reasoner
        self.clear_memory(True) # install basic MOPs


    def calc_type(self, absts, slots):
        '''Determine whether a new MOP with absts and slots will be of type 'mop' (for an abstraction) or 'instance'. Returns value as a string.'''
        pass


    def add_mop(self, mop_name, absts={'M-ROOT'}, mop_type=None, slot_forms=[]):
        '''The equivilent of DEFMOP in Schank/Riesbeck. absts is a set of valid MOP names which are used to look up existing MOPs when creating this new MOP or direct references to abstraction MOPs.'''
        if mop_name in self.mops.keys():
            raise ValueError('MOP with name already exists: ', mop_name)
        absts_as_mops = {self.name_mop(n) if isinstance(n, str) else n for n in absts} # if isinstance(n, str) or isinstance(n, MOP)} # this should accept string names *or* MOP objects
        slots = self.forms_to_slots(slot_forms)
        if mop_type == None:
            mop_type = self.calc_type(absts, slots)
        new_mop = MOP(environment=self.environment, time=self.time, parent=self, mop_name=mop_name, absts=absts_as_mops, slots=slots, mop_type=mop_type)
        self.mops[mop_name] = new_mop
        for abst in absts_as_mops:
            new_mop.link_abst(abst) # link absts
        if mop_type == 'mop':
            self.install_abstraction(new_mop)
        elif mop_type == 'instance':
            self.install_instance(new_mop)
        return new_mop


    def remove_mop(self, name):
        '''Unlink MOP with name from any MOPs referring to it and delete it from the CBR's case library.'''
        if name in self.mops:
            mop = self.mops[name]

            # remove the MOP from all of its abstractions
            for abst in mop.absts:
                abst.specs.remove(mop)
            # remove the MOP from all of its specializations
            for spec in mop.specs:
                spec.absts.remove(mop)

            # delete the MOP from our lsit of MOPs
            self.mops.pop(name)
        else:
            raise ValueError(f"MOP {name} does not exist.")



    def install_instance(self, instance):
        ''''''
        pass


    def install_abstraction(self, mop):
        ''''''
        pass


    def forms_to_slots(self, slot_forms):
        '''Equivilent to FORMS->SLOTS in Schank/Riesbeck. This method accepts an interable of slot forms analagous to the tuples returned by the .items() method on Python dicts. If one of these slot forms already has the form [role, filler_mop], then it is already a slot. However, it can also have one or more additional slot forms following filler_mop. In this case, the slot forms are converted into slots recursively and the result is turned into a specialization of filler_mop, using slots_to_mop.'''
        pass


    def slots_to_mop(self, slots, absts, must_work=True):
        '''Equivilent to SLOTS->MOP is Schank/Riesbeck.'''
        # Ensure absts contains one or more MOPs and no non-MOPs
        pass
    
    def install_foundation_mops(self):
        '''Equivilent to the DEFMOPs in listing 3.21 of Schank/Riesbeck.'''
        self.add_mop(mop_name='M-EVENT')
        self.add_mop(mop_name='M-STATE')
        self.add_mop(mop_name='M-ACT')
        self.add_mop(mop_name='M-ACTOR')

        self.add_mop(mop_name='M-GROUP')
        self.add_mop(mop_name='M-EMPTY-GROUP', )
        self.add_mop(mop_name='I-M-EMPTY-GROUP', absts={'M-EMPTY-GROUP'}, mop_type='instance')

        self.add_mop(mop_name='M-FUNCTION')
        self.add_mop(mop_name='CONSTRAINT-FN', absts={'M-FUNCTION'})

        m_pattern = self.add_mop(mop_name='M-PATTERN', slot_forms=[['abst_fn', constraint_fn]])

        g_sibling = self.add_mop(mop_name='GET-SIBLING', absts={'M-FUNCTION'})

        self.add_mop(mop_name='M-CASE', slot_forms=[['old', m_pattern, ['calc_fn', g_sibling]]])

        self.add_mop(mop_name='M-ROLE')

        self.add_mop(mop_name='NOT-CONSTRAINT', absts={'CONSTRAINT-FN'})
        self.add_mop(mop_name='M-NOT', absts={m_pattern}, slot_forms=[['abst_fn', not_constraint]])

        self.add_mop(mop_name='M-FAILED-SOLUTION')
        

    def clear_memory(self, install_foundation_mops=True):
        '''This method clears all current MOPs from memory and installs a new M-ROOT MOP. If install_foundation_mops is True, then it also installs the basic MOPs as well.'''
        self.mops.clear()
        root = MOP(environment=self.environment, time=self.time, parent=self, mop_name='M-ROOT', absts=set(), specs=set(), slots=dict(), mop_type='mop')
        self.mops['M-ROOT'] = root
        if install_foundation_mops:
            self.install_foundation_mops()
        return self.name_mop('M-ROOT')


    def name_mop(self, name):
        '''This method finds a MOP associated with name in the CBR's case library and returns the associated MOP object.'''
        mop = self.mops[name]
        if mop.mop_name != name:
            raise ValueError('mop.name and key do not match')
        return mop

    def get_graph(self):
        '''This method returns a graph representation of the CBR's case library.'''
        G = nx.Graph() # make an empty graph, defined by its nodes and edges
        # ask the root node to make the graph
        root_mop = self.mops['M-ROOT']
        G = nx.union(G, root_mop.get_graph())

        return G
