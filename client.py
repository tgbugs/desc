#!/usr/bin/env python3.4

import asyncio
import random
import pickle
import zlib
import ssl
from time import sleep
from IPython import embed
from numpy.random import rand

from panda3d.core import GeomNode

from defaults import CONNECTION_PORT, DATA_PORT
from request import Request, DataByteStream


# XXX NOTE TODO: There are "DistributedObjects" that exist in panda3d that we might be able to use instead of this???
    #that would vastly simplify life...? ehhhhh



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

class newConnectionProtocol(asyncio.Protocol):
    """ this is going to be done with fixed byte sizes known small headers """
    def connection_made(self, transport):
        self.transport = transport
        self.transport.write(b'I promis I real client, plz dataz')
        #send public key (ie the account we are looking for) #their password should unlock a local key which 

    def data_received(self, data):
        token = b''
        token_start = data.find(DataByteStream.OP_TOKEN)  # FIXME sadly we'll probably need to deal with splits again
        if token_start != -1:
            token_start += DataByteStream.OPCODE_LEN
            token = data[token_start:token_start+DataByteStream.TOKEN_LEN]
        if token:
            self.future_token.set_result(token)
            self.transport.write_eof()

    def connection_lost(self, exc):
        if exc is None:
            print("New connection transport closed.")

    @asyncio.coroutine
    def get_data_token(self,future):
        self.future_token = future
        yield from future

class dataProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        transport.write(b'hello there')
        self.transport = transport
        self.__receiving__ = False
        self.__block__ = b''  # TODO we almost certainly will need this

    def data_received(self, data):
        """ receive bam files that come back on request
            we can tag them with a request id if needs be
            this way we can also just start sending bam files
            as soon as the connection has been created if they
            arent cached
        """
        print("received",data)  # this *should* just be bam files coming back, no ids? or id header?
        response_start = data.find(DataByteStream.OP_BAM)  # TODO modify this so that it can detect any of the types
        if response_start != -1:
            response_start += DataByteStream.OPCODE_LEN
            hash_start = response_start + DataByteStream.CACHE_LEN
            bam_start = hash_start + DataByteStream.MD5_HASH_LEN
            bam_stop = bam_start + data[bam_start:].find(DataByteStream.STOP)  # FIXME make sure the bam byte stream doesnt have this in there...
        cache = int(data[response_start:response_start + DataByteStream.CACHE_LEN])
        request_hash = data[hash_start:hash_start + DataByteStream.MD5_HASH_LEN]
        bam_data = data[bam_start:bam_stop]  # FIXME this may REALLY need to be albe to split across data_received calls...
        print('')
        print('bam_data',bam_data)
        if cache:
            # TODO this is second field in header
            self.update_cache(request_hash, bam_data)  # TODO: the mapping between requests and the data in the database needs to be injective
        else:  # this data was generated in response to a request
            self.render_bam(request_hash, zlib.decompress(bam_data))

            # hrmmmm how do we get this data out!?
            # its a precache... and the server is the
            # one that is going to be doing predictions
            # about what to load... this should not be
            # synchronous synchrnomus requests should exist
            # but mostly it hsould just be "here, get me this when you can"
    
    def connection_lost(self, exc):  # somehow this never triggers...
        if exc is None:
            print('Data connection closed')
        else:
            print('connection lost')
            #probably we want to try to renegotiate a new connection
            #but that could get really nast if we have a partition and
            #we try to reconnect repeatedly
            #asyncio.get_event_loop().close()  # FIXME probs don't need this

    def send_token(self, token):
        self.transport.write(b'.\x99'+token)

    def send_request(self, request):
        rh = request.hash_
        if not self.check_cache(rh):
            out = dumps(request)
            self.transport.write(out)
            print(out)
        # TODO add that hash to a 'waiting' list and then cross it off when we are done
            # could use that to quantify performance

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

    def update_cache(self, request_hash, bam_data):
        raise NotImplementedError('patch this function with the shared stated version in bamCacheManager')

    def check_cache(self, request_hash):
        raise NotImplementedError('patch this function with the shared stated version in bamCacheManager')

    def render_bam(self, bam):
        raise NotImplementedError('patch this function with a function from a DirectObject')


class collCacheManager:
    def __init__(self,rootNode):
        pass
    

class bamCacheManager:
    """ shared state bam cache """
    def __init__(self,rootNode):
        self.cache = {}
        self.rootNode = rootNode

    def check_cache(self, request_hash):
        try:
            bam = zlib.decompress(self.cache[request_hash])  # FIXME is there some way to make the gzing more transparent?
            self.render_bam(bam)
            print('local cache hit')
            return True
        except KeyError:
            print('local cache miss')
            return False

    def update_cache(self, request_hash, bam_data):
        self.cache[request_hash] = bam_data

    def render_bam(self, render_hash, bam):
        """ render the GEOM only, will hang with nasty error if fed a collision node """
        newNode = GeomNode(render_hash)
        geomNode = newNode.decodeFromBamStream(bam)  # apparently the thing I'm encoding is a node for test purposes... may need something
        #newNode.addGeom(geom)
        self.rootNode.attachNewNode(newNode)

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
    coro_conClient = clientLoop.create_connection(newConnectionProtocol, '127.0.0.1', CONNECTION_PORT, ssl=None)  # TODO ssl

    conTransport, conProtocol = clientLoop.run_until_complete(coro_conClient)
    tokenFuture = asyncio.Future()
    clientLoop.run_until_complete(conProtocol.get_data_token(tokenFuture))
    print('got token',tokenFuture.result())
        
    class FakeNode:
        def attachNewNode(self, node):
            print('pretend like this print statement actually causes things to render')

    rootNode = FakeNode()

    bcm = bamCacheManager(rootNode)

    datCli = type('dataProtocol',(dataProtocol,),
                  {'check_cache':bcm.check_cache,
                   'update_cache':bcm.update_cache,
                   'render_bam':bcm.render_bam})

    coro_dataClient = clientLoop.create_connection(datCli, '127.0.0.1', DATA_PORT, ssl=None)  # TODO ssl
    transport, protocol = clientLoop.run_until_complete(coro_dataClient)
    transport.write(b'testing?')
    transport.write(b'testing?')
    transport.write(b'testing?')
    protocol.send_token(tokenFuture.result())
    #transport.write(b'.\x99'+tokenFuture.result())
    #print("I get here")

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
    protocol.send_request(request)
    protocol.send_request(request)
    #TODO likely to need a few tricks to get run() and loop.run_forever() working in the same file...
    # for simple stuff might be better to set up a run_until_complete but we don't need that complexity
    run_for_time(clientLoop,1)
    transport.write_eof()
    clientLoop.close()
    #eventLoop.run_until_complete(run_panda)


if __name__ == "__main__":
    #for _ in range(10):
    main()
