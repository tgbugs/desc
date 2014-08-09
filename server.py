#!/usr/bin/env python3.4

import pickle
import ssl
import sys
from asyncio import get_event_loop
from uuid import uuid4
from collections import defaultdict, deque

import numpy as np
from ipython import embed

from defaults import CONNECTION_PORT, DATA_PORT
from test_objects import makeSimpleGeom
from request import FAKE_PREDICT


#fix sys module reference
sys.modules['core'] = sys.modules['panda3d.core']


#TODO logging...

class responseMaker:  # TODO we probably move this to its own file?
    npoints = 9999
    def __init__(self):
        #setup at connection to whatever database we are going to use
        pass

    def make_response(self, request):
        # TODO so encoding the collision nodes to a bam takes a REALLY LONG TIME
        # it seems like it might be more prudent to serialize to (x,y,z,radius) or maybe a type code?
        # yes, the size of the bam serialization is absolutely massive, easily 3x the size in memory
        # also if we send it already in tree form... so that the child node positions are just nested
        # it might be pretty quick to generate the collision nodes
        n = self.npoints
        np.random.seed()  # XXX MUST do this otherwise the same numbers pop out over and over, good case for cache invalidation though...
        positions = np.cumsum(np.random.randint(-1,2,(n,3)), axis=0)
        uuids = np.array(['%s'%uuid4() for _ in range(n)])
        bounds = np.ones(n) * .5
        example_coll = pickle.dumps((positions, uuids, bounds))  # FIXME putting pickles last can bollox the STOP
        #print('making example bam')
        example_bam = makeSimpleGeom(positions, np.random.rand(4)).__reduce__()[1][-1]  # the ONE way we can get this to work atm; GeomNode iirc; FIXME make sure -1 works every time
        #print('done making bam',example_bam)  # XXX if you want this use repr() ffs

        data_tuple = (example_bam, example_coll, b'this is a UI data I swear')

        #code for testing threading and sending stuff
        #cnt = 9999999
        #if request.request_type is 'prediction':
            #data_tuple = [make_bytes(cnt) for _ in range(2)] + [b'THIS IS THE FIRST ONE']
        #else:
            #data_tuple = [make_bytes(cnt) for _ in range(2)] + [b'THIS IS THE SECOND ONE']

        return data_tuple

    def make_predictions(self, request):
        #TODO this is actually VERY easy, because all we need to do is use
            #the list of connected UI elements that we SEND OUT ANYWAY and
            #just prospectively load those models/views
        request = FAKE_PREDICT
        yield request  # XXX NOTE: yielding the request itself causes a second copy to be sent

class requestCacheManager:
    """ we want to use a global cache so that we don't recompute the same request
        for multiple clients

        we *could* make this persistent if needs be
    """
    def __init__(self, cache_limit = 10000):
        self.cache_limit = cache_limit
        self.cache = {}
        self.cache_age = deque()  # this is a nasty hack, probably need a real tree here at some point
        self.passout = []  # HOW DO SERVER PROTOCOLS WORK!?

    def get_cache(self, request_hash):
        try:
            data_stream = self.cache[request_hash]
            self.cache_age.remove(request_hash)
            self.cache_age.append(request_hash)  # basically ranks cache by access frequency
            #print('server cache hit')
            return data_stream
        except KeyError:
            #print('server cache miss')
            return None

    def update_cache(self, request_hash, data_stream):  # TODO only call this if 
        #print('cache updated!')
        #print(request_hash)
        self.cache[request_hash] = data_stream
        self.cache_age.append(request_hash)
        while len(self.cache_age) > self.cache_limit:
            self.cache.pop(self.cache_age.popleft())
        #print('server cache updated with', request_hash, data_stream)

    def __repr__(self):
        return "\n".join([repr(rh) for rh in self.cache_age])

class tokenManager:  # TODO this thing could be its own protocol and run as a shared state server using lambda: instance
#FIXME this may be suceptible to race conditions on remove_token!
    """ shared state for tokens O_O (I cannot believe this works
        As long as these functions do what they say they do this
        could run on mars and no one would really care.
    """
    def __init__(self):
        self.tokenDict = defaultdict(set)
    def update_ip_token_pair(self, ip, token):
        self.tokenDict[ip].add(token)
        #print(self.tokenDict)
    def get_tokens_for_ip(self, ip):
        #print(self.tokenDict)
        return self.tokenDict[ip]
    def remove_token_for_ip(self, ip, token):
        self.tokenDict[ip].remove(token)
        #print(self.tokenDict)

class make_shutdown:
    def __init__(self, serverLoop, serverThread, serverCon, serverData, ppe):
        self.serverLoop = serverLoop
        self.serverThread = serverThread
        self.serverCon = serverCon
        self.serverData = serverData
        self.ppe = ppe

        self.done = False

    def __call_(self):
        repr(self)

    def __bool__(self):
        return self.done

    def __repr__(self):
        print('\nexiting...')
        self.serverLoop.call_soon_threadsafe(self.serverLoop.stop)
        self.serverThread.join()
        self.serverCon.close()
        self.serverData.close()
        self.serverLoop.close()
        self.ppe.shutdown(wait=True)
        self.done = True
        get_ipython().ask_exit()  # can only be called inside an interactive shell
        return 'Shutdown successful.'

        #return 'The server has already been shutdown!'

def main():
    from threading import Thread
    from protocols import connectionServerProtocol, dataServerProtocol
    from process_fixed import ProcessPoolExecutor_fixed as ProcessPoolExecutor
    serverLoop = get_event_loop()
    ppe = ProcessPoolExecutor()

    conContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None)
    dataContext = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)

    tm = tokenManager()  # keep the shared state out here! magic if this works

    conServ = connectionServerProtocol(tm)

    #shared state, in theory this stuff could become its own Protocol
    rcm = requestCacheManager(9999)
    respMaker = responseMaker
    # FIXME here we cannot remove references to these methods from instances
        # because they are defined at the class level and not passed in at
        # run time. We MAY be able to fix this by using a metaclass that
        # constructs these so that when a new protocol is started those methods
        # are passed in and thus can successfully be deleted from a class instance

    datServ = dataServerProtocol(serverLoop, respMaker, rcm, tm, ppe)

    coro_conServer = serverLoop.create_server(conServ, '127.0.0.1', CONNECTION_PORT, ssl=None)  # TODO ssl
    coro_dataServer = serverLoop.create_server(datServ, '127.0.0.1', DATA_PORT, ssl=None)  # TODO ssl and this can be another box
    serverCon = serverLoop.run_until_complete(coro_conServer)
    serverData = serverLoop.run_until_complete(coro_dataServer)

    serverThread = Thread(target=serverLoop.run_forever)
    serverThread.start()

    shutdown = make_shutdown(serverLoop, serverThread, serverCon, serverData, ppe)

    print('ready',end='')
    while True:
        embed(banner1='')
        if shutdown:
            break
        else:
            print("To exit please run shutdown",end='')


if __name__ == "__main__":
    main()
