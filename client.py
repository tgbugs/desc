#!/usr/bin/env python3.4

import asyncio
import random
import pickle
#import zlib
import ssl
import os
from collections import deque
from time import sleep
from threading import Lock

from IPython import embed
from numpy.random import rand

from panda3d.core import GeomNode, CollisionNode, NodePath, PandaNode

from defaults import CONNECTION_PORT, DATA_PORT
from request import Request, DataByteStream
from dataIO import treeMe


# XXX NOTE TODO: There are "DistributedObjects" that exist in panda3d that we might be able to use instead of this???
    #that would vastly simplify life...? ehhhhh


def become_future(function):
    """ Decorator function to make a normal function run in a future """
    @asyncio.coroutine
    def wrapped(*args, **kwargs):
        future = asyncio.Future()
        yield future
        future.set_result(function(*args, **kwargs))
    return wrapped

@asyncio.coroutine
def run_future(function, *args, **kwargs):
    """ Run a function in a future """
    future = asyncio.Future()
    yield future
    future.set_result(function(*args,**kwargs))


@asyncio.coroutine
def run_panda():
    """ make panda work with the event loop? I'm expecting bugs here... """
    future = asyncio.Future()
    yield future
    run()
    future.set_result(True)

def dumps(object):
    """ Special dumps that adds a double stop to make deserializing easier """
    return pickle.dumps(object)+b'.'

def run_for_time(loop,time):
    """ use this to view responses inside embed """
    loop.run_until_complete(asyncio.sleep(time))

class newConnectionProtocol(asyncio.Protocol):  # this could just be made into a token getter...
    """ this is going to be done with fixed byte sizes known small headers """
    def __new__(cls, *args, **kwargs:'for create_connection'):
        """ evil and unpythonic, this no longer behaves like a class """
        cls.event_loop = asyncio.get_event_loop()  # FIXME make this work even if running? we probably only need to call this the first time we make a new class, it will persist thereafter
        future = asyncio.Future()
        instance = super().__new__(cls)
        instance.future_token = future
        coro = cls.event_loop.create_connection(lambda: instance, *args, **kwargs)
        return coro, future

    def connection_made(self, transport):
        self.transport = transport
        self.transport.write(b'I promis I real client, plz dataz')
        #send public key (ie the account we are looking for) #their password should unlock a local key which 

    def data_received(self, data):
        token_data = b''
        token_start = data.find(DataByteStream.OP_TOKEN)  # FIXME sadly we'll probably need to deal with splits again
        #print('token?',data)
        if token_start != -1:
            #token_start += DataByteStream.LEN_OPCODE
            print('__',self,'token_start',token_start,'__')
            token_data = data[token_start:token_start+DataByteStream.LEN_OPCODE+DataByteStream.LEN_TOKEN]
        if token_data:
            self.future_token.set_result(token_data)
            self.transport.write_eof()

    def connection_lost(self, exc):
        if exc is None:
            print("New connection transport closed.")

    @asyncio.coroutine
    def get_data_token(self):
        yield from self.future_token
        #try: yield from self.future_token
        #except asyncio.futures.InvalidStateError as e:
            #print(e)
            #print('ssuming that this is because the future is already finished')

