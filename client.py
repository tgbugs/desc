#!/usr/bin/env python3.4

import asyncio
import pickle
import ssl
import sys
from time import sleep
from concurrent.futures import ProcessPoolExecutor

from IPython import embed

from defaults import CONNECTION_PORT, DATA_PORT
from request import Request, DataByteStream
from request import FAKE_REQUEST, FAKE_PREDICT, RAND_REQUEST
from dataIO import treeMe

#fix sys module reference
sys.modules['core'] = sys.modules['panda3d.core']

# XXX NOTE TODO: There are "DistributedObjects" that exist in panda3d that we might be able to use instead of this???
    #that would vastly simplify life...? ehhhhh

class newConnectionProtocol(asyncio.Protocol):  # this could just be made into a token getter...
    """ this is going to be done with fixed byte sizes known small headers """
    def __new__(cls, *args, event_loop=None, **kwargs:'for create_connection'):
        """ evil and unpythonic, this no longer behaves like a class """
        future = asyncio.Future(loop=event_loop)
        instance = super().__new__(cls)
        if event_loop:
            instance.event_loop = event_loop
        else:
            instance.event_loop = asyncio.get_event_loop()
        instance.future_token = future
        coro = instance.event_loop.create_connection(lambda: instance, *args, **kwargs)
        return coro

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
            request_hash, data_tuple = DataByteStream.decodeResponseStream(self.__block__[:self.__block_size__], *self.__block_tuple__)
            #print('yes we are trying to render stuff')
            #self.event_loop.run_in_executor( None, self.set_nodes, request_hash, data_tuple )
            self.event_loop.call_soon(self.set_nodes, request_hash, data_tuple)  #still segfaults even if this is threadsafe
            #self.set_nodes(*output)
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
        #print("received data length ",len(data))  # this *should* just be bam files coming back, no ids? or id header?
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
            print('Data connection lost')
            print('trying to reconnect')
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)  # this is a hack
            sleep(.1)
            taskMgr.add(self.reup_con,'reupTask')
            #self.reup_con()
            #t = asyncio.Task(self.reup_con(), loop=self.event_loop)
            #t = asyncio.Task(self.reup_con, loop=self.event_loop)  # FIXME replace with self.event_loop.create_task(self.reup_con) 3.4.2
            #print(t)

            # FIXME why does literally terminiating the server cause this to survive?
        else:
            print('connection lost error was',exc)
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
            #print('yes we are trying to render stuff')
            self.event_loop.run_in_executor( None , lambda: self.set_nodes(request_hash, data_tuple) )  # amazingly this works!

    def set_nodes(self, request_hash, data_tuple):
        raise NotImplementedError('patch this function with the shared stated version in renderManager')

    def render_set_send_request(self, send_request:'function'):
        raise NotImplementedError('patch this function with the shared stated version in renderManager')

def main():
    from threading import Thread

    # render setup
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import loadPrcFileData
    from panda3d.core import PStatClient

    from render_manager import renderManager
    from selection import BoxSel
    from util import ui_text, console, exit_cleanup, frame_rate, startup_data
    from ui import CameraControl, Axis3d, Grid3d, GuiFrame


    PStatClient.connect() #run pstats in console
    loadPrcFileData('','view-frustum-cull 0')
    base = ShowBase()

    base.setBackgroundColor(0,0,0)
    base.disableMouse()
    # TODO init all these into a dict or summat?
    startup_data()
    frame_rate()
    ut = ui_text()
    grid = Grid3d()
    axis = Axis3d()
    cc = CameraControl()
    con = console()

    # TODO make it so that all the "root" nodes for the secen are initialized in their own space, probably in with defaults or something globalValues.py?
    # roots

    # frames XXX FIXME TODO this is a terrible way to pass this around...
    frames = {
        'data':GuiFrame('Data view')
    }

    #asyncio and network setup
    clientLoop = asyncio.get_event_loop()

    bs = BoxSel(frames)

    rendMan = renderManager()

    #ppe = ProcessPoolExecutor()
    #clientLoop.set_default_executor(ppe)  # FIXME this doesn't work ;_;

    # TODO ssl contexts
    conContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cadata=None)  # TODO cadata should allow ONLY our self signed, severly annoying to develop...
    dataContext = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)

    datCli_base = type('dataProtocol',(dataProtocol,),
                  {'set_nodes':rendMan.set_nodes,  # FIXME this needs to go through make_nodes
                   'render_set_send_request':rendMan.set_send_request,
                   'event_loop':clientLoop })  # FIXME we could move event_loop to __new__? 

    coro_conClient = newConnectionProtocol('127.0.0.1', CONNECTION_PORT, ssl=None)
    conTransport, conProtocol = clientLoop.run_until_complete(coro_conClient)
    clientLoop.run_until_complete(conProtocol.get_data_token())
    token = conProtocol.future_token.result()

    def recon_task(self, task):
        taskMgr.remove('reupTask')
        return task.cont
        try:
            coro_conClient = newConnectionProtocol('127.0.0.1', CONNECTION_PORT, ssl=None)
            conTransport, conProtocol = clientLoop.run_until_complete(coro_conClient)
            clientLoop.run_until_complete(conProtocol.get_data_token())
            self.token = conProtocol.future_token.result()
            coro_dataClient = clientLoop.create_connection(lambda: self, '127.0.0.1', DATA_PORT, ssl=None)
            clientLoop.run_until_complete(coro_dataClient) # can this work with with?
            asyncThread = Thread(target=clientLoop.run_forever)
            asyncThread.start()
            taskMgr.remove('reupTask')
            return task.cont
        except ConnectionRefusedError as e:
            return task.cont

    setattr(dataProtocol, 'reup_con', recon_task)

    datCli = datCli_base(token)
    coro_dataClient = clientLoop.create_connection(datCli, '127.0.0.1', DATA_PORT, ssl=None)
    transport, protocol = clientLoop.run_until_complete(coro_dataClient) # can this work with with?

    #make sure we can exit
    el = exit_cleanup(clientLoop)  #use this to call stop() on run_forever

    #taskMgr.add(setup_connection,'reupTask')

    #run it
    asyncThread = Thread(target=clientLoop.run_forever)
    asyncThread.start()
    #embed()
    run()  # this MUST be called last because we use sys.exit() to terminate
    assert False, 'Note how this never gets printed due to sys.exit()'


if __name__ == "__main__":
    #for _ in range(10):
    main()
