#!/usr/bin/env python3.4

import asyncio
import pickle
import ssl
import os  # for dealing with firewall stuff
from uuid import uuid4
from collections import defaultdict, deque
from time import sleep

import numpy as np
from numpy.random import bytes as make_bytes
from IPython import embed

from defaults import CONNECTION_PORT, DATA_PORT
from request import Request, DataByteStream

from massive_bam import massive_bam as example_bam

#TODO logging...
class connectionServerProtocol(asyncio.Protocol):  # this is really the auth server protocol
    """ Define the protocol for handling basic connections
        should spin up client specific connections?

        Turns out that this automatically spins up isolated
        versions of itself for each connection, we just need
        to make sure that we print the client info ahead of the
        message so we know which connection we are getting data
        about
    """
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
        print(self.pprefix,data)
        if data == b'I promis I real client, plz dataz':
            self.transport.write(b'ok here dataz')
            token = make_bytes(DataByteStream.LEN_TOKEN)
            token_stream = DataByteStream.makeTokenStream(token)
            self.update_ip_token_pair(self.ip, token)
            self.open_data_firewall(self.ip)
            #DO ALL THE THINGS
            #TODO pass that token value paired with the peer cert to the data server...
                #if we use client certs then honestly we dont really need the token at all
                #so we do need the token, but really only as a "we're ready for you" message
            #open up the firewall to give that ip address access to that port
            print('token stream',token_stream)
            self.transport.write(token_stream)
        if done:
            self.transport.write_eof()

    def eof_received(self):
        #clean up the connection and store stuff because the client has exited
        print(self.ip, 'got eof')

    def register_data_server_token_setter(self,function):
        self.send_ip_token_pair = function

    def open_data_firewall(self, ip_address):
        """ probably nftables? """
        # TODO NOTE: this should probably be implemented under the assumption that
            #the data server is NOT the same as the connection server
        os.system('echo "firewall is now kittens!"')
    
    def update_token_data(self, ip, token):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

class dataServerProtocol(asyncio.Protocol):
    """ Data server protocol that holds the code for managing incoming data
        streams. It should be data agnoistic, thus try to keep the code that
        actually manipulates the data in DataByteStream.
    """
    def __init__(self):
        self.token_received = False
        self.__block__ = b''

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print("connection from:",peername)
        try:
            self.expected_tokens = self.get_tokens_for_ip(peername[0])
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
                token = DataByteStream.decodeToken(self.__block__)
                if token in self.expected_tokens:
                    self.token_received = True  # dont store the token anywhere in memory, ofc if you can find the t_r bit and flip it...
                    self.remove_token_for_ip(self.ip, token)  # do this immediately so that the token cannot be reused!
                    #self.remove_token_for_ip = None  # done with it, remove it from this instance XXX will fail
                    self.expected_tokens = None  # we don't need access to those tokens anymore
                    del self.expected_tokens
                    print(self.pprefix,'token auth successful')
                    self.process_requests(self.process_data(b''))  # run this in case a request follows the token, this will reset block
                else:
                    print(self.pprefix,'token auth failed, received token not expected')
                    self.__block__ = b''
                    # should probably send a fail message? where else are they going to get their token??
            except IndexError:
                pass  # block already has the existing data wait for more

        else:
            request_generator = self.process_data(data)
            self.process_requests(request_generator)

    def eof_received(self):
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

    def process_requests(self,request_generator):  # TODO we could also use this to manage request_prediction and have the predictor return a generator
        print(self.pprefix,'processing requests')
        for request in request_generator:  # FIXME this blocks... not sure it matters since we are waiting on the incoming blocks anyway?
            if request is not None:
                self.event_loop.run_in_executor( None, lambda: self.send_response(request) )  # FIXME error handling live?
                self.event_loop.run_in_executor( None, lambda: self.request_prediction(request) )

    def send_response(self,request):
        """ returns the request hash and a compressed bam stream """
        rh =  request.hash_
        data_stream = self.get_cache(rh)
        if data_stream is None:  # FIXME if we KNOW we are going to gz stuff we should do it early...
            data_tuple = self.make_response(request)  # LOL wow is there redundancy in these bams O_O zlib to the rescue
            data_stream = DataByteStream.makeResponseStream(rh, data_tuple)
            self.update_cache(rh, data_stream)
        self.transport.write(data_stream)

    def request_prediction(self, request):
        for preq in self.make_predictions(request):
            self.send_response(preq)

    #things that go to the database
    def make_response(self, request):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

    def make_predictions(self, request):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

    # shared state functions
    def get_cache(self, request_hash):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

    def update_cache(self, request_hash, data_stream):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

    def get_tokens_for_ip(self, ip):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

    def remove_token_for_ip(self, ip, token):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