class dataProtocol(asyncio.Protocol):  # in theory there will only be 1 of these per interpreter... so could init ourselves with the token
    def __new__(cls, token):
        instance = super().__new__(cls)
        instance.token = token
        return lambda: instance  # this is vile, but it works

    def connection_made(self, transport):
        transport.write(b'hello there')
        transport.write(self.token)
        self.transport = transport
        self.render_set_send_request(self.send_request)
        self.__block__ = b''
        self.__block_size__ = None
        self.__block_tuple__ = None

    def data_received(self, data):
        """ receive bam files that come back on request
            we can tag them with a request id if needs be
            this way we can also just start sending bam files
            as soon as the connection has been created if they
            arent cached
        """
        self.__block__ += data
        #print(id(self),'block length',len(self.__block__))
        if not self.__block_size__:
            if DataByteStream.OP_DATA not in self.__block__:
                self.__block__ = b''
                return None
            else:
                self.__block_size__, self.__block_tuple__ = DataByteStream.decodeResponseHeader(self.__block__)

        if len(self.__block__) >= self.__block_size__:
            #print('total size expecte', self.__block_size__)
            #print('post split block',self.__block__[self.__block_size__:])
            #embed()
            output = DataByteStream.decodeResponseStream(self.__block__[:self.__block_size__], *self.__block_tuple__)
            print('yes we are trying to render stuff')
            self.event_loop.run_in_executor( None, lambda: self.set_nodes(*output) )
            self.__block__ = self.__block__[self.__block_size__:]
            self.__block_size__ = None
            self.__block_tuple__ = None
            self.data_received(b'')  # lots of little messages will bollox this


    def __data_received(self, data): #works with the split version (ie fails)
        self.__block__ += data
        split = self.__block__.split(DataByteStream.STOP)
        if len(split) is 1:  # no stops
            if DataByteStream.OP_DATA not in self.__block__:  # no ops
                self.__block__ = b''
        else:
            self.__block__ = split.pop()
            response_generator = DataByteStream.decodeResponseStreams(split)
            self.process_responses(response_generator)
    
    def _data_received(self, data):  # XXX deprecated
        print("received data length ",len(data))  # this *should* just be bam files coming back, no ids? or id header?
        response_start = data.find(DataByteStream.OP_BAM)  # TODO modify this so that it can detect any of the types
        if response_start != -1:
            response_start += DataByteStream.LEN_OPCODE
            hash_start = response_start + DataByteStream.LEN_CACHE
            bam_start = hash_start + DataByteStream.LEN_MD5_HASH
            bam_stop = bam_start + data[bam_start:].find(DataByteStream.STOP)  # FIXME make sure the bam byte stream doesnt have this in there...
        cache = int(data[response_start:response_start + DataByteStream.LEN_CACHE])
        request_hash = data[hash_start:hash_start + DataByteStream.LEN_MD5_HASH]
        bam_data = data[bam_start:bam_stop]  # FIXME this may REALLY need to be albe to split across data_received calls...
        #print('')
        #print('bam_data',bam_data)

        # TODO if the request hash is not in cache.keys() stick it in there and don't render it
        if cache:  # FIXME this needs to be controlled locally based soley on request hash NOT cache bit
            # TODO this is second field in header
            self.update_cache(request_hash, bam_data)  # TODO: the mapping between requests and the data in the database needs to be injective
        #else:  # this data was generated in response to a request
            #self.render_bam(request_hash, zlib.decompress(bam_data))


            # hrmmmm how do we get this data out!?
            # its a precache... and the server is the
            # one that is going to be doing predictions
            # about what to load... this should not be
            # synchronous synchrnomus requests should exist
            # but mostly it hsould just be "here, get me this when you can"
    
    def connection_lost(self, exc):  # somehow this never triggers...
        if exc is None:
            print('Data connection closed')
            self.event_loop.close()  # FIXME we use this for now, but tis dangerous
            # FIXME why does literally terminiating the server cause this to survive?
        else:
            print('connection lost')
            #probably we want to try to renegotiate a new connection
            #but that could get really nast if we have a partition and
            #we try to reconnect repeatedly
            #asyncio.get_event_loop().close()  # FIXME probs don't need this

    def send_request(self, request):
        """ this is called BY renderManager.get_cache !!!!"""
        out = dumps(request)
        self.transport.write(out)

        # TODO add that hash to a 'waiting' list and then cross it off when we are done
            # could use that to quantify performance
            # XXX need this to prevent sending duplicate requests

    @asyncio.coroutine
    def _send_request(self, request, future):  # see if we need this / relates to how we deal with data_received
        self.future_data = {}    
        # maybe we don't need this? because we don't really care when it comes back?
        # and we don't need to block for it? maybe in some cases it *could* be useful
        # the way it is implemented at the moment with the dict is a bit of a problem
        # if we want to use this we should either tag requests with their counter OR
        # if there is no counter then we 
        # XXX NOTE for now, future returns do not match requests
        # in fact we may need to figure out what to do with data that is preloaded by the server w/o client happyness
        # basically act like an http and SEND early and often

        rh = hash(request)
        self.future_data[rh] = future
        # TODO XXX hashing requests will be SUPER important for caching, but how to determine the request
        self.check_cache(rh)
        self.transport.write(dumps(request))
        yield from future

    def process_responses(self, response_generator):  # TODO this should be implemented in a subclass specific to panda, same w/ the server
        for request_hash, data_tuple in response_generator:
            print('yes we are trying to render stuff')
            self.event_loop.run_in_executor( None, lambda: self.set_nodes(request_hash, data_tuple) )
            # XXX FIXME panda *should* be ok with this, hopefully this gets around the gil or we have problems

    def set_nodes(self, request_hash, data_tuple):
        raise NotImplementedError('patch this function with the shared stated version in bamCacheManager')

    def render_set_send_request(self, send_request:'function'):
        raise NotImplementedError('patch this function with the shared stated version in bamCacheManager')


