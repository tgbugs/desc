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

#XXX NOTE: currently this cannot be used effectively to track the positions of relations, which have 2 ends
    #at best realtions should probably be referenced as a tuple of MonoDict index values...
    #we might be able to do fast type inference, but then a relation could reference a relation and the
    #whole thing will come tumbling down
#basically when we deal with the relations between relations we will have to think a little bit harder about this

from itertools import count

class MonoDict(dict): #TODO this might work really well as one of those shared index dicts!??
    """ threadsafe dict with .insert that gurantees monotonicity """
    def __init__(self,*args,**kwargs):
        super(MonoDict,self).__init__(*args,**kwargs)
        self.__counter__ = count(0,1) #this is threadsafe
        self.__lastIndex__ = -1
        #self.idx = 0 #test for monotonicity
    def insert(self,value):
        """ insert an object into the manager and get back its identifier
        """
        key = next(self.__counter__)
        if key > self.__lastIndex__: #ensure monotonicity
            self.__lastIndex__ = key
        self.__setitem__(key, value)
        return key

    def TOOSLOW__setitem__(self,key,value): #FIXME we might just want to completely ignore this since we want fast updates?
        if key > self.__lastIndex__:
            raise KeyError('Use insert to add new objects!') #self.update will just be a nasty mess
        else:
            #assert self.idx <= self.__lastIndex__, 'not monotonic!'
            #self.idx = self.__lastIndex__
            super().__setitem__(key,value)

###
#   Tests
###
if __name__ == '__main__':
    import threading
    from prof import Prof
    p = Prof()

    def OMvsDict():
        reps = 999999
        om = MonoDict()
        for i in range(0,10,3):
            print('before',om.__addIndex__)
            print('insert',om.insert('asdf'))
            print('after',om.__addIndex__)

        om = MonoDict()
        p.Before()
        for i in range(reps):
            om.insert(i)
        p.After('om')
            
        om2 = {}
        def helper(i): #turns out locks are super expensive... who knew!
            om2[i] = i
            1+1
            1-1

        p.Before()
        for i in range(reps): #roughly 5x faster
            helper(i)
            #om2[i] = i #weirdness dude
        #[om2.update({i:i}) for i in range(reps)]
        p.After('dict')
        print(len(om2))

    def countIsThreadsafe():
        om = MonoDict()
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

        #print(om)
        #print(om.__addIndex__)

    def addPoses():
        import numpy as np
        om = MonoDict()
        #om = {}

        bases = np.random.randn(999999,3) #as long as we stage inserts or do it in a different thread everything should be ok

        p.Before()
        for b in bases:
            #helper(b)
            om.insert(b)
            #print(out,b) #crap
        #[om.update({-1:b}) for b in bases]
        p.After('inserts')
        #print(om) #super slow for big dicts

    def main():
        countIsThreadsafe()
        #OMvsDict()
        addPoses()

if __name__ == '__main__':
    main()
