#!/usr/bin/env python3.4
"""
    orders and properties

    these will largely be an internal representation if we stick with the uuid
"""

from collections import defaultdict, OrderedDict
from uuid import uuid4
from weakref import WeakSet as wrs

class WeakSet(wrs):
    def __repr__(self):
        return repr(set([a for a in self]))

from ipython import embed

class RelationClass:  # there will be many different realtion classes with their own meanings (hello tripples), but the orders that they can take are limited
    """
        A relation class contains the adjascency matrix for a set of nodes and edges
        As well as the preorder for reachability to speed up sorting opperations
        It also defines the type or order that particular set of objects will have

        for adding members we will always reference against the 'upper' value that
        is above the added value...
    """
    # TODO it should be possible to put orders in other orders of less complexity since the members of the total order satisfy relations for the preorder
        # this will require a bit more work to make everything work as expected without doing silly things like nesting dicts
        # best option might be to use that Chained collection or something to fake join tables?
        # OR just create a new combined object???
    # TODO how to add nodes that are greater than other nodes (which actually happens frequently where there is *some* order)
    name = "FIXME ME DUMMY"
    def __init__(self, name):
        self.table = None
        self.name = name
        self.adj_matrix = None
        self.reachability = None

    @property
    def members(self):
        return [m for m in self.table]

    @property
    def values(self):  # FIXME
        return [v for v in self.table.values()]

    def items(self):  # FIXME massively broken
        try:
            return self.table.items()
        except AttributeError:
            return self.table

    def add_member(self, member, uppers = tuple(), lowers = tuple()):  # FIXME we could also use this function to just create a member without extra code?
        """
            when creating a new vertex for a given relation class or object participating in an order
            simply call rc.add_member(self) during object __init__
        """
        #add the member as a vertex
        # FIXME this MUST be a weakref

    #def del_member(self, member):  # we use weakrefs for order objects
        # will we ever use this?
        # FIXME deleting lowers is going to be MASSIVELY slow ;_;
        # but, I guess not a huge issue given expected usage?

    def add_pair(self, lower, upper):
        raise NotImplementedError('You need to inherit from this class and define this method.')

    def add_edge(self, start, end):
        pass

    def del_edge(self, start, end):
        pass

    # I think with this combination of things we can implement everything down to preorders by controling how <= >= and == interact
    def lt(self, a, b):
        raise NotImplementedError('You need to inherit from this class and define this method.')
    def le(self, a, b):
        raise NotImplementedError('You need to inherit from this class and define this method.')
    def eq(self, a, b):
        raise NotImplementedError('You need to inherit from this class and define this method.')
    def ne(self, a, b):
        raise NotImplementedError('You need to inherit from this class and define this method.')
    def gt(self, a, b):
        raise NotImplementedError('You need to inherit from this class and define this method.')
    def ge(self, a, b):
        raise NotImplementedError('You need to inherit from this class and define this method.')

    def __iter__(self):
        yield from self.table

    def __sorted__(self):
        # TODO toposort?

        uppers = set()
        [uppers.update(s) for s in self.table.values()]

        #starts=[node for node in depDict.keys() if node not in revDepDict.keys()]
        starts=[member for member in self.table if node not in uppers]  # FIXME make sure this is correct?
        L=[] #our sorted list
        while starts:
            node=starts.pop()
            L.append(node)
            discards=set()
            #print(depDict.keys(),node)
            try:
                for m in depDict[node]:
                    revDepDict[m].discard(node)
                    discards.add(m)
                    if not revDepDict[m]:
                        starts.append(m)
                depDict[node].difference_update(discards)
            except KeyError:
                pass #the node is a leaf and thus not in depDict
        check=set()
        (check.update(v) for v in depDict.values())
        (check.update(v) for v in revDepDict.values())
        if check:
            raise TypeError('NOT ACYCLIC!!')
        else:
            return L




        yield from sorted(self.table)

    def __repr__(self):
        out = ""
        for k, v in self.table.items():
            out += "%s : uppers = %s \n"%(k, set([m for m in v]))
        return out


class UnOrder(RelationClass):  # FIXME we may not need this? just don't define any pairs?
    """
        Unordered set with an equivalence relation
    """
    def __init__(self):
        self.table = set()  # this one does not use weak references since it is the equivalent of dict.keys()

    def add_member(self, member):
        self.table.add(member)

    def lt(self, a, b):
        return False
    def le(self, a, b):
        return False
    def eq(self, a, b):
        # TODO
        raise NotImplemented("TODO")
    def ne(self, a, b):
        # TODO
        raise NotImplemented("TODO")
    def gt(self, a, b):
        return False
    def ge(self, a, b):
        return False

class PreOrder(RelationClass):
    """
        reflexive
        transitive
        table defines the 'is covered by' set ie keys are a where a <= b implies b covers a
    """
    def __init__(self):
        self.table = defaultdict(WeakSet)
    

    def add_member(self, member, uppers = tuple(), lowers = tuple()):
        self.table[member]
        for upper in uppers:
            if upper in self.table:
                self.add_pair(member, upper)
                for even_more_upper in self.table[upper]:
                    self.add_pair(member, even_more_upper)
            else:
                raise ValueError('%s is not currently in this set.'%upper)

        for lower in lowers:
            self.add_pair(lower, member)

    def add_pair(self, lower, upper):
        self.table[lower].add(upper)

    def lt(self, a, b):
        return self.le(a, b)
    def le(self, a, b):
        if b in self.table[a]:  # that is a <= b
            return True
    def eq(self, a, b):  # FIXME how to deal with identity?
        return False
    def ne(self, a, b):
        return True
    def gt(self, a, b):
        return self.ge(a, b)
    def ge(self, a, b):
        return self.le(b, a)