class bamCacheManager:
    """ shared state bam cache """
    def __init__(self,rootNode):
        self.cache = {}
        # XXX FIXME a better way to do this is to use make it a future aware cache and just put a future at the index
            # until the result arrives
            # this way we can just maintain a list of all future stuff and add 'unexpected' data too
            # the one question is what to do about gzing stuff... maybe use other cycles to go ahead and prep the nodes?
            # in which case we degz and convert to a node asap and stick the node in the cache?
            # that seems like a better idea...
        self.rootNode = rootNode

        self.reqLock = Lock()  # this works, the issue is that I havent written the deserializer for the client yet!
        self.__future_hashes__ = set()  # the set of all future (or current) hashes should be similar to cache_age

    def add_out_request(self, request_hash):
        with self.reqLock:
            if request_hash in self.__future_hashes__:
                print('the request is already outstanding')
                return False
            else:
                self.__future_hashes__.add(request_hash)
                return True

    def del_out_request(self, request_hash):
        """ This method should be called when the data for a hash has
            a) been removed from the render tree
            b) has passed out of the cache_age queue
        """
        with self.reqLock:
            print('')
            print(self.__future_hashes__)
            print(request_hash)
            try:
                self.__future_hashes__.remove(request_hash)
            except KeyError as e:
                pass
                #print('somehow we received a hash for a request response that we did not request')
                #print('error was ',e)
                # FIXME actually we definitely want to receive all of these requests

    def check_cache(self, request_hash):
        try:
            #bam = zlib.decompress(self.cache[request_hash])  # FIXME is there some way to make the gzing more transparent?
            bam = None
            self.render_bam(bam)
            print('local cache hit')
            return True
        except KeyError:
            print('local cache miss')
            return False

    def update_cache(self, request_hash, bam_data):
        print('cache updated')
        self.cache[request_hash] = bam_data

    def render_bam(self, render_hash, bam):
        """ render the GEOM only, will hang with nasty error if fed a collision node """
        newNode = GeomNode(render_hash)
        geomNode = newNode.decodeFromBamStream(bam)  # apparently the thing I'm encoding is a node for test purposes... may need something
        #newNode.addGeom(geom)
        self.rootNode.attachNewNode(newNode)


