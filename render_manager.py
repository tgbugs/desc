import pickle
import zlib
import time
import asyncio
from collections import defaultdict, deque
#from multiprocessing import Pool, Manager
from multiprocessing import Pipe as mpp
#from multiprocessing import Queue as mpq
#from multiprocessing.queues import Empty
#from queue import Queue as tq
from threading import Lock
#from concurrent.futures import ProcessPoolExecutor

from ipython import embed

from direct.showbase.DirectObject import DirectObject
from panda3d.core import GeomNode, NodePath, PandaNode

from dataIO import treeMe
from request import FAKE_REQUEST, FAKE_PREDICT, RAND_REQUEST
from protocols import collPipeProtocol


#import sys  # we shouldnt need to call this here
#sys.modules['core'] = sys.modules['panda3d.core']

from prof import profile_me

#import rpdb2


class renderManager(DirectObject):
    """ a class to manage, geom, coll, and ui (and more?) incoming data
        all of those streams should be decompressed and reconstructed before
        showing up here so that there are just two or three nodes that can be
        attached to the scene graph if the call comes
        
        wait... why would we not just go ahead and construct this stuff in another
        process pool?? it shouldn't affect framerates if I'm thinking about this the
        right way... run_in_executor??? shouldnt there be a way to NOT use run_in_executor?
    """

    limit = False
    if limit:
        RECV_LIMIT = 50  # tweak to keep recv/frame sane, 2 is ~30fps (computer pending)
        BAM_ADD_LIMIT = 5  # TODO
        COLL_ADD_LIMIT = 50  # in theory we could scale this based on load
    else:
        RECV_LIMIT = 99999
        BAM_ADD_LIMIT = 99999
        COLL_ADD_LIMIT = 99999
    
    def __init__(self, event_loop = None, ppe = None):
        self.event_loop = event_loop
        self.ppe = ppe
        self.cache = {}
        #self.cache_age = deque()  # TODO implement this?
        self.__inc_nodes__ = defaultdict(list)
        self.pipes = {}
        self.coll_add_queue = deque()
        self.geom_add_queue = deque()
        self.pipeLock = Lock()

        geomRoot = render.find('geomRoot')
        if not geomRoot:
            geomRoot = render.attachNewNode('geomRoot')

        collideRoot = render.find('collideRoot')
        if not collideRoot:
            collideRoot = render.attachNewNode('collideRoot')

        uiRoot = render.find('uiRoot')
        if not uiRoot:
            uiRoot = render.attachNewNode('uiRoot')

        self.geomRoot = geomRoot
        self.collRoot = collideRoot
        self.uiRoot = uiRoot

        self.cpp = collPipeProtocol(self.cache, self.geom_add_queue, self.coll_add_queue, self.collRoot)

        self.accept('r', self.fake_request)
        self.accept('p', self.fake_predict)
        self.accept('n', self.rand_request)
        self.accept('c', self.embed)
        self.accept('k', self.print_cache)


        # TODO replace this with asyncio queue?
        taskMgr.add(self.add_collision_task,'add_collision')

    def set_send_request(self, send_request:'function *args = (request,)'):
        self.__send_request__ = send_request

    def submit_request(self, request):  # FIXME 
        """ this should only be called after failing a search for hidden nodes
            matching a request in the scene graph
        """
        request_hash = request.hash_
        try:
            self.render(*self.cache[request_hash])
            print('local cache hit')
        except KeyError:  # ValueError if a future is in there, maybe just use False?
            self.cache[request_hash] = False
            self.__send_request__(request)
            print('local cache miss')
        except TypeError:  # TypeError will catch incorrect lenght on the input
            print('the request has been sent, if it is still wanted when it gets here we will render it')
            # FIXME really we should only render the last thing... so yes we do need a
                # bit more advanced system so we only render the last requested thing (could change)
                # TODO this means that each UI element / collisionSolid needs to send a "not active" signal
                # when a request is no longer wanted

    def unrender(self, request_hash):  # FIXME what do we need this fellow sending? ie: how generate requests from UI
        # FIXME this needs to be "unrender" and we can work from there, no canceling, because we pretend like it completed
        try:
            self.cache.pop(request_hash)
        except KeyError:
            pass

        # use an rx reactive extensions construction with a temporal list or whatever?
        #try:
            #self.cache.pop(request_hash)  # so may problems with ordering and state O_O
            # TODO it is not this simple, there needs to be a temoral list and if the 'current' state includes a cancel render request...
                # argh this is a mess so think about, need better abstraction
                # no, this is easy, the render request shall be considered to have been _completed_
                # when it is submitted, even if it hasnt, so all we need to do is use a future to
                # synchronize execution? ... or does that... wait...
        #except KeyError:
            #pass

    def render(self, geom, coll, ui):
        if not geom.getNumParents():
            self.geomRoot.attachNewNode(geom)
        else:
            print('already being rendered', geom)

        # FIXME this will just reparent all the l2 nodes if already attached
        [n.reparentTo(self.collRoot) for n in coll]

    def set_nodes(self, request_hash, data_tuple):  # TODO is there any way to make sure we prioritize direct requests so they render fast?
        """ this is the callback used by the data protocol """
        #if request_hash in self.cache:  # FIXME what to do if we already have
        #the data?! knowing that a prediction is in server cache doesn't tell
        #us if we have sent it out already... # TODO cache inv
        try:
            if not self.cache[request_hash]:  # request expected
                geom, coll, ui = self.make_nodes(request_hash, data_tuple)
                if hasattr(coll, 'recv'):  # not running in ppe
                    todo = self.event_loop.connect_read_pipe(lambda: self.cpp(request_hash, geom, ui, render_=True), coll)
                    asyncio.Task(todo, loop=self.event_loop)
                    #self.make_nt_task(request_hash, geom, coll, ui, render_=True)
                else:
                    self.geom_add_queue.append(geom)
                    self.coll_add_queue.append(coll)
                    self.cache[request_hash] = geom, coll, ui
                    # TODO new async task goes here
                    if not taskMgr.hasTaskNamed('add_collision'):
                        taskMgr.add(self.add_collision_task,'add_collision')

        except KeyError:
            print("predicted data view cached")
            geom, coll, ui = node_tuple = self.make_nodes(request_hash, data_tuple)
            if hasattr(node_tuple[1], 'recv'):  # not running in ppe
                todo = self.event_loop.connect_read_pipe(lambda: self.cpp(request_hash, geom, ui), coll)
                asyncio.Task(todo, loop=self.event_loop)
                #self.make_nt_task(request_hash, *node_tuple)
            else:
                self.cache[request_hash] = node_tuple

    # tasks
    def make_nt_task(self, request_hash, geom, coll, ui, render_ = False):
        """ given a node tuple return a task that will render/cache it when finished """
        if render_:
            if not geom.getNumParents():
                self.geom_add_queue.append(geom)
            else:
                print('already being rendered', geom)

        with self.pipeLock:
            self.pipes[request_hash] = coll, geom, ui, render_
            if not taskMgr.hasTaskNamed('coll_task'):
                taskMgr.add(self.coll_task,'coll_task')


    def coll_task(self,task):
        with self.pipeLock:
            pops = []
            recv_counter = 0
            for request_hash, (recv, geom, ui, render_) in self.pipes.items():  # TODO there is a way to listen to multiple pipes iirc
                if recv_counter >= self.RECV_LIMIT:
                    break
                elif recv.poll():
                    try:
                        node = recv.recv()
                        self.__inc_nodes__[request_hash].append(node)
                        recv_counter += 1
                        if render_:  # render the l2 node!
                            self.coll_add_queue.append(node)
                            if not taskMgr.hasTaskNamed('add_collision'):
                                taskMgr.add(self.add_collision_task,'add_collision')
                    except EOFError:  #all nodes in
                        pops.append(request_hash)
                        nodes = self.__inc_nodes__.pop(request_hash)
                        self.cache[request_hash] = geom, nodes, ui

            for rh in pops:
                tup = self.pipes.pop(rh)
                print('popped',tup)
                print('pipes left',len(self.pipes))

            if not self.pipes:
                print('we are done')
                taskMgr.remove('coll_task')
        return task.cont
                
    def add_collision_task(self, task):
        geomEmpty = False
        try:
            for i in range(self.BAM_ADD_LIMIT):
                self.geomRoot.attachNewNode(self.geom_add_queue.popleft())
        except IndexError:
            geomEmpty = True

        try:
            for i in range(self.COLL_ADD_LIMIT):
                #print(len(self.coll_add_queue))
                self.coll_add_queue.popleft().reparentTo(self.collRoot)
                #print('coll added!')
        except IndexError:
            #if geomEmpty:
                #taskMgr.remove('add_collision')
            pass
        finally:
            return task.cont

    # make nodes (or spawn processes that make nodes)
    def make_nodes(self, request_hash, data_tuple):
        """ fire and forget """
        geom = self.makeGeom(data_tuple[0])  #needs to return a node
        geom.setName(repr(request_hash))
        coll_tup = pickle.loads(data_tuple[1]) #positions uuids geomCollides
        coll = self.makeColl(request_hash, coll_tup)  #returns a list or a recv pipe
        ui = self.makeUI(coll_tup[:2])  #needs to return a node (or something)
        return geom, coll, ui

    def makeGeom(self, geom_data):
        """ this is for Geoms or GeomNodes """
        node = GeomNode('')  # use attach new node...
        out = node.decodeFromBamStream(geom_data)
        return out

    def makeColl(self, request_hash, coll_tup):
        #node = NodePath(CollisionNode(''))  # use reparent to? XXX yes because of caching you tard
        pos, uuid, geom = coll_tup
        if self.ppe is False:
            return treeMe(None, pos, uuid, geom, None, None, None, request_hash)
        recv, send = mpp(False)
        try:
            future = self.event_loop.run_in_executor(self.ppe, treeMe, None, pos, uuid, geom, None, None, None, request_hash, send)
            return recv
        except RuntimeError:
            return None  # happens at shutdown

    def makeUI(self, ui):  # FIXME this works inconsistently with other stuff
        """ we may not need this if we stick all the UI data in geom or coll nodes? """

    # key callbacks
    def fake_request(self):
        r = FAKE_REQUEST
        self.submit_request(r)

    def fake_predict(self):
        r = FAKE_PREDICT
        self.submit_request(r)

    def rand_request(self):
        for _ in range(10):
            r = RAND_REQUEST()
            self.submit_request(r)

    def embed(self):
        embed()

    def print_cache(self):
        print([repr(k) for k in self.cache.keys()])

    def __send_request__(self, request):
        raise NotImplementedError('NEVER CALL THIS DIRECTLY. If you didnt, is'
                                  ' your dataProtocol up?')

def capture_datatuple(data_tuple):
    with open('edge_case_data_tuple.pickle','wb') as f:
        pickle.dump(data_tuple, f)


