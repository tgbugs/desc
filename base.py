#Type
#Occurence
#Token

#ideally we woud like to have a relationship between pure types saying 'ok my name for this is equal'

class renderable: #ideally we would like to dissociate this from the knowledge structure (heh)
    @property
    def renderPosition(self):
        return self.__render_position__

class univType:
    def __init__(self, stringIdentifier: str, relations: relations, properties: properties  ):
        self.uuid = getUUID()
        self.stringIdentifier = stringIdentifier
        self.properties = {}
        self.relations = {}

class objectType(univType):
    def __init__(self):
        pass

class propertyType(univType): #is this really the right way? well yes if we add objects
    def __init__(self):
        pass

class property:
    def __init__(self, propertyType: propertyType):
        self.type_ = propertyType
        pass

class relationType(univType):
    def __init__(self):
        pass

class relation:
    def __init__(self, relationType: relationType):
        self.type_ = relationType