class renderManager:
    """ a class to manage, bam, coll, and ui (and more?) incoming data
        all of those streams should be decompressed and reconstructed before
        showing up here so that there are just two or three nodes that can be
        attached to the scene graph if the call comes
        
        wait... why would we not just go ahead and construct this stuff in another
        process pool?? it shouldn't affect framerates if I'm thinking about this the
        right way... run_in_executor??? shouldnt there be a way to NOT use run_in_executor?
    """
    
    def __init__(self, bamNode, collNode, uiNode):
        self.bamNode = bamNode
        self.collNode = collNode
        self.uiNode = uiNode

        self.cache = {}
        self.cache_age = deque()

        self.checkLock = Lock()  # TODO see if we need this

    def set_send_request(self, send_request:'function *args = (request,)'):
        self.send_request = send_request

    def submit_request(self, request):  # FIXME 
        """ this should only be called after failing a search for hidden nodes
            matching a request in the scene graph
        """
        request_hash = request.hash_
        try:
            #bam, coll, ui = self.cache[request_hash]
            self.render(*self.cache[request_hash])
            # FIXME we need to not attach the thing again...
            print('local cache hit')
        except KeyError:  # ValueError if a future is in there, maybe just use False?
            self.cache[request_hash] = False
            #self.cache[request_hash] = False
            self.send_request(request)
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
        print('cache updated')
        node_tuple = self.make_nodes(request_hash, data_tuple)
        try:
            #if request_hash in self.cache:  # FIXME what to do if we already have the data?! knowing that a prediction is in server cache doesn't tell us if we have sent it out already... # TODO cache inv
            if not self.cache[request_hash]:
                #self.render(*self.cache[request_hash])
                print(len(node_tuple))
                self.render(*node_tuple)
        except KeyError:
            print("predicted data view cached")
            self.cache[request_hash] = node_tuple

    def render(self, bam, coll, ui):
        self.bamNode.attachNewNode(bam)
        #self.collNode.attachNewNode(coll)
        coll.reparentTo(self.collNode)
        self.uiNode.attachNewNode(ui)
        print(self.uiNode.getChildren())

    def make_nodes(self, request_hash, data_tuple):
        """ fire and forget """
        bam = self.makeBam(data_tuple[0])  #needs to return a node
        coll = self.makeColl(data_tuple[1])  #needs to return a node
        ui = self.makeUI(data_tuple[2])  #needs to return a node (or something)
        node_tuple = (bam, coll, ui)  # FIXME we may want to have geom and collision on the same parent?
        [n.setName(request_hash) for n in node_tuple]  # FIXME python3 unicde and bytes >_< GARARARARAR
        embed()
        return node_tuple

    def makeBam(self, bam_data):
        """ this is for Geoms or GeomNodes """
        node = GeomNode('')  # use attach new node...
        node.decodeFromBamStream(bam_data)  # apparently the thing I'm encoding is a node for test purposes... may need something
        return node

    def makeColl(self, coll_data):
        node = NodePath(PandaNode(''))  # use reparent to?
        coll = pickle.loads(coll_data)
        # FIXME treeMe is SUPER slow... :/
        treeMe(node, *coll)  # positions, uuids, geomCollide (should be the radius of the bounding volume)
        print('coll node successfully made')
        return node

    def makeUI(self, ui_data):
        """ we may not need this if we stick all the UI data in geom or coll nodes? """
        # yeah, because the 'properties' the we select on will be set based on which node
            # is selected
        node = PandaNode('')  # use reparent to?
        return node

