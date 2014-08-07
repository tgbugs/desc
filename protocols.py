"""
    All transport protocols and associated files go here. Yes, it is silly
    to put server and client classes in the same file for git, but they do
    talk to eachother, so that might be useful.
"""

import os  # for dealing with firewall stuff?
import asyncio
import pickle
import struct
from multiprocessing import Pipe as mpp
from multiprocessing.reduction import ForkingPickler

from numpy.random import bytes as make_bytes

from panda3d.core import NodePath, PandaNode

from defaults import CONNECTION_PORT, DATA_PORT
from request import DataByteStream
from ipython import embed

###
#   Utility or picklable functions
###

def dumps(object_):
    """ Special dumps that adds a double stop to make deserializing easier """
    return pickle.dumps(object_)+b'.'

class no_repr(tuple):
    def __repr__(self):
        return "You do NOT want to see all these bytes in a debug!"

def make_response(pipe, request, respMaker):
    """ returns the request hash and a compressed bam stream """
    rh =  request.hash_
    data_tuple = respMaker.make_response(request)  # LOL wow is there redundancy in these bams O_O zlib to the rescue
    data_stream = DataByteStream.makeResponseStream(rh, data_tuple)
    pipe.send_bytes(data_stream)
    pipe.close()
    del pipe


###
#   Client
###

class connectionClientProtocol(asyncio.Protocol):  # this could just be made into a token getter...
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
            #print('__',self,'token_start',token_start,'__')
            token_data = data[token_start:token_start+DataByteStream.LEN_OPCODE+DataByteStream.LEN_TOKEN]
        if token_data:
            self.future_token.set_result(token_data)
            self.transport.write_eof()

    def connection_lost(self, exc):
        if exc is None:
            pass
            #print("New connection transport closed.")

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

class dataClientProtocol(asyncio.Protocol):  # in theory there will only be 1 of these per interpreter... so could init ourselves with the token
    def __new__(cls, set_nodes, render_set_send_request, cache, event_loop):
        cls.set_nodes = set_nodes
        cls.render_set_send_request = render_set_send_request
        #cls.cache = cache
        cls.event_loop = event_loop
        cls.__new__ = super().__new__
        return cls

    def __init__(self):
        self.transport = None
        self.__to_send__ = b''
        self.render_set_send_request(self.send_request)

        self.__block__ = b''
        self.__block_size__ = None
        self.__block_tuple__ = None

    def connection_made(self, transport):
        transport.write(b'hello there')
        transport.write(self.token)
        transport.write(self.__to_send__)
        self.__to_send__ = b''
        self.transport = transport

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
            request_hash, data_tuple = DataByteStream.decodeResponseStream(self.__block__[:self.__block_size__], *self.__block_tuple__)
            data_tuple = no_repr(data_tuple)
            self.set_nodes(request_hash, data_tuple)
            self.__block__ = self.__block__[self.__block_size__:]
            self.__block_size__ = None
            self.__block_tuple__ = None
            self.data_received(b'')  # lots of little messages will bollox this

    def connection_lost(self, exc):  # somehow this never triggers...
        self.transport = None  # FIXME race condition with send?
        if exc is None:
            print('Data connection lost trying to reconnect')
        if exc == 'START':
            print('connecting to data server')
        else:
            print('connection lost error was',exc)

        return asyncio.Task(self.connection_task(), loop=self.event_loop)

    @asyncio.coroutine
    def connection_task(self):
        """ MAGIC :D """
        while True:
            coro_conClient = connectionClientProtocol('127.0.0.1', CONNECTION_PORT, event_loop=self.event_loop, ssl=None)
            try:
                _, conProtocol = yield from asyncio.Task(coro_conClient, loop=self.event_loop)
                self.token = yield from asyncio.wait_for(conProtocol.future_token, None, loop=self.event_loop)
                coro_dataClient = self.event_loop.create_connection(lambda: self, '127.0.0.1', DATA_PORT, ssl=None)
                yield from asyncio.Task(coro_dataClient, loop=self.event_loop)
                print('Got connection to: ')  # TODO
                break
            except ConnectionRefusedError:
                yield from asyncio.sleep(5, loop=self.event_loop)

    def send_request(self, request):
        """ this is called BY renderManager.get_cache !!!!"""
        out = dumps(request)
        if self.transport is None:
            self.__to_send__ += out
        else:
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


###
#   Server
###

