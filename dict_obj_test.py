import threading
class objectManager:
    def __init__(self):
        #TODO monolithic for all things or allow manager managers?
            #personally I would prefer monolitic for sake of simplicity
            #and frankly uint32 has more indexes than we will ever need
        self.addLock = threading.RLock()
        #self.__maxIndex = -1 #TODO do we need this? will it reduce computations? an add vs a subtract more or less equal for python
        self.__addIndex__ = 0 #DO NOT TOUCH WITHOUT addLock!
        self.index = {}
        #the main question is where the identifiers are going to come from?
            #the answer for this almost certainly is the data structure that
            #has uuids or the like baked in and references *could* work that way
            #BUT we don't need that for just the things in memory right now...
        #how do we call a bulk update eg when we switch an axis?
            #step one we are in hierarchical exploration mode
            #step two we are switch to axis mode with a set of objects, perhaps still in hier space

    def insert(self,value):
        try:
            self.addLock.acquire()
            self.index[self.__addIndex__] = value
            self.__addIndex__ += 1
            self.addLock.release()
            return self.__addIndex__ - 1
        except:
            self.addLock.release()
            raise

    #def update(self,key,value):

def main():
    om = objectManager()
    for i in range(10):
        print('before',om.__addIndex__)
        print('insert',om.insert('asdf'))
        print('after',om.__addIndex__)

if __name__ == '__main__':
    main()
