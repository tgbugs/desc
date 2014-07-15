#!/usr/bin/env python3.4

import asyncio
import pickle
import ssl
import zlib
import os  # for dealing with firewall stuff
from collections import defaultdict, deque
from time import sleep

from numpy.random import bytes as make_bytes
from IPython import embed

from defaults import CONNECTION_PORT, DATA_PORT
from request import Request, DataByteStream

from massive_bam import massive_bam as example_bam

#TODO logging...

class requestManager(object):
    """ Server side class that listens for requests to render data to bam
        Should cooperate with another predictive class that generates related
        requests.

        This is the main code to handle all incomming request for a *single* session
        it itself can dispatch to multiple workers but there should only be one entry
        and one exit for a session, every new session gets its own instance of this?

        Yes, yes I know, http handles a lot of this stuff already, but we don't really
        need all those features.
    """
    def __init__(self,port):
        """ Set up to listen for requests for data from the render client.
            These requests will then spawn processes that retrieve and
            render the data and related data the user might want to view.
        """
        pass
    def listenForRequest(self):
        pass
    def handleRequest(self):
        pass

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
        print(self.ip,data)
        if data == b'I promis I real client, plz dataz':
            self.transport.write(b'ok here dataz')
            token = make_bytes(DataByteStream.TOKEN_LEN)
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
        os.system('echo "kittens!"')
    
    def update_token_data(self, ip, token):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

class dataServerProtocol(asyncio.Protocol):
    #first of all ignore all packets received on 
    #the port in question that have not passed auth
    def __init__(self):
        self.token_received = False
        self.__splitStopPossible__ = False
        self.__receiving__ = False
        self.__block__ = b''

    def connection_made(self, transport):
        #check for session token
        peername = transport.get_extra_info('peername')
        print("connection from:",peername)
        try:
            self.expected_tokens = self.get_tokens_for_ip(peername[0])
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
            if self.__receiving__:
                self.__block__ += data
                data = self.__block__
            try:
                token = DataByteStream.decodeToken(data)
                if token in self.expected_tokens:
                    self.token_received = token
                    self.remove_token_for_ip(self.ip, self.token_received)  # do this immediately so that the token cannot be reused!
                    print(self.pprefix,'token auth successful')
                    self.process_requests(self.process_data(data))  # run this in case a request follows the token
                else:
                    print(self.pprefix,'token auth failed, received token not expected')
                    # should probably send a fail message? where else are they going to get their token??
                self.__receiving__ = False
                self.__block__ = b''
            except IndexError:
                if not self.__receiving__:
                    self.__receiving__ = True
                    self.__block__ = data

        else:
            request_generator = self.process_data(data)
            self.process_requests(request_generator)

    def eof_received(self):
        #close the firewall!
        print(self.pprefix,'data server got eof')

    def process_data(self,data):
        if self.__block__:
            data = self.__block__ + data

        split = data.split(DataByteStream.STOP)

        if len(split) is 1:  # NO STOPS
            self.__block__ += data
            yield None
        else:  # len(split) > 1:
            self.__block__ = split.pop()  # this will always hit b'' or an incomplete pickle
            yield from DataByteStream.decodePickleStreams(split)

    def _process_data(self,data):  # FIXME does this actually go here? or should it be in code that works directly on the transport object??!
        """ generator that generates requests from the incoming data stream """
        pickleStop = 0
        if not self.__receiving__:
            pickleStart = data.find(b'\x80')
            if pickleStart != -1:
                pickleStop = data.find(b'..') + 1
                if not pickleStop:
                    pickleStop = None
                self.__block__ += data[pickleStart:pickleStop]
        else:
            if self.__receiving__ == 'pickle':
                pickleStop = data.find(b'..') + 1
                if self.__splitStopPossible__ and data[0] == b'.':
                    pickleStop = 0
                    self.__splitStopPossible__ = False
                elif not pickleStop:
                    pickleStop = None
                self.__block__ += data[:pickleStop]

        if pickleStop is None:  # this is confusing, None only occurs if we are receiving and assumes all transport is done by pickle
            self.__receiving__ = 'pickle'  # FIXME why we set this every time >_<
            if data[-1] == b'.':
                self.__splitStopPossible__ == True
            yield None
        elif self.__block__:  # make sure we don't have another pickle lurking in the rest of the data!
            try:
                thing = pickle.loads(self.__block__)
                if type(thing) != Request:  # throw out any data that is not a request
                    thing = None
            except (ValueError, EOFError, pickle.UnpicklingError) as e:
                block = self.__block__
                self.__block__ = b''
                self.__receiving__ = False
                print(self.pprefix,block)
                raise e
            self.__block__ = b''
            yield thing
            rest = data[pickleStop:]
            self.__receiving__ = False  # dont know if need this here, but just incase
            if len(rest) > 1:
                yield from self.process_data(rest[1:])  # FIXME this can triggers recursion error on too many ..
            self.__receiving__ = False

    #@asyncio.coroutine
    def process_requests(self,request_generator):  # TODO we could also use this to manage request_prediction and have the predictor return a generator
        print('processing requests')
        def do_request(request):
            rh, bam_data = self.get_bam(request)
            coll_data = b'this is collision data'
            ui_data = b'this is ui data'
            sleep(1)
            bam_stream = DataByteStream.makeBamStream(rh, bam_data, cache=False)
            coll_stream = DataByteStream.makeCollStream(rh, coll_data, cache=False)
            ui_stream = DataByteStream.makeUIStream(rh, ui_data, cache=False)
            self.transport.write(bam_stream + coll_stream + ui_stream)

        for request in request_generator:
            if request is not None:
                self.event_loop.run_in_executor( None, lambda: do_request(request) )
                self.event_loop.run_in_executor( None, lambda: self.request_prediction(request) )

    def get_bam(self,request):
        """ returns the request hash and a compressed bam stream """
        print('th',request.hash_,'rh',hash(request))
        rh =  request.hash_
        print(rh)
        bam = self.get_cache(rh)
        if bam is None:
            bam = zlib.compress(self.make_bam(request))  # LOL wow is there redundancy in these bams O_O zlib to the rescue
            self.update_cache(rh, bam)
        return rh, bam

    def request_prediction(self, request):
        #should compute a set of n related requests, and send their hash + bam to the client and to the local cache
        for preq in self.make_predictions(request):
            rh, bam_data = self.get_bam(preq)
            coll_data = b'this is collision data'
            ui_data = b'this is ui data'
            bam_stream = DataByteStream.makeBamStream(rh, bam_data, cache=True)
            coll_stream = DataByteStream.makeCollStream(rh, coll_data, cache=True)
            ui_stream = DataByteStream.makeUIStream(rh, ui_data, cache=True)
            self.transport.write(bam_stream + coll_stream + ui_stream)
            #yield None
        #return
        #yield

    #things that go to the database
    def make_bam(self, request):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

    def make_predictions(self, request):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

    # shared state functions
    def get_cache(self, request_hash):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

    def update_cache(self, request_hash, bam_data):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

    def get_tokens_for_ip(self, ip):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

    def remove_token_for_ip(self, ip, token):
        raise NotImplemented('This should be set at run time really for message passing to shared state')

