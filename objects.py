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

class relType(relatable):   #note that inheritance is being treated implicitly; different types should NOT use inheritance? or should they?
                            #the issue here is whether the code of the program is considered data or not >_<
    """ """
    def __init__(self , name:str , constraint = lambda left,right = None ):
        self.name = name
        self.constraint = constraint

class identityRelation(relType):



class relationship(relatable):
    def __init__(self, relType:relType, left:relatable , right:relatable , kwargs** ):
        super().__init__()
        self.type_ = relType(left #could just be a string?
        self.left = left #table + key OR the whole object?
        self.right = right #we *could* make this the whole object but that gets inefficient
        #passing left and right as ints seems like a bad idea... since we don't know the actual identity of the objects
        left.addRelation(self)



#initial types
IDENTITY_RELATION = relType('identity') #vs equality relation??
