"""
    orders and properties
"""

class RelationClass:  # there will be many different realtion classes with their own meanings (hello tripples), but the orders that they can take are limited
    """
        A relation class contains the adjascency matrix for a set of nodes and edges
        As well as the preorder for reachability to speed up sorting opperations
        It also defines the type or order that particular set of objects will have
    """
    def __init__(self, name):
        self.name = name
        self.adj_matrix = None
        self.reachability = None

    def add_member(self, member):  # FIXME we could also use this function to just create a member without extra code?
        """
            when creating a new vertex for a given relation class or object participating in an order
            simply call rc.add_member(self) during object __init__
        """
        #add the member as a vertex

    def del_member(self, member):
        # will we ever use this?
        pass

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

class Unordered(RelationClass):
    """
        Unordered set with an equivalence relation
    """
    def lt(self, a, b):
        return False
    def le(self, a, b):
        return False
    def eq(self, a, b):
        return a == b if a == b else False
    def ne(self, a, b):
        return a != b if a != b else False
    def gt(self, a, b):
        return False
    def ge(self, a, b):
        return False
    

class RCMember:
    def __init__(self, relation_class):
        self.relation_class = relation_class
        self.realtion_class.add_member(self)

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
        self.instance_type = 

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


