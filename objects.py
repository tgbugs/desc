#the minimal 'object' is a pair of uuids, the first references the identity relation, the second shall be another uuid
#the UUID for the identity relation shall tell the program to return the UUID of its associated pair
#the (idfunc_uuid,uuid) tuple shall be implicit...
#to allow for references to an object in human language a second

#mappings to literals/symbols, 'representation' mapping... mapping to symbolic token...
#In THEORY representations should have their own uuid? well then we get immediately into type occurence token issues

#in this case we have to use functions because we are mapping from one set to another eg: set of universals to the set of english words
#well not necesarily... relations between types... but grrrr
#"The universal referred to by the english words 'a chair'" "The universal referred to in english by "the function from a to b" hrm...
#ALL this is a representation, don't get bogged down


#basic types, we probably need a hierarchy as usual...
    #relation <- somehow this seems most fundamental...
        #how do we construct types out of relations
            #an 'object' is a member of a type if it has the requisite properties to belong to it
                #sometimes the requisite property is having been assigned said type... data is probably 'so and so has assigned this type'
                #thus we have different types of type membership... which must be defined, yay goedel!
            #thus our need for fuzzy types?
    #quantitative property
    #representation
        #symbolic (text numbers etc aka literals) 'to a computer everything is a number'
        #visual
        #auditory
        #etc
        #probably going to need to subtype these based on the function we use to output them eg text vs pictures
    #asdf

#note: open scene graph, panda3d <- apparently panda3d can be build w/ python3 support

from uuid import uuid4

class relatable:
    def __init__(self):
        self.relations = {}
        self.uuid = uuid4() #this is a uuid object, tokens of relateables point to the type but do not inherit, so this is ok
    def addRelation(self,relationship):
        self.relations.add(relationship)
    def delRelation(self,uuid):
        return 
    def relations(self):
        return
    def relationTypes(self):
        return
    def hasRelationType(self):
        return

    #def __hash__(self): #may want to make this the UUID?

                            #the issue here is whether the code of the program is considered data or not >_<
class relType(relatable):   #note that inheritance is being treated implicitly; different types should NOT use inheritance? or should they?
    """ """
    def __init__(self , name:str , constraint = lambda left,right = False ):
        self.name = name
        self.constraint = constraint #sanity check?

    def __call__(self , left , right ):
        return self.constraint( left , right )

#class identityRelation(relType): #we do not do this because we want to
#pretend that these classes are actually types so we can make fake generics




class relationship(relatable):
    def __init__(self, relType:relType, left:relatable , right:relatable , kwargs** ):
        super().__init__()
        self.type_ = relType(left,right) #could just be a string?
        self.left = left #table + key OR the whole object?
        self.right = right #we *could* make this the whole object but that gets inefficient
        #passing left and right as ints seems like a bad idea... since we don't know the actual identity of the objects
        left.addRelation(self)



#initial types
IDENTITY_RELATION = relType('identity') #vs equality relation??


#the problem is that BOTH parent and child objects need to know about eachother AND how they relate to eachother so we need pointers in both directions AND to the relationship
#namely occurences and tokens need to know... I guess we could user the MRO and use python's inheritance...

#ologs?
#what is the minimal data stucture needed to state that a diagram commutes?

class Object:
    """ ologs! """
    def __init__(self, type_:str ):
        self.type_ = type_

class Morphism:
    def __init__(self, origin:Object, target:Object, aspect:str ):
        self.origin = origin
        self.target = target
        self.aspect = aspect

class PathEquivalence:
    #could simply declare pairs of morphisms to be equivalent?
    pass

class CommutativeDiagram:
    def __init__(self, objects:set(Object) , morphisms:set(Morphism) , evidence:ObjectInstance = None ):
        self.


###
#   Types of sets of objects, annotations to cope with pre/partial/total orders and sampling rates
###

