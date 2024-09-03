import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from romancer.environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict
from casebasedreasoner.mop import MOP, is_satisfied
import networkx as nx
import random

class CBRError(Exception):
    pass

def constraint_fn(constraint, filler, slots):
    return True


def not_constraint(constraint, filler, slots):
    # ensure filler is non-null
    if not filler:
        raise ValueError('Filler in not_constraint must be non-null.')
    return not is_satisfied(constraint.get_filler('object'), filler, slots)


class CaseBasedReasoner(ImprovedRomancerObject):
    ''''''

    def __init__(self, environment, time):
        super().__init__(environment, time)
        self.mop_seq = 0 # Increasing with every addition/deletion
        self.unlogged_attrs.append('mops')
        self.mops = LoggedDict(dict(), self, 'mops') # collection of all MOPs used by this case-based reasoner
        self.clear_memory(True) # install basic MOPs
        self.decision_making_ability = None  # A number in the range 0..1. If None, use normal get_sibling
        self.rng = random.Random()  # Used by the stochastic mop selector

    def get_next_mop_seq(self):
        self.mop_seq += 1
        return self.mop_seq

    def set_stochastic_decision_making(self, decision_making_ability):
        # Setting this turns on the stochastic reasoner
        # Turn it on after the default and foundational mops are inserted
        self.decision_making_ability = decision_making_ability

    def calc_type(self, absts, slots):
        '''Determine whether a new MOP with absts and slots will be of type 'mop' (for an abstraction) or 'instance'. Returns value as a string.'''
        for abst in absts:
            if self.mops[abst].is_pattern():
                return 'mop'
        if not slots:
            return 'mop'
        for role, filler in slots.items(): # slots is a listof tuples(role, filler)
            if isinstance(filler, MOP) and not filler.is_instance_mop():
                return 'mop'
        return 'instance'


    def add_mop(self, mop_name=None, absts={'M-ROOT'}, mop_type=None, slots={}, is_default_mop=False, is_core_cbr_mop=False):
        '''The equivilent of DEFMOP in Schank/Riesbeck. absts is a set of valid MOP names which are used to look up existing MOPs when creating this new MOP or direct references to abstraction MOPs.'''
        # is_core_cbr_mop is the set of mops that are set up by default in all CBRs, per the book [implied to be a default]
        # is_default_mop are the rest of the mops that are populated by default for a given use case
        if mop_name and mop_name in self.mops.keys():
            raise ValueError('MOP with name already exists: ', mop_name)
        absts_as_mops = {self.name_mop(n) if isinstance(n, str) else n for n in absts} # if isinstance(n, str) or isinstance(n, MOP)} # this should accept string names *or* MOP objects 
        if mop_type == None:
            # raise MOPError("Do not add MOPs with mop_type=None.")
            mop_type = self.calc_type(absts, slots)
        new_mop = MOP(environment=self.environment, time=self.time, parent=self, mop_name=mop_name, absts=absts_as_mops, slots=slots, mop_type=mop_type, is_default_mop=is_default_mop, is_core_cbr_mop=is_core_cbr_mop)
        mop_name = new_mop.mop_name
        self.mops[mop_name] = new_mop
        for abst in absts_as_mops:
            new_mop.link_abst(abst) # link absts
        ## this ought not happen and may be redundant, it results in abstractless mops
        # if mop_type == 'mop':
        #     self.install_abstraction(new_mop)
        # elif mop_type == 'instance':
        #     self.install_instance(new_mop, check_legal=False)
        ##
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
            # remove the MOP specializations from this CBR
            for spec in mop.specs:
                self.remove_mop(spec.mop_name)
            # delete the MOP from our lsit of MOPs
            self.mops.pop(name)
        # else:
        #     raise ValueError(f"MOP {name} does not exist.")


    def forward_simulation(self, time):
        for mop in self.mops.values():
            mop.forward_simulation(time)
        super().forward_simulation(time)


    def rewind(self, time):
        for mop in self.mops.values():
            mop.rewind(time)
        super().rewind(time)

    
    def install_instance(self, instance):
        instance.refine_instance()
        twin = instance.get_twin()
        if twin:
            self.remove_mop(instance.mop_name)
            return twin
        elif instance.has_legal_absts():
            return instance
        else:
            self.remove_mop(instance.mop_name)
            return None
        

    def install_abstraction(self, mop):
        ''''''
        twin = mop.get_twin()
        if twin:
            self.remove_mop(mop.mop_name)
            return twin
        else:
            return mop.reindex_siblings()
        

   
    def forms_to_slots(self, slot_forms):
        '''Equivilent to FORMS->SLOTS in Schank/Riesbeck. This method accepts an iterable of slot forms analagous to the tuples returned by the .items() method on Python dicts. If one of these slot forms already has the form [role, filler_mop], then it is already a slot. However, it can also have one or more additional slot forms following filler_mop. In this case, the slot forms are converted into slots recursively and the result is turned into a specialization of filler_mop, using slots_to_mop.'''
        slots = []
        for slot_form in slot_forms:
            if isinstance(slot_form, str): # first slot form is a string -> it determines the mop type
                mop_type = slot_form
                slots.append(mop_type)
            else:
                role = slot_form[0]
                filler = slot_form[1]
                if len(slot_form) > 2: # there is a slot form defined by the rest of the slot form
                    mop = self.slots_to_mop(self.forms_to_slots(slot_form[2:]), [filler])
                    slots.append([role, mop])
                else: # complete slot
                    slots.append([role, filler])
        return slots


    def slots_to_mop(self, slots, absts, mop_type=None, must_work=True):
        '''Equivilent to SLOTS->MOP is Schank/Riesbeck.'''
        if len(slots) == 0 and len(absts) == 1:
            return absts[0]

        mop = self.add_mop(mop_name=None, absts=absts, slots=slots, mop_type=mop_type)

        #this code block may be redundant (gets called in add_mop)
        mop_type = mop.mop_type
        if mop_type == 'instance':
            return self.install_instance(mop)
        elif mop_type == 'mop':
            return self.install_abstraction(mop)
        if must_work:
            raise CBRError(f"Failed to convert slots {slots} to MOP of type {mop_type} with absts {absts}.")
    

    def install_foundation_mops(self, amygdala=None):
        '''Equivilent to the DEFMOPs in listing 3.21 of Schank/Riesbeck.'''

        self.add_mop(mop_name='M-EVENT', mop_type='mop', is_core_cbr_mop=True)
        self.add_mop(mop_name='M-STATE', mop_type='mop', is_core_cbr_mop=True)
        self.add_mop(mop_name='M-ACT', mop_type='mop', is_core_cbr_mop=True)
        self.add_mop(mop_name='M-ACTOR', mop_type='mop', is_core_cbr_mop=True)

        self.add_mop(mop_name='M-GROUP', mop_type='mop', is_core_cbr_mop=True)
        self.add_mop(mop_name='M-EMPTY-GROUP', mop_type='mop', is_core_cbr_mop=True)
        self.add_mop(mop_name='I-M-EMPTY-GROUP', absts={'M-EMPTY-GROUP'}, mop_type='instance', is_core_cbr_mop=True)

        self.add_mop(mop_name='M-FUNCTION', mop_type='mop', is_core_cbr_mop=True)
        self.add_mop(mop_name='CONSTRAINT-FN', absts={'M-FUNCTION'}, mop_type='mop', is_core_cbr_mop=True)

        m_pattern = self.add_mop(mop_name='M-PATTERN', slots={'abst_fn': constraint_fn}, mop_type='mop', is_core_cbr_mop=True)

        g_sibling = self.add_mop(mop_name='GET-SIBLING', absts={'M-FUNCTION'}, mop_type='mop', is_core_cbr_mop=True)

        self.add_mop(mop_name='M-CASE', slots={'old': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.get_sibling}, is_core_cbr_mop=True)}, mop_type='mop', is_core_cbr_mop=True)

        self.add_mop(mop_name='M-ROLE', mop_type='mop', is_core_cbr_mop=True)

        self.add_mop(mop_name='NOT-CONSTRAINT', absts={'CONSTRAINT-FN'}, mop_type='mop', is_core_cbr_mop=True)
        self.add_mop(mop_name='M-NOT', absts={m_pattern}, slots={'abst_fn': not_constraint}, mop_type='mop', is_core_cbr_mop=True)

        self.add_mop(mop_name='M-FAILED-SOLUTION', mop_type='mop', is_core_cbr_mop=True)
        

    def clear_memory(self, install_foundation_mops=True):
        '''This method clears all current MOPs from memory and installs a new M-ROOT MOP. If install_foundation_mops is True, then it also installs the basic MOPs as well.'''
        self.mops.clear()
        root = MOP(environment=self.environment, time=self.time, parent=self, mop_name='M-ROOT', absts=set(), specs=set(), slots=dict(), mop_type='mop', is_core_cbr_mop=True)
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

    def get_sibling(self, pattern, mop):
        '''Finds a sibling of MOP. It is only defined for instance MOPs.'''
        sibling = None
        if self.decision_making_ability is not None:
            sibling = self.choose_stochastic(mop, self.decision_making_ability, self.rng)
            print("Randomly chose " + sibling.mop_name)
        else:
            for abst in mop.absts: # goes up one layer in abstraction
                for spec in abst.specs: # looks at all specializations
                    if isinstance(spec, MOP) and spec.is_instance_mop() and spec != mop and not spec.is_abstraction(
                            self.name_mop('M-FAILED-SOLUTION')):
                        sibling = spec
        return sibling

    def get_mop_slots_r(self, mop_name, root_mop=None, curr_dict=None, depth=0):
        ''' For a given mop, return a map of all slot->slot_value.
         Do this recursively [ie, if a slot references another mop, go down into that]
          A higher-level dict value should not be overwritten by a lower level one '''
        if root_mop is None:
            root_mop = mop_name
        if curr_dict is None:
            curr_dict = dict()
        if mop_name not in self.mops:
            return curr_dict
        if depth > 200:
            raise CBRError("Recursively getting slots went too deep (cycle in graph?)")

        this_mop = self.mops[mop_name]
        recurse_mop_queue = []

        for slot in this_mop.slots:
            # Already have a key
            if slot in curr_dict:
                continue

            slot_val = this_mop.slots[slot]
            if slot_val == root_mop:
                continue
            if slot_val in self.mops:
                curr_dict[slot] = slot_val
                recurse_mop_queue.append(slot_val)
            elif isinstance(slot_val, MOP):
                mop_name = slot_val.mop_name
                curr_dict[slot] = slot_val.mop_name
                recurse_mop_queue.append(slot_val.mop_name)
            elif isinstance(slot_val, (str, int, float)):
                curr_dict[slot] = slot_val
            elif callable(slot_val):
                # print(f"Slot {slot} on mop {mop_name} is a callable. Fix plz")
                pass
            elif slot_val is None:
                pass
            else:
                print(f"Slot {slot} on mop {mop_name} has unknown slot type {type(slot_val)}")

        for r_mop in recurse_mop_queue:
            self.get_mop_slots_r(r_mop, root_mop, curr_dict, depth=depth + 1)

        return curr_dict

    def compare_two_mop_dicts(self, mop_1, mop_2):
        ''' Provide two dictionaries, representing two mops. get_mop_slots_r(mop_name) creates those dicts '''
        # Function is not required to be symmetric; it's reasonable to only calculate based on keys in mop_1
        # Function should return float >0, where 0 = "nothing in common", and higher numbers = "lots in common"
        # For now, naively calculate cosine distance. If values are strings, then they either match, or do not match.
        retval = 0.0
        for k1 in mop_1:
            if k1 not in mop_2:
                # No comparison to be done
                continue

            v1 = mop_1[k1]
            v2 = mop_2[k1]
            if not isinstance(v1, type(v2)):
                # Don't know how to compare this
                print(f"Don't know how to compare a {type(v1)} and a {type(v2)}")
                continue
            if isinstance(v1, str):
                if v1 == v2:
                    retval += 1
            elif isinstance(v1, (int, float)):
                retval -= pow((v1 - v2), 2)
            else:
                print(f"Don't know how to compare two {type(v1)}")

        return retval

    def normalise_mop_dicts(self, key_mop, other_dicts):
        for k in key_mop.keys():
            if isinstance(key_mop[k], (int, float)):
                min_val = 1000000
                max_val = -1000000
                for other_mop in other_dicts.keys():
                    other_dict = other_dicts[other_mop]
                    if k in other_dict:
                        min_val = min(min_val, other_dict[k])
                        max_val = max(max_val, other_dict[k])
                for other_mop in other_dicts.keys():
                    other_dict = other_dicts[other_mop]
                    if k in other_dict:
                        other_dict[k] = (other_dict[k] - min_val) / (max_val - min_val)
                key_mop[k] = (key_mop[k] - min_val) / (max_val - min_val)

    def get_all_siblings(self, mop):
        '''all siblings for a mop, including the mop itself'''
        siblings = []
        absts = mop.absts
        for abst in absts:  # goes up one layer in abstraction
            for spec in abst.specs:  # looks at all specializations
                if isinstance(spec, MOP) and spec.is_instance_mop() and spec != mop and not spec.is_abstraction(
                        self.name_mop('M-FAILED-SOLUTION')):
                    siblings.append(spec.mop_name)
        return siblings

    def compare_to_all_other_mops(self, mop_name):
        ''' Return a map of mop_name => similarity_score, showing how similar
        every other mop in this CBR is, to the mop requested '''
        this_mop_dict = self.get_mop_slots_r(mop_name)
        other_dicts = {}
        # In keeping with get_sibling: Only search through MOPs that come from the same abst as the one we're holding

        for other_mop in self.get_all_siblings(mop_name):
            if other_mop == mop_name:
                continue

            other_mop_dict = self.get_mop_slots_r(other_mop)
            other_dicts[other_mop] = other_mop_dict

        self.normalise_mop_dicts(this_mop_dict, other_dicts)

        comparisons = {}
        for other_mop in other_dicts:
            comparisons[other_mop] = self.compare_two_mop_dicts(this_mop_dict, other_dicts[other_mop])

        sorted_items = sorted(comparisons.items(), key=lambda x: x[1], reverse=True)
        sorted_mops = [item[0] for item in sorted_items]
        return sorted_mops

    def choose_stochastic(self, mop_name, decision_making_ability, rng):
        ''' for a given mop, and a given decision_making_ability , find a comparable mop. Pass a Random Number Generator '''
        # decision_making_ability should be in the range 0 [= no ability to make good decisions] to 1 [= will make best decision possible]
        # return self.mops['I-M-CRIME.123']
        sorted_mops = self.compare_to_all_other_mops(mop_name)
        # Choose uniformly, one from the top n mops, where n is derived from current decision making ability
        select_from_cnt = int(min(len(sorted_mops), max(1, (1.0-decision_making_ability) * len(sorted_mops))))
        # print(f"Decision Making {decision_making_ability}, Selected range: {select_from_cnt}")
        selected_idx = rng.randrange(select_from_cnt)
        return self.mops[sorted_mops[selected_idx]]
