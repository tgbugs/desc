import pickle
import zlib
import time
from collections import deque
#from multiprocessing import Pool, Manager
from multiprocessing import Pipe as mpp
#from multiprocessing import Queue as mpq
#from multiprocessing.queues import Empty
#from queue import Queue as tq
from threading import Lock
#from concurrent.futures import ProcessPoolExecutor

from IPython import embed

from direct.showbase.DirectObject import DirectObject
from panda3d.core import GeomNode, NodePath, PandaNode

from dataIO import treeMe
from request import FAKE_REQUEST, FAKE_PREDICT, RAND_REQUEST

#import sys  # we shouldnt need to call this here
#sys.modules['core'] = sys.modules['panda3d.core']

from prof import profile_me

#import rpdb2


class renderManager(DirectObject):
    """ a class to manage, bam, coll, and ui (and more?) incoming data
        all of those streams should be decompressed and reconstructed before
        showing up here so that there are just two or three nodes that can be
        attached to the scene graph if the call comes
        
        wait... why would we not just go ahead and construct this stuff in another
        process pool?? it shouldn't affect framerates if I'm thinking about this the
        right way... run_in_executor??? shouldnt there be a way to NOT use run_in_executor?
    """
    #RECV_LIMIT = 50  # tweak to keep recv/frame sane, 2 is ~30fps (computer pending)
    #BAM_ADD_LIMIT = 3  # TODO
    #COLL_ADD_LIMIT = 50  # in theory we could scale this based on load

    RECV_LIMIT = 99999  # tweak to keep recv/frame sane, 2 is ~30fps (computer pending)
    BAM_ADD_LIMIT = 99999  # TODO
    COLL_ADD_LIMIT = 99999  # in theory we could scale this based on load
    
    def __init__(self, event_loop = None, ppe = None):
        self.event_loop = event_loop
        self.ppe = ppe  # FIXME
        self.__inc_nodes__ = {}
        self.pipes = {}
        self.coll_add_queue = deque()
        self.bam_add_queue = deque()
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

        self.cache = {}
        #self.cache_age = deque()  # TODO implement this?

        self.accept('r', self.fake_request)
        self.accept('p', self.fake_predict)
        self.accept('n', self.rand_request)
        self.accept('c', self.embed)
        self.accept('k', self.print_cache)

    def print_cache(self):
        print([repr(k) for k in self.cache.keys()])

    def add_collision_task(self, task):
        bamEmpty = False
        try:
            for i in range(self.BAM_ADD_LIMIT):
                self.geomRoot.attachNewNode(self.bam_add_queue.popleft())
        except IndexError:
            bamEmpty = True

        try:
            for i in range(self.COLL_ADD_LIMIT):
                #self.add_queue.get_nowait().reparentTo(self.collRoot)
                self.coll_add_queue.popleft().reparentTo(self.collRoot)
        except IndexError:
            #print('l2 nodes added')
            if bamEmpty:
                taskMgr.remove('add_collision')
        finally:
            return task.cont

    def embed(self):
        embed()

    def set_send_request(self, send_request:'function *args = (request,)'):
        self.__send_request__ = send_request

    def submit_request(self, request):  # FIXME 
        """ this should only be called after failing a search for hidden nodes
            matching a request in the scene graph
        """
        request_hash = request.hash_
        try:
            #bam, coll, ui = self.cache[request_hash]
            self.render(*self.cache[request_hash])  # FIXME we need to test if this is already attached
            # FIXME we need to not attach the thing again...
            print('local cache hit')
        except KeyError:  # ValueError if a future is in there, maybe just use False?
            self.cache[request_hash] = False
            #self.cache[request_hash] = False
            self.__send_request__(request)
            print('local cache miss')
        except TypeError:  # TypeError will catch incorrect lenght on the input
            print('the request has been sent, if it is still wanted when it gets here we will render it')
            #self.cache[request_hash]
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

    #def make_nt_task(self, request_hash, bam, coll, ui, cache_ = False):
    def make_nt_task(self, request_hash, bam, coll, ui, render_ = False):
        """ given a node tuple return a task that will render/cache it when finished """
        if render_:
            if not bam.getNumParents():
                #self.geomRoot.attachNewNode(bam)  # FIXME this isn't quite right :/
                self.bam_add_queue.append(bam)
            else:
                print('already being rendered', bam)

        with self.pipeLock:
            #print('got pipelock')
            self.__inc_nodes__[request_hash] = []  # FIXME this could overwrite received nodes?
            self.pipes[request_hash] = coll, bam, ui, render_
            if not taskMgr.hasTaskNamed('coll_task'):
                taskMgr.add(self.coll_task,'coll_task') # %s'%request_hash)

        #send, recv = coll
        #q = coll

    #@profile_me
    def coll_task(self,task):
        with self.pipeLock:
            pops = []
            #recv_counter = 0
            #done = 0
            #print('iterating through requests')
            for request_hash, (recv, bam, ui, render_) in self.pipes.items():  # TODO there is a way to listen to multiple pipes iirc
                #if recv_counter >= self.RECV_LIMIT:
                    #break
                """
                try:
                    if recv.poll():  # can't use multiprocessing.connection.wait
                        node = recv.recv()
                        self.__inc_nodes__[request_hash].append(node)
                        if render_:
                            self.coll_add_queue.append(node)
                            if not taskMgr.hasTaskNamed('add_collision'):
                                taskMgr.add(self.add_collision_task,'add_collision')
                except EOFError:
                    print('got EOFError this pipe is done')
                    recv.close()
                    pops.append(request_hash)
                    nodes = self.__inc_nodes__.pop(request_hash)
                    self.cache[request_hash] = bam, nodes, ui
                except BaseException as e:
                    print('Coll task wat',e)

                """
                #try:
                if recv.poll():
                    nodes = recv.recv()
                    recv.close()
                    pops.append(request_hash)

                    #recv_counter += 1
                    #self.__inc_nodes__[request_hash].append(node)
                    if render_:  # render the l2 node!
                        self.coll_add_queue.extend(nodes)
                        if not taskMgr.hasTaskNamed('add_collision'):
                            taskMgr.add(self.add_collision_task,'add_collision')
                    self.cache[request_hash] = bam, nodes, ui
                #except EOFError:  # recv() raises this once the other end is closed
                    #pass
                    #done += 1
                    #recv.close()
                    #embed()
                    #print('processing done, closing the pipe')
                    #recv.close()
                    #pops.append(request_hash)
                    #nodes = self.__inc_nodes__.pop(request_hash)
                    #self.cache[request_hash] = bam, nodes, ui
                    #nodes = self.__inc_nodes__[request_hash]
                #"""

            for rh in pops:
                tup = self.pipes.pop(rh)
                print('popped',tup)
                print('pipes left',len(self.pipes))
            pops = []

            #print(done, len(self.pipes))
            #if done == len(self.pipes):
            if not self.pipes:
                print('we are done')
                taskMgr.remove('coll_task')
        return task.cont
                
    def set_nodes(self, request_hash, data_tuple):  # TODO is there any way to make sure we prioritize direct requests so they render fast?
        """ this is the callback used by the data protocol """
        #print('cache updated')
        #print('bam length', len(data_tuple[0]))
        #capture_datatuple(data_tuple)  # XXX for debugging selection
        #if request_hash in self.cache:  # FIXME what to do if we already have the data?! knowing that a prediction is in server cache doesn't tell us if we have sent it out already... # TODO cache inv

        try:
            if not self.cache[request_hash]:  # request expected
                #self.render(*self.cache[request_hash])
                #print(len(node_tuple))
                bam, coll, ui = node_tuple = self.make_nodes(request_hash, data_tuple)
                if hasattr(coll, '__iter__'):
                    self.bam_add_queue.append(bam)
                    self.coll_add_queue.extend(coll)
                    self.cache[request_hash] = bam, coll, ui
                    if not taskMgr.hasTaskNamed('add_collision'):
                        taskMgr.add(self.add_collision_task,'add_collision')
                else:
                    self.make_nt_task(request_hash, *node_tuple, render_=True)

        except KeyError:
            print("predicted data view cached")
            bam, coll, ui = node_tuple = self.make_nodes(request_hash, data_tuple)
            if hasattr(node_tuple[1], '__iter__'):
                self.cache[request_hash] = bam, coll, ui
            else:
                self.make_nt_task(request_hash, *node_tuple)
            #self.cache[request_hash] = node_tuple

    def render(self, bam, coll, ui):  # XXX almost deprecated
        if not bam.getNumParents():
            #self.bam_add_queue.append(bam)  # MMMM baby can you feel the overhead?
            #if not taskMgr.hasTaskNamed('coll_task'):
                #taskMgr.add(self.coll_task,'coll_task') # %s'%request_hash)
            self.geomRoot.attachNewNode(bam)  # FIXME this isn't quite right :/
        else:
            print('already being rendered', bam)

        [n.reparentTo(self.collRoot) for n in coll]


        #bam.reparentTo(self.geomRoot)
        #self.collRoot.attachNewNode(coll)
        #[c.reparentTo(self.collRoot) for c in coll.getChildren()]  # FIXME too slow!
        #self.uiRoot.attachNewNode(ui)
        #print(self.uiRoot.getChildren())  # utf-8 errors

    def make_nodes(self, request_hash, data_tuple):
        """ fire and forget """
        bam = self.makeBam(data_tuple[0])  #needs to return a node
        bam.setName(repr(request_hash))
        coll_tup = pickle.loads(data_tuple[1]) #positions uuids geomCollides
        #from panda3d.core import GeomVertexReader
        #data = GeomVertexReader(bam.getGeom(0).getVertexData(), 'vertex')
        #while not data.isAtEnd():
            #print(data.getData3f(),end='    ')
            #pass
        #print(coll_tup)
        coll = self.makeColl(request_hash, coll_tup)  #needs to return a node
        ui = self.makeUI(coll_tup[:2])  #needs to return a node (or something)
        node_tuple = (bam, coll, ui)  # FIXME we may want to have geom and collision on the same parent?
        #[n.setName(repr(request_hash)) for n in node_tuple]  # FIXME use eval to get the bytes back out yes I know this is not technically injective
        #[print(n) for n in node_tuple]
        return node_tuple

    def makeBam(self, bam_data):
        """ this is for Geoms or GeomNodes """
        node = GeomNode('')  # use attach new node...
        out = node.decodeFromBamStream(bam_data)  # apparently the thing I'm encoding is a node for test purposes... may need something
        #node.addGeom(out)
        return out

    #@profile_me
    def makeColl(self, request_hash, coll_tup):
        node = NodePath(PandaNode(''))  # use reparent to? XXX yes because of caching you tard
        pos, uuid, geom = coll_tup
        #return treeMe(node, pos, uuid, geom, None, None, None, request_hash)
        recv, send = mpp(False)
        #try:
        #rpdb2.setbreak()
        future = self.event_loop.run_in_executor(self.ppe, treeMe, node, pos, uuid, geom, None, None, None, request_hash, send)
        #embed()
        print('yes we are running stuff')
        return recv
        #except RuntimeError:
            #return None  # happens at shutdown


        #nodes = treeMe(node, *coll_tup)
        #for n in nodes:
            #n.reparentTo(node)
        #print('coll node successfully made')

    def makeUI(self, ui):  # FIXME this works inconsistently with other stuff
        """ we may not need this if we stick all the UI data in geom or coll nodes? """
        # yeah, because the 'properties' the we select on will be set based on which node
            # is selected
        node = PandaNode('')  # use reparent to?
        return node

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

    def __send_request__(self, request):
        raise NotImplementedError('NEVER CALL THIS DIRECTLY. If you didnt, is'
                                  ' your dataProtocol up?')

def capture_datatuple(data_tuple):
    with open('edge_case_data_tuple.pickle','wb') as f:
        pickle.dump(data_tuple, f)