class tokenAccess:  # FIXME I'm basically asking for an ORM here
    """ inherit from this and set properties you want and the index to use """
    COLUMNS = []
    INDEX = None
    def __init__(self, index, coll_source):
        for name in self.COLUMNS:
            setattr(self, name, coll_source[name][index])


#what I really want is the structure that will let me reason about how to present a set points
    #any object can be a member of multiple orders (the whole point of this system)
    #we need another layer before we get to the points...

class orderedObject:
    def __init__(self, points, order):
        """
            len(points) == len(order)
        """
        pass

        

class setObject:
    """ basically, vectorize everything, and do corrispondence with the ordering
        this is actually the opposite of vectorization for SIMD but whatever
    """
    #collection of things  # try not to reinvent the database please >_<
    #functional order  # XXX because type is consistent per set, vectorize everything and use the index to manage cross type corrispondence
        #defaults to the python implementation with no gurantees from reproducibility
        #these sets have their use cases but basically force functions that opperate
        #on themassume that all members of the set are of the same type
        #BASICALLY python has solved this, *args, **kwargs, or arg called repeatedly
    #actual order
        #defaults to no order, that is, there are no expectations for indexing behavior

    #FUNCTIONAL = [
        #'none',  # functions with a single arg
        #'labeled',  # dict of indexes (inefficient, but whatever)  # FIXME no, this is confounding because labled implies types in the set are different
    #]
    def __init__(self, collection, ordering = None):
        self.collection = colleciton
        self.ordering = ordering
    



###
#   Simple data objects
###

def universalType:
    representation_types = [
        'unicode',  # followed by exhaustive symbolic systems and their input/output methods
        'bytes',  # for any other things...
        'other symbols that *can* be represented by bytes',
    ]

    def __init__(self, uuid):
        self.uuid = uuid

def uiDataObject:
    def __init__(self, uuid, type_, None )
        self.uuid = uuid
        self.type_ = type_  # this gives access to the 'universal' by which all related types can be found
        self.relations = relations

def dataTokenObject(object):  # tokens themselves are also types that need to be selectable and searchable for filtering and interacting
    """ data tokens delegate all their major relations to their parent type
        except for stuff like links to experiment metadata and nitty gritty
    """
    # this is really just a row in a table
    def __init__(self, uuid):
        pass


def dataObject(object):
    """ no relations here for the time being """
    def __init__(self, type_name, uuid, property_names, property_dims):
        self.type_name = type_name
        self.uuid = uuid
        self.property_names = property_names
        self.property_dims = property_dims

    def add_instance(self,instance):
        """ instances are *sort of* sub type relations """
        pass

    def add_token(self,token):
        pass

    def tokenMaker(self):
        #class tokenClass(object):
        tokenClass = type( self.type_name+"_token",
                          dataTokenObject, {},
        )

        return tokenClass



class dataObject:
    properties = dProperties()
    


class dProperties:
    measured = {}
    computed = {}


##
#  THIRD TIME'S THE CHARM!
##


class dObject:  # TODO needs the HasProperties decorator...
    def __init__(self, type_, relationship_tables):
        self.type_ = type_  # XXX aka name in ontology
        self.active_relation = 'default'  # FIXME this probably should access some global state manager for the UI????
        self.relations = {}  # a dict of instances as a function of a given relationship not sure if best idea...
        self.Properties = {}  # TODO these are what we really need for the UI moreso than the instances or tokens themselves
        self.instProperties = {}  # based on the active set of relations
        self.tokenProperties = {}  # based on the active set of relations

    @property
    def instances(self):
        """ returns a list of other child dObjects
        """
        return self.relations[self.active_relation]

    @property
    def tokens(self):
        #TODO this probably will need to be recursive? and depend on the relationship
        #FIXME recursion :/ probably need to override this somewhere
        out = []
        for obj in self.relations[self.active_relation]:  #TODO one fix might just be to have tokens exist under this but they themselves have no children
            out.extend(obj.tokens)
        return out

    @property
    def instProperties(self):
        out = []
        for i in self.instances:
            out.extend(i.Properties)

        return out



