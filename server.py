import asyncio

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

    def data_received(self, data):  # data is a bytes object
        print('data received: %s'%data)

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
