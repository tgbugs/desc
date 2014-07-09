import unittest
#import numpy as np
import random
import string

class objectMaker(object):
    """ Class for making test data """
    type_ = "neuron in vitro epys"
    names = [
        "resting membrane potential",
        "axonal branches per um",
        "rheobase",
        "dendrite length",
        "spike rate",
        "dendritic branches per um",
        "total dendrite length",
    ]
    def __init__(self,type_,names,n):
        self.type_ = type_
        self.names = names
        self.container = {}
        self.index = ["%s"%uuid4() for _ in range(n)]
        for name in self.names:
            self.container[name] = np.linspace(-100,100,n)

    def getDimensions(self,names):

    def returnNames(self):
        return self.names

def makeData_uint(n):
    return [random.randint(0,2E64) for _ in range(n)]

def makeData_int(n):
    return [random.randint(-2E32,2E32) for _ in range(n)]

def makeData_float(n):
    return [random.uniform(-2E32,2E32) for _ in range(n)]

def makeData(n):  # TODO need to accomodate multiple dimensions of data, multiple time points/samples
    datMaker = random.choice([makeData_uint, makeData_int, makeData_float])
    return datMaker(n)

def makeDimNames(n):
    return [''.join([random.choice(string.ascii_lowercase+' ') for _ in range(random.randint(5,25))]) for _ in range(n)]

def makeTypes(n):
    return [''.join([random.choice(string.ascii_lowercase+' ') for _ in range(random.randint(5,25))]) for _ in range(n)]

def makeUUIDs(n):
    return ["%s"%uuid4() for _ in range(n)]


def makeDataObject(n):
    container = {}
    types = makeTypes(n)
    dimNames = makeDimNames(n)
    data1d = makeData(n)
    uuids = makeUUIDs(n)

    #metadata and data need to be separate!


    for _ in range(n):
        container[





class testMakeData(unittest.TestCase):
    def setUp(self):
        n = 10
        #generate requests
        self.names = makeNames(n)
        self.uuids = makeUUIDs(n)
    def test_processDataRequest(self):
        pass
    def test_addNewData(self):
        pass
    def test_things(self):
        pass

def main():
    pass

if __name__ == "__main__":
    main()
    unittest.main()
