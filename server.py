#!/usr/bin/env python3.4

import asyncio
import pickle
import ssl
import os  # for dealing with firewall stuff
from collections import defaultdict
from numpy.random import bytes as make_bytes
from IPython import embed

from defaults import CONNECTION_PORT, DATA_PORT

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
            token = make_bytes(256)
            token_message = b'\x99'+token
            self.send_ip_token_pair(self.ip, token)
            self.open_data_firewall(self.ip)
            #DO ALL THE THINGS
            #TODO pass that token value paired with the peer cert to the data server...
                #if we use client certs then honestly we dont really need the token at all
                #so we do need the token, but really only as a "we're ready for you" message
            #open up the firewall to give that ip address access to that port
            self.transport.write(token_message)
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
    

class dataServerProtocol(asyncio.Protocol):
    #first of all ignore all packets received on 
    #the port in question that have not passed auth
    def __init__(self):
        self.token_received = False
        self.tokenDict = defaultdict(set)

    def connection_made(self, transport):
        #check for session token
        peername = transport.get_extra_info('peername')
        print("connection from:",peername)
        try:
            self.expected_tokens = self.tokenDict[peername[0]]
            self.transport = transport
            self.pprefix = peername
            self.ip = peername[0]
            self.__receiving__ = False
            self.__block__ = b''
        except KeyError:
            transport.write(b'This is a courtesy message alerting you that your'
                            b' IP is not on the list of IPs authorized to make'
                            b' data connections. Query: How did you get through'
                            b' the firewall?')
            # probably should log this event
            transport.write_eof()
            print(peername,'This IP is not in the list (dict) of know ips. Terminated.')

    def data_received(self, data):
        #print(self.pprefix,data)
        print('current token dict',self.tokenDict)
        if not self.token_received:
            token_start = data.find(b'\x99')
            if token_start != -1:
                token_start += 1
                token = data[token_start:token_start+256]
                if token in self.expected_tokens:
                    self.token_received = token
        else:
            print(self.pprefix,[t for t in self.process_data(data)])
            self.transport.write(b'processed response\n')
        #try:
            #print(self.pprefix,'data tail:',data[-10])
        #except IndexError:
            #print(self.pprefix,'data received: %s'%data)
        #print([t for t in self.process_data(data)])
        #actually process the response

    def eof_received(self):
        self.tokenDict[self.ip].remove(self.token_received)
        print(self.pprefix,'got eof')

    def process_data(self,data):  # FIXME does this actually go here? or should it be in code that works directly on the transport object??!
        self.__splitStopPossible__ = False
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

    def update_token_data(self, ip, token):
        self.tokenDict[ip].add(token)  # could have multiple connections per ip
        print('token added',self.tokenDict)


def main():
    conContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None)
    dataContext = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)

    conServ = connectionServerProtocol()
    datServ = dataServerProtocol()
    conServ.register_data_server_token_setter(datServ.update_token_data)  # hat now eaten

    serverLoop = asyncio.get_event_loop()
    coro_conServer = serverLoop.create_server(lambda: conServ, '127.0.0.1', CONNECTION_PORT, ssl=None)  # TODO ssl
    coro_dataServer = serverLoop.create_server(lambda: datServ, '127.0.0.1', DATA_PORT, ssl=None)  # TODO ssl and this can be another box
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
