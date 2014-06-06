import threading
from itertools import count
class objectManager(dict):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.__counter__ = count(0,1) #this is threadsafe
        self.__lastIndex__ = -1
        #self.idx = 0 #test for monotonicity
        #TODO monolithic for all things or allow manager managers?
            #personally I would prefer monolitic for sake of simplicity
            #and frankly uint32 has more indexes than we will ever need
        #the main question is where the identifiers are going to come from?
            #the answer for this almost certainly is the data structure that
            #has uuids or the like baked in and references *could* work that way
            #BUT we don't need that for just the things in memory right now...
        #how do we call a bulk update eg when we switch an axis?
            #step one we are in hierarchical exploration mode
            #step two we switch to axis mode with a set of objects, perhaps still in hier space

    def insert(self,value):
        key = self.__counter__.__next__()
        if key > self.__lastIndex__: #if some other thread has already updated, don't reset to a lower value
            self.__lastIndex__ = key #this prevents problems with other threads resetting __lastIndex__
        self.__setitem__(key, value)
        return key

    def __setitem__(self,key,value):
        if key > self.__lastIndex__:
            raise KeyError('Use insert to add new objects!') #self.update will just be a nasty mess
        else:
            #assert self.idx <= self.__lastIndex__, 'not monotonic!'
            #self.idx = self.__lastIndex__
            super().__setitem__(key,value)

import cProfile, pstats, io
sortby = 'cumulative'
def Before():
    global pr, s
    pr = cProfile.Profile()
    s = io.StringIO()
    pr.enable()

def After(name='WHO KNOWS!'):
    global pr, s
    pr.disable()
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(name,s.getvalue())


def OMvsDict():
    reps = 999999
    om = objectManager()
    for i in range(0,10,3):
        print('before',om.__addIndex__)
        print('insert',om.insert('asdf'))
        print('after',om.__addIndex__)

    om = objectManager()
    Before()
    for i in range(reps):
        om.insert(i)
    After('om')
        
    om2 = {}
    def helper(i): #turns out locks are super expensive... who knew!
        om2[i] = i
        1+1
        1-1

    Before()
    for i in range(reps): #roughly 5x faster
        helper(i)
        #om2[i] = i #weirdness dude
    #[om2.update({i:i}) for i in range(reps)]
    After('dict')
    print(len(om2))

def countIsThreadsafe():
    om = objectManager()
    #om = {}
    def nasty(n):
        num = 111
        for i in range(num*n,num*(n+1)):
            #om[i]=i
            om.insert(i)

    tnum = 9999
    threads = []
    [threads.append(threading.Thread(target=nasty, args=(i,))) for i in range(tnum)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    print(om.idx)
    #print(om)
    #print(om.__addIndex__)

def addPoses():
    import numpy as np
    om = objectManager()
    #om = {}

    #Before()
    bases = np.random.randn(99999,3) #as long as we stage inserts or do it in a different thread everything should be ok
    #After('gens')

    def helper(b):
        om[99999999999999] = b

    Before()
    for b in bases:
        helper(b)
        #print(out,b) #crap
    #[om.update({-1:b}) for b in bases]
    After('inserts')
    #print(om)

    
def main():
    countIsThreadsafe()
    #OMvsDict()
    addPoses()



if __name__ == '__main__':
    main()