class bamManager:  # TODO we probably move this to its own file?
    def __init__(self):
        #setup at connection to whatever database we are going to use
        pass
    def make_bam(self, request):
        # TODO so encoding the collision nodes to a bam takes a REALLY LONG TIME
        # it seems like it might be more prudent to serialize to (x,y,z,radius) or maybe a type code?
        # yes, the size of the bam serialization is absolutely massive, easily 3x the size in memory
        # also if we send it already in tree form... so that the child node positions are just nested
        # it might be pretty quick to generate the collision nodes
        return example_bam
    def make_predictions(self, request):
        #TODO this is actually VERY easy, because all we need to do is use
            #the list of connected UI elements that we SEND OUT ANYWAY and
            #just prospectively load those models/views
        yield request

class requestCacheManager:
    """ we want to use a global cache so that we don't recompute the same request
        for multiple clients

        we *could* make this persistent if needs be
    """
    def __init__(self, cache_limit = 10000):
        self.cache_limit = cache_limit
        self.cache = {}
        self.cache_age = deque()  # this is a nasty hack, probably need a real tree here at some point

    def check_cache(self, request_hash):  # XXX not used
        try:
            self.cach[request_hash]
            return True
        except KeyError:
            return False

    def get_cache(self, request_hash):
        try:
            bam = self.cache[request_hash]
            self.cache_age.remove(request_hash)
            self.cache_age.append(request_hash)  # basically ranks cache by access frequency
            return bam
        except KeyError:
            return None

    def update_cache(self, request_hash, bam_data):  # TODO only call this if 
        self.cache[request_hash] = bam_data
        self.cache_age.append(request_hash)
        while len(self.cache_age) > self.cache_limit:
            self.cache.pop(self.cache_age.popleft())


class tokenManager:  # TODO this thing could be its own protocol and run as a shared state server using lambda: instance
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
    bm = bamManager()
    datServ = type('dataServerProtocol', (dataServerProtocol,),
                   {'get_tokens_for_ip':tm.get_tokens_for_ip,
                    'remove_token_for_ip':tm.remove_token_for_ip,
                    'get_cache':rcm.get_cache,
                    'update_cache':rcm.update_cache,
                    'make_bam':bm.make_bam,
                    'make_predictions':bm.make_predictions,
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
