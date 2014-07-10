import asyncio
import pickle

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

class connectionServerProtocol(asyncio.Protocol):
    """ Define the protocol for handling basic connections
        should spin up client specific connections?
    """
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        #print('connection from: %s'%peername)
        print("connection from:",peername)
        self.transport = transport
        self.__receiving__ = False
        self.__block__ = b''

    def data_received(self, data):  # data is a bytes object
        try:
            print('data tail:',data[-10])
        except IndexError:
            print('data received: %s'%data)
        print([t for t in self.process_data(data)])
        #actually process the response
        self.transport.write(b'processed response')

    def process_data(self,data):
        #are we already receiving a stream?
            #new stream
                #what type of stream is it?
                #if the stream sends fixed sized requests just wait for bytes
            #existing stream
                #are we there yet?
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

        if pickleStop is None:  # this is confusing, -1 only occurs if we are receiving
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
                raise BaseException(block)
            self.__block__ = b''
            yield thing
            rest = data[pickleStop:]
            self.__receiving__ = False  # dont know if need this here, but just incase
            if len(rest) > 1:
                yield from self.process_data(rest[1:])  # FIXME this can triggers recursion error on too many ..
            self.__receiving__ = False

                ##look for pickle end
            #else:
                #pass
                #look for newline or rather, just ignore it

    #def dispatch_block(self):
        #processBlock(self.transport,self.__block__)  # this should probably yield a future or something to keep it async

    def eof_received(self):
        #clean up the connection and store stuff because the client has exited
        print('got eof')
        pass
    

def main():
    serverLoop = asyncio.get_event_loop()
    coro_conServer = serverLoop.create_server(connectionServerProtocol, '127.0.0.1', 55555, ssl=None)  # TODO ssl
    server = serverLoop.run_until_complete(coro_conServer)
    try:
        serverLoop.run_forever()
    except KeyboardInterrupt:
        print('exiting...')
    finally:
        server.close()
        serverLoop.close()



if __name__ == "__main__":
    main()