class connectionServerProtocol(asyncio.Protocol):  # this is really the auth server protocol
    """ Define the protocol for handling basic connections
        should spin up client specific connections?

        Turns out that this automatically spins up isolated
        versions of itself for each connection, we just need
        to make sure that we print the client info ahead of the
        message so we know which connection we are getting data
        about
    """
    def __new__(cls, tm):
        cls.tm = tm
        cls.__new__ = super().__new__
        return cls

    def connection_made(self, transport):
        cert = transport.get_extra_info('peercert')
        if not cert:
            #make a cert, sign it ourselves so we know it came from us, and send it to the client
            #use that cert id to get stored data if needs be
            #this is NOT secure
            pass
        self.transport = transport
        self.pprefix = transport.get_extra_info('peername')
        self.ip = transport.get_extra_info('peername')[0]
        #for now we are just going to give clients peer certs and not worry about it

        #client telling us this is a new user request

        #client telling us this is an existing auth

        #client telling us this is 

        #not new user
        #if not add it
        #request the passphrase locked private key #this fails because people need to be able to change passwords >_<

        #make some bytes
        #encrypt those bytes with their public key
        #send them the encrypted bytes
        #wait to get the unencrypted bytes back
        #check if they match #make sure this is done in constant time



        #print('connection from: %s'%peername)


        #TODO I think we need to have a way to track 'sessions' or 'clients'
            #NOT users, though that would still be useful if people are using
            #the same system
            #however, auth will all be done locally on the machine with the
            #proper protections to prevent a malicious client fubar all
        #since we all we really want is to be able to give a unique id its
        #existing data...
        #the ident and auth code probably needs to go here since establishing
        #the transport is PRIOR to that, getting the SSLed channel comes first
        #but we don't want application auth mixed up in that, so do it here
        #XXX I suppose that we could do it all with ssl certs?
            #ie: don't implement your own auth system tis hard

        #if everything succeeds

    def data_received(self, data):  # data is a bytes object
        done = False
        #print(self.pprefix,data)
        if data == b'I promis I real client, plz dataz':
            self.transport.write(b'ok here dataz')
            token = make_bytes(DataByteStream.LEN_TOKEN)  # FIXME
            token_stream = DataByteStream.makeTokenStream(token)
            self.tm.update_ip_token_pair(self.ip, token)
            self.open_data_firewall(self.ip)
            #DO ALL THE THINGS
            #TODO pass that token value paired with the peer cert to the data server...
                #if we use client certs then honestly we dont really need the token at all
                #so we do need the token, but really only as a "we're ready for you" message
            #open up the firewall to give that ip address access to that port
            #print('token stream',token_stream)
            self.transport.write(token_stream)
        if done:
            self.transport.write_eof()

    def eof_received(self):
        #clean up the connection and store stuff because the client has exited
        self.transport.close()
        print('New data connection request from', self.ip, 'was successful.')

    def register_data_server_token_setter(self,function):
        self.send_ip_token_pair = function

    def open_data_firewall(self, ip_address):
        """ probably nftables? """
        # TODO NOTE: this should probably be implemented under the assumption that
            #the data server is NOT the same as the connection server
        os.system('echo "firewall is now kittens!"')

