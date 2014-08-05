#!/usr/bin/env python3.4

import asyncio
import pickle
import ssl
import time
from time import sleep
from concurrent.futures import ProcessPoolExecutor
from threading import Thread

from IPython import embed

from request import DataByteStream
from defaults import CONNECTION_PORT, DATA_PORT


# XXX NOTE TODO: There are "DistributedObjects" that exist in panda3d that we might be able to use instead of this???
    #that would vastly simplify life...? ehhhhh

def dumps(object_):
    """ Special dumps that adds a double stop to make deserializing easier """
    return pickle.dumps(object_)+b'.'

class no_repr(tuple):
    def __repr__(self):
        return "You do NOT want to see all these bytes in a debug!"

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
    def get_data_token(self, timeout = None):
        #yield from self.future_token
        yield from asyncio.wait_for(self.future_token, timeout)

        #try: yield from self.future_token
        #except asyncio.futures.InvalidStateError as e:
            #print(e)
            #print('ssuming that this is because the future is already finished')

    #def wait_for_token(self, timeout = None):
        #self.event_loop.run_until_complete(asyncio.wait_for(self.future_token, timeout))

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
            data_tuple = no_repr(data_tuple)
            #print('yes we are trying to render stuff')
            #self.event_loop.run_in_executor( None, self.set_nodes, request_hash, data_tuple )
            #self.event_loop.call_soon_threadsafe(self.set_nodes, request_hash, data_tuple)  #still segfaults even if this is threadsafe
            #sleep(.1)
            #try:
                #if not self.cache[request_hash]:
            self.set_nodes(request_hash, data_tuple)
            #except KeyError:
                #pass  # FIXME currently not caching anything to hunt down the lockup bug
            #self.set_nodes(*output)
            self.__block__ = self.__block__[self.__block_size__:]
            self.__block_size__ = None
            self.__block_tuple__ = None
            self.data_received(b'')  # lots of little messages will bollox this

    def connection_lost(self, exc):  # somehow this never triggers...
        if exc is None:
            print('Data connection lost')
            print('trying to reconnect')
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)  # this is a hack
            #sleep(1)
            self.__timer_start__ = time.time()
            taskMgr.add(self.recon_task,'recon_task')  # FIXME
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

    def recon_task(self, task):  # FIXME
        if time.time() - self.__timer_start__ > 10:
            print('running recon task')
            try:
                coro_conClient = newConnectionProtocol('127.0.0.1', CONNECTION_PORT, ssl=None)
                conTransport, conProtocol = self.event_loop.run_until_complete(coro_conClient)
                self.event_loop.run_until_complete(conProtocol.get_data_token(1))  # FIXME still blocks ;_;
                self.token = conProtocol.future_token.result()
                coro_dataClient = self.event_loop.create_connection(lambda: self, '127.0.0.1', DATA_PORT, ssl=None)
                self.event_loop.run_until_complete(coro_dataClient) # can this work with with?
                asyncThread = Thread(target=self.event_loop.run_forever)
                asyncThread.start()
                taskMgr.remove(task.getName())
            except (ConnectionRefusedError, TimeoutError) as e:
                self.__timer_start__ = time.time()
            finally:
                return task.cont
        else:
            return task.cont

    def send_request(self, request):
        """ this is called BY renderManager.get_cache !!!!"""
        out = dumps(request)
        self.transport.write(out)

        # TODO add that hash to a 'waiting' list and then cross it off when we are done
            # could use that to quantify performance
            # XXX need this to prevent sending duplicate requests

    def process_responses(self, response_generator):  # XXX deprecated
        # TODO this should be implemented in a subclass specific to panda, same w/ the server
        for request_hash, data_tuple in response_generator:
            #print('yes we are trying to render stuff')
            #self.event_loop.run_in_executor( None , lambda: self.set_nodes(request_hash, data_tuple) )  # amazingly this works!
            self.set_nodes(request_hash, data_tuple)

    def set_nodes(self, request_hash, data_tuple):
        raise NotImplementedError('patch this function with the shared stated version in renderManager')

    def render_set_send_request(self, send_request:'function'):
        raise NotImplementedError('patch this function with the shared stated version in renderManager')

def main():
    import sys

    # render setup
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import loadPrcFileData
    from panda3d.core import PStatClient

    from render_manager import renderManager
    from selection import BoxSel
    from util import ui_text, console, exit_cleanup, frame_rate, startup_data
    from ui import CameraControl, Axis3d, Grid3d, GuiFrame

    # fix sys module reference
    sys.modules['core'] = sys.modules['panda3d.core']

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
    ppe = ProcessPoolExecutor()
    clientLoop.set_default_executor(ppe)

    rendMan = renderManager(clientLoop)

    bs = BoxSel(frames)


    # TODO ssl contexts
    conContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cadata=None)  # TODO cadata should allow ONLY our self signed, severly annoying to develop...
    dataContext = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)

    datCli_base = type('dataProtocol',(dataProtocol,),
                  {'set_nodes':rendMan.set_nodes,  # FIXME this needs to go through make_nodes
                   'render_set_send_request':rendMan.set_send_request,
                   'cache':rendMan.cache,
                   'event_loop':clientLoop })  # FIXME we could move event_loop to __new__? 

    coro_conClient = newConnectionProtocol('127.0.0.1', CONNECTION_PORT, ssl=None)
    conTransport, conProtocol = clientLoop.run_until_complete(coro_conClient)
    clientLoop.run_until_complete(conProtocol.get_data_token())
    token = conProtocol.future_token.result()


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