class responseMaker:  # TODO we probably move this to its own file?
    def __init__(self):
        #setup at connection to whatever database we are going to use
        pass
    def make_response(self, request):
        # TODO so encoding the collision nodes to a bam takes a REALLY LONG TIME
        # it seems like it might be more prudent to serialize to (x,y,z,radius) or maybe a type code?
        # yes, the size of the bam serialization is absolutely massive, easily 3x the size in memory
        # also if we send it already in tree form... so that the child node positions are just nested
        # it might be pretty quick to generate the collision nodes
        n = 10000
        positions = np.cumsum(np.random.randint(-1,2,(n,3)), axis=0)
        uuids = np.array(['%s'%uuid4() for _ in range(n)])
        bounds = np.ones(n) * .5
        example_coll = pickle.dumps((positions, uuids, bounds))  # FIXME putting pickles last can bollox the STOP

        data_tuple = (example_bam, example_coll, b'this is a UI data I swear')
        return data_tuple

    def make_predictions(self, request):
        #TODO this is actually VERY easy, because all we need to do is use
            #the list of connected UI elements that we SEND OUT ANYWAY and
            #just prospectively load those models/views
        request = Request('prediction','who knows',(2,3,4),None)
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

    def get_cache(self, request_hash):
        try:
            data_stream = self.cache[request_hash]
            self.cache_age.remove(request_hash)
            self.cache_age.append(request_hash)  # basically ranks cache by access frequency
            print('server cache hit')
            return data_stream
        except KeyError:
            print('server cache miss')
            return None

    def update_cache(self, request_hash, data_stream):  # TODO only call this if 
        self.cache[request_hash] = data_stream
        self.cache_age.append(request_hash)
        while len(self.cache_age) > self.cache_limit:
            self.cache.pop(self.cache_age.popleft())
        #print('server cache updated with', request_hash, data_stream)


class tokenManager:  # TODO this thing could be its own protocol and run as a shared state server using lambda: instance
#FIXME this may be suceptible to race conditions on remove_token!
    """ shared state for tokens O_O (I cannot believe this works
        As long as these functions do what they say they do this
        could run on mars and no one would really care.
    """
    def __init__(self):
        self.tokenDict = defaultdict(set)
    def update_token_data(self, ip, token):
        self.tokenDict[ip].add(token)
        print(self.tokenDict)
    def get_tokens_for_ip(self, ip):
        print(self.tokenDict)
        return self.tokenDict[ip]
    def remove_token_for_ip(self, ip, token):
        self.tokenDict[ip].remove(token)
        print(self.tokenDict)

def main():
    serverLoop = asyncio.get_event_loop()

    conContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None)
    dataContext = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)

    tm = tokenManager()  # keep the shared state out here! magic if this works

    # commence in utero monkey patching
    conServ = type('connectionServerProtocol', (connectionServerProtocol,),
                   {'update_ip_token_pair':tm.update_token_data})

    #shared state, in theory this stuff could become its own Protocol
    rcm = requestCacheManager(9999)
    respMaker = responseMaker()
    # FIXME here we cannot remove references to these methods from instances
        # because they are defined at the class level and not passed in at
        # run time. We MAY be able to fix this by using a metaclass that
        # constructs these so that when a new protocol is started those methods
        # are passed in and thus can successfully be deleted from a class instance
    datServ = type('dataServerProtocol', (dataServerProtocol,),
                   {'get_tokens_for_ip':tm.get_tokens_for_ip,
                    'remove_token_for_ip':tm.remove_token_for_ip,
                    'get_cache':rcm.get_cache,
                    'update_cache':rcm.update_cache,
                    'make_response':respMaker.make_response,
                    'make_predictions':respMaker.make_predictions,
                    'event_loop':serverLoop })

    coro_conServer = serverLoop.create_server(conServ, '127.0.0.1', CONNECTION_PORT, ssl=None)  # TODO ssl
    coro_dataServer = serverLoop.create_server(datServ, '127.0.0.1', DATA_PORT, ssl=None)  # TODO ssl and this can be another box
    serverCon = serverLoop.run_until_complete(coro_conServer)
    serverData = serverLoop.run_until_complete(coro_dataServer)
    try:
        serverLoop.run_forever()
    except KeyboardInterrupt:
        print('exiting...')
    finally:
        serverCon.close()
        serverData.close()
        serverLoop.close()



if __name__ == "__main__":
    main()
