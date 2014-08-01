from direct.showbase.DirectObject import DirectObject
from panda3d.core import GeomNode, NodePath, PandaNode

class renderManager(DirectObject):
    """ a class to manage, bam, coll, and ui (and more?) incoming data
        all of those streams should be decompressed and reconstructed before
        showing up here so that there are just two or three nodes that can be
        attached to the scene graph if the call comes
        
        wait... why would we not just go ahead and construct this stuff in another
        process pool?? it shouldn't affect framerates if I'm thinking about this the
        right way... run_in_executor??? shouldnt there be a way to NOT use run_in_executor?
    """
    
    def __init__(self):
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
        self.cache_age = deque()

        self.checkLock = Lock()  # TODO see if we need this

        self.accept('r',self.fake_request)
        self.accept('p',self.fake_predict)
        self.accept('n',self.rand_request)

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

    def set_nodes(self, request_hash, data_tuple):  # TODO is there any way to make sure we prioritize direct requests so they render fast?
        """ this is the callback used by the data protocol """
        #print('cache updated')
        #print('bam length', len(data_tuple[0]))
        #capture_datatuple(data_tuple)  # XXX for debugging selection
        try:
            #if request_hash in self.cache:  # FIXME what to do if we already have the data?! knowing that a prediction is in server cache doesn't tell us if we have sent it out already... # TODO cache inv
            if not self.cache[request_hash]:
                #self.render(*self.cache[request_hash])
                #print(len(node_tuple))
                node_tuple = self.make_nodes(request_hash, data_tuple)
                self.cache[request_hash] = node_tuple
                self.render(*node_tuple)
        except KeyError:
            print("predicted data view cached")
            node_tuple = self.make_nodes(request_hash, data_tuple)
            self.cache[request_hash] = node_tuple

    def render(self, bam, coll, ui):
        if not bam.getNumParents():
            self.geomRoot.attachNewNode(bam)  # FIXME this isn't quite right :/
        else:
            print('already being rendered', bam)
        #bam.reparentTo(self.geomRoot)
        #self.collRoot.attachNewNode(coll)
        [c.reparentTo(self.collRoot) for c in coll.getChildren()]  # FIXME too slow!
        #self.uiRoot.attachNewNode(ui)
        #print(self.uiRoot.getChildren())  # utf-8 errors

    def make_nodes(self, request_hash, data_tuple):
        """ fire and forget """
        bam = self.makeBam(data_tuple[0])  #needs to return a node
        coll_tup = pickle.loads(data_tuple[1]) #positions uuids geomCollides
        from panda3d.core import GeomVertexReader
        data = GeomVertexReader(bam.getGeom(0).getVertexData(), 'vertex')
        #while not data.isAtEnd():
            #print(data.getData3f(),end='    ')
            #pass
        #print(coll_tup)
        coll = self.makeColl(coll_tup)  #needs to return a node
        ui = self.makeUI(coll_tup[:2])  #needs to return a node (or something)
        node_tuple = (bam, coll, ui)  # FIXME we may want to have geom and collision on the same parent?
        [n.setName(repr(request_hash)) for n in node_tuple]  # FIXME use eval to get the bytes back out yes I know this is not technically injective
        #[print(n) for n in node_tuple]
        return node_tuple

    def makeBam(self, bam_data):
        """ this is for Geoms or GeomNodes """
        node = GeomNode('')  # use attach new node...
        out = node.decodeFromBamStream(bam_data)  # apparently the thing I'm encoding is a node for test purposes... may need something
        #node.addGeom(out)
        return out

    def makeColl(self, coll_tup):
        node = NodePath(PandaNode(''))  # use reparent to? XXX yes because of caching you tard
        # FIXME treeMe is SUPER slow... :/
        treeMe(node, *coll_tup)  # positions, uuids, geomCollide (should be the radius of the bounding volume)
        print('coll node successfully made')
        return node

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
        for _ in range(2):
            r = RAND_REQUEST()
            self.submit_request(r)

    def __send_request__(self, request):
        raise NotImplementedError('NEVER CALL THIS DIRECTLY. If you didnt, is'
                                  ' your dataProtocol up?')

def capture_datatuple(data_tuple):
    with open('edge_case_data_tuple.pickle','wb') as f:
        pickle.dump(data_tuple, f)