class PartialOrder(PreOrder):
    """
        a preorder with the added
        antisymmetric property
    """
    def eq(self, a, b):  # FIXME how to deal with identity?
        if a in self.table[b] and b in self.table[a]:
            return True
    def ne(self, a, b):
        return not self.eq(a, b)

class TotalOrder(RelationClass):
    """
        this is a strict total order
        
        technically this could inherit from PartialOrder, but for performance
        reasons the internal implementation needs to be different
    """
    # FIXME insertion into this thing sucks... but really we should never be doing anything except appending?
    # TODO is self.table.find(a) < self.table.find(b)
    def __init__(self, table = None):
        self.table = table  # FIXME probably need to preserve hasability?
        if self.table == None:
            self.table = []  # gurantee uniqueness issue: object must be hashable, but we   FIXME this needs to be instance level fyi
        elif self.table:
            try: hash(self.table[0])
            except TypeError: raise TypeError('Order members must be hashable!')

    def add_member(self, member, upper = None):  # should this be __add_member__ so that we always use RCMember??
        """
            lower < member < upper lower is implicit
            insert happens AT the index of upper so the item at upper
            is bumped up one

            default behavior is to add to the end of the list if no upper is specced
        """

        if member not in self.table:  # FIXME type check this table?
            if upper == None:
                self.table.append(member)
            else:
                try:
                    index = self.table.index(upper)
                    self.table = self.table[:index] + [member] + self.table[index:]
                except ValueError:
                    raise ValueError('%s is not currently in this set.'%upper)

    def lt(self, a, b):
        return self.table.index(a) < self.table.index(b)
    def le(self, a, b):
        return self.table.index(a) <= self.table.index(b)
    def eq(self, a, b):
        return self.table.index(a) == self.table.index(b)
    def ne(self, a, b):
        return not self.eq(a, b)
    def gt(self, a, b):
        return self.lt(b, a)
    def ge(self, a, b):
        return self.le(b, a)

class RCMember:
    """ class for creating and accessing members of orders
    """
    def __init__(self, relation_class, uppers = tuple(), lowers = tuple(), uuid = None):
        self.uuid = uuid
        if not self.uuid:
            self.uuid = uuid4()

        self.relation_class = relation_class
        self.relation_class.add_member(self, uppers)

    @property
    def uppers(self):
        return self.relation_class.table[self]

    @property
    def lowers(self): # FIXME SLOW AS BALLS
        return [m for m, uppers_ in self.relation_class.items() if self in uppers_] 

    def add_upper(self, upper):
        self.relation_class.add_pair(self, upper)

    def add_lower(self, lower):
        self.relation_class.add_pair(lower, self)

    def __hash__(self):  # FIXME :/
        return hash(self.uuid)

    def __repr__(self):
        return "Member %s of order %s"%(self.uuid, self.relation_class.name)

    def __lt__(self, other):
        if self.relation_class.lt(self, other):
            return True
        else:
            return False

    def __le__(self, other):
        if self.relation_class.le(self, other):
            return True
        else:
            return False

    def __eq__(self, other):
        if self.relation_class.eq(self, other):
            return True
        else:
            return False

    def __ne__(self, other):
        if self.relation_class.eq(self, other):
            return False
        else:
            return True

    def __gt__(self, other):
        if self.relation_class.gt(self, other):
            return True
        else:
            return False

    def __ge__(self, other):
        if self.relation_class.ge(self, other):
            return True
        else:
            return False



class Property:  # FIXME should inherit from something like a time serries?
    """ a type level property object
        instances (values) in a property object should have a way of ordering themselves
        or raise an error if they fail
    """

    # TODO, for graphs, we we do not precompute reachability (the preorder) then implementing orderability calcs
    # will require repeatedly walking edges >_<, also, loads of work to add new orderable types
    # or we require a ton of memory using adj lists
    def __init__(self, name, instances):
        self.name = name
        self.instances = instances
        self.instance_type = None

    def __iter__(self):
        for instance in self.instances:
            yield instance

    def __repr__(self):
        return self.name+' with %s tokens'%len(self.instances)


class Prop_Computed(Property):
    """
        A property computed from a collection of other properties
    """
    def __init__(self, name, function, *properties):
        # how do we figure out the output type without a type system!?
        #expected_length = len(properties[0])  # FIXME, probably should raise a warning, otherwise assume that all props are same lenght, and alert that zip() goes w/ shortest, return ERROR or something?
        #for i, p in enumerate(properties):
            #if len(p) != expected_length:
                #raise ValueError('Property lengths do not match! Your %sth column (and possibly other) did not match.'%i)  # XXX TypeError? check numpy
        self.properties = properties

    def __iter__(self):
        for props in zip(*properties):  # I wonder if this is really inefficient
            yield function(*args)


class HasProperties:
    def __init__(self, properties):
        self.properties = properties

def main():
    p = PartialOrder()
    pom = RCMember(p)
    for _ in range(10):
        pom = RCMember(p,[pom])
    embed()

if __name__ == '__main__':
    main()