class dataServerProtocol(asyncio.Protocol):
    """ Data server protocol that holds the code for managing incoming data
        streams. It should be data agnoistic, thus try to keep the code that
        actually manipulates the data in DataByteStream.
    """

    def __new__(cls, event_loop, respMaker, rcm, tm, ppe):
        cls.event_loop = event_loop
        cls.respMaker = respMaker
        cls.rcm = rcm
        cls.tm = tm
        cls.ppe = ppe  # process pool executor
        cls.__new__ = super().__new__
        return cls
        

    def __init__(self):
        self.token_received = False
        self.__block__ = b''
        self.__resp_done__ = False
        self.respMaker = self.respMaker()
        self.requests_sent = set()

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        try:
            self.expected_tokens = self.tm.get_tokens_for_ip(peername[0])
            #self.get_tokesn_for_ip = None  # XXX will fail, reference to method persists
            self.transport = transport
            self.pprefix = peername
            self.ip = peername[0]
        except KeyError:
            transport.write(b'This is a courtesy message alerting you that your'
                            b' IP is not on the list of IPs authorized to make'
                            b' data connections. Query: How did you get through'
                            b' the firewall?')
            # probably should log this event
            transport.write_eof()
            print(peername,'This IP is not in the list (dict) of know ips. Terminated.')

    def data_received(self, data):
        if not self.token_received:
            self.__block__ += data
            try:
                token, token_end = DataByteStream.decodeToken(self.__block__)
                if token in self.expected_tokens:
                    self.token_received = True  # dont store the token anywhere in memory, ofc if you can find the t_r bit and flip it...
                    self.tm.remove_token_for_ip(self.ip, token)  # do this immediately so that the token cannot be reused!
                    #self.remove_token_for_ip = None  # done with it, remove it from this instance XXX will fail
                    self.expected_tokens = None  # we don't need access to those tokens anymore
                    del self.expected_tokens
                    print("Data connection from:",self.pprefix,"token auth successful.")
                    self.__block__ = self.__block__[token_end:]  # nasty \x80 showing up
                    self.process_requests(self.process_data(b''))  # run this in case a request follows the token, this will reset block
                else:
                    print("Data connection from:",self.pprefix,"token auth failed, token not expected.")
                    self.__block__ = b''
                    # should probably send a fail message? where else are they going to get their token??
            except IndexError:
                pass  # block already has the existing data wait for more

        else:
            request_generator = self.process_data(data)  # FIXME one big issue with this is there is a HUGE glut before we start returning >_<
            self.process_requests(request_generator)  # FIXME too many calls to this...

    def eof_received(self):
        self.transport.close()
        os.system("echo 'firewall is now DRAGONS!'")  # TODO actually close
        print(self.pprefix,'data server got eof')

    def process_data(self,data):  # XXX is this actually a coroutine?
        self.__block__ += data
        split = self.__block__.split(DataByteStream.STOP)  # split requires a copy?
        if len(split) is 1:  # NO STOPS
            if DataByteStream.OP_PICKLE not in self.__block__:  # NO OPS
                self.__block__ = b''
            yield None  # self.__block__ already updated
        else:  # len(split) > 1:
            self.__block__ = split.pop()  # this will always hit b'' or an incomplete pickle
            yield from DataByteStream.decodePickleStreams(split)

    def process_requests(self, requests:'iterable', pred = 0):  # TODO we could also use this to manage request_prediction and have the predictor return a generator
        #print(self.pprefix,'processing requests')
        pipes = []
        for_pred = []
        for request in requests:  # FIXME this blocks... not sure it matters since we are waiting on the incoming blocks anyway?
            if request is not None and request.hash_ not in self.requests_sent:  # FIXME and not rerequested
                self.requests_sent.add(request.hash_)
                data_stream = self.rcm.get_cache(request.hash_)  # FIXME this is STUID to put here >_<
                if data_stream is None:
                    recv, send = mpp(False)
                    pipes.append(recv)
                    self.event_loop.run_in_executor( self.ppe, make_response, send, request, self.respMaker )
                    for_pred.append(request)
                else:
                    self.transport.write(data_stream)
                    #print('WHAT WE GOT THAT HERE')
                    #print('data stream tail',data_stream[-10:])

        if pipes:
            while 1:
                pops = []
                for i, recv in enumerate(pipes):
                    try:
                        if recv.poll():
                            _data_stream = recv.recv_bytes()  # this would raise EOF but we pop
                            self.transport.write(_data_stream)
                            _request_hash = _data_stream[DataByteStream.LEN_OPCODE:DataByteStream.LEN_OPCODE + DataByteStream.LEN_HASH]
                            self.rcm.update_cache(_request_hash, _data_stream)
                            recv.close()
                            pops.append(i)
                    except EOFError:
                        print("The other end was closed before we received anything!?")

                if pops:
                    pops.sort()
                    pops.reverse()  # so that the index doesn't change
                    #print(pipes)
                    #print('things to pop',pops)
                    for index in pops:
                        #print("popping:",index)
                        pipes.pop(index)
                if not pipes:
                    break

            #print(self.pprefix, 'finished processing requests')
        #else:
            #print(self.pprefix, 'there were no requests')
        
        #do prediction
        if pred < 1:
            for request in for_pred:
                self.process_requests(self.respMaker.make_predictions(request), pred + 1)

###
#   Pipes
###

class collPipeProtocol(asyncio.Protocol):
    """ use with lambda: instance() """
    def __new__(cls, cache, geom_add_queue, coll_add_queue, collRoot):
        cls.cache = cache
        cls.geom_add_queue = geom_add_queue
        cls.coll_add_queue = coll_add_queue
        cls.__new__ = cls._new_
        cls.collRoot = collRoot
        return cls
    
    @staticmethod
    def _new_(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, request_hash, geom, ui, render_ = False):
        if render_:
            self.geom_add_queue.append(geom)
        self.request_hash = request_hash
        self.geom = geom
        self.nodes = []
        self.ui = ui
        self.render_ = render_
        self._data = b''
    
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):  # I'm worried this will be slower...
        data = self._data + data
        while True:
            size, = struct.unpack("!i", data[:4])
            if len(data) < size:
                self._data = data
                break
            node = ForkingPickler.loads(data[4:4+size])
            if self.render_:
                node.reparentTo(self.collRoot)
                #self.coll_add_queue.append(node)
            self.nodes.append(node)
            data = data[4+size:]
            if len(data) < 4:
                self._data = data
                break
        
    def eof_received(self):
        # TODO is it silly to use a future in place of nodes?
        self.cache[self.request_hash] = self.geom, self.nodes, self.ui
        print('got eof')
        return True