def main():
    conContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cadata=None)  # TODO cadata should allow ONLY our self signed, severly annoying to develop...
    dataContext = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)

    #embed()
    #transport, protocol = yield from clientLoop.create_connection(newConnectionProtocol, '127.0.0.1', 55555, ssl=None)  # TODO ssl
    #reader, writer = yield from asyncio.open_connection('127.0.0.1', 55555, loop=clientLoop, ssl=None)

    #transport, protocol = clientLoop.run_until_complete(coro_conClient)

    #TODO ONE way to make this synchronous so to add a coroutine that only completes when it gets a response
        #and then call run_until_complete on it :)
    #test = []
    #def myfunc(data):
        #test.append(data)


    clientLoop = asyncio.get_event_loop()
    #tokenFuture = asyncio.Future()  # we have to pass the future in before init since the token is sent immediately, we might not even have to call run_until_complete??
    #coro_conClient = clientLoop.create_connection(newConnectionProtocol(tokenFuture), '127.0.0.1', CONNECTION_PORT, ssl=None)  # TODO ssl

    coro_conClient, tokenFuture = newConnectionProtocol('127.0.0.1', CONNECTION_PORT, ssl=None)

    conTransport, conProtocol = clientLoop.run_until_complete(coro_conClient)
    clientLoop.run_until_complete(conProtocol.get_data_token())
    print('got token',tokenFuture.result())

        
    #here we demonstrate how to get a buttload of tokens >_<
    #cf = [newConnectionProtocol('127.0.0.1', CONNECTION_PORT) for _ in range(10)]
    #prots = [clientLoop.run_until_complete(c)[1] for c, _ in cf]
    #coros_ = [clientLoop.run_until_complete(p.get_data_token()) for p in prots]  # this works too
    #coros_ = [p.get_data_token() for p in prots]
    #[clientLoop.run_until_complete(f) for f in coros_]
    #tokens = [f.result() for _, f in cf]
    #print('LOOK AT THEM WE\'RE RICH!',tokens)

    class FakeNode:
        def attachNewNode(self, node):
            print('pretend like this print statement actually causes things to render',node)

    #rootNode = FakeNode()
    rootNode = NodePath(PandaNode('testRoot'))

    rendMan = renderManager(*[rootNode]*3)  # in theory we can have multiple connections for a single render manager if we have disconnects
    # if fact renderMan might even spin up its own connections! so render before connection is correct

    datCli_base = type('dataProtocol',(dataProtocol,),
                  {'set_nodes':rendMan.set_nodes,  # FIXME this needs to go through make_nodes
                   'render_set_send_request':rendMan.set_send_request,
                   'event_loop':clientLoop })  # FIXME we could move event_loop to __new__? 

    datCli = datCli_base(tokenFuture.result())  # __new__ magic, we don't use type() since tokens arent shared
    coro_dataClient = clientLoop.create_connection(datCli, '127.0.0.1', DATA_PORT, ssl=None)  # TODO ssl
    transport, protocol = clientLoop.run_until_complete(coro_dataClient)

    #the 3 lines that follow completely break everything... why? don't know!
    #datCli2 = datCli_base(tokens[3])  # __new__ magic, we don't use type() since tokens arent shared
    #coro_dataClient2 = clientLoop.create_connection(datCli, '127.0.0.1', DATA_PORT, ssl=None)  # TODO ssl
    #transport2, protocol2 = clientLoop.run_until_complete(coro_dataClient2)

    transport.write(b'testing?')
    transport.write(b'testing?')
    transport.write(b'testing?')

    #protocol2.send_token_data(tokenFuture.result())  # testing race condition, bet is both can get it
    #protocol.send_token_data(tokenFuture.result())


    #writer.write('does this work?')
    for i in range(10):
        sleep(1E-4)  # FIXME around 1E-4 we switch from a single data stream to multiple streams...
        # clearly we should expect any data sent to act as a single stream (obviously given the doccumentation
        transport.write("testing post {} ?".format(i).encode())

    transport.write(dumps([random.random() for _ in range(100)]))
    #a = yield from transport  # WHAT having this in here at all causes main to be skipped?!?!
    #print('it works!',a)
    transport.write(dumps([random.random() for _ in range(100)]))
    transport.write(dumps([random.random() for _ in range(100)]))
    transport.write(dumps([random.random() for _ in range(100)]))
    transport.write(dumps('numpy?!'))
    transport.write(dumps(rand(100)))
    transport.write(dumps(rand(100)))
    #TODO we can make scheduling things nice by using run_until_complete on futures associated with each write IF we care

    #embed()  # if this is anything like calling run() .... this will work nicely
    #try:
        # TODO how to send in new writes??? yield or something?
        #clientLoop.run_forever()
    #except KeyboardInterrupt:
        #print('exiting...')
    #finally:
        #clientLoop.close()
    #request = Request('test..','test',(1,2,3),None)  # FIXME this breaks stop detection!
    request = Request('test.','test',(1,2,3),None)
    print('th',request.hash_,'rh',hash(request))
    rendMan.submit_request(request)
    rendMan.submit_request(request)
    rendMan.submit_request(request)
    rendMan.submit_request(request)
    rendMan.submit_request(request)
    rendMan.submit_request(request)
    rendMan.submit_request(request)
    #protocol2.send_request(request)
    #TODO likely to need a few tricks to get run() and loop.run_forever() working in the same file...
    # for simple stuff might be better to set up a run_until_complete but we don't need that complexity
    #embed()
    run_for_time(clientLoop,10)
    print("testing prediction caching")
    request2 = Request('prediction','who knows',(2,3,4),None)
    rendMan.submit_request(request2)
    rendMan.submit_request(request2)
    run_for_time(clientLoop,4)
    transport.write_eof()
    clientLoop.close()
    #eventLoop.run_until_complete(run_panda)


if __name__ == "__main__":
    #for _ in range(10):
    main()
