import asyncio
import random
import pickle
from time import sleep
from IPython import embed
from numpy.random import rand

def dumps(object):
    """ Special dumps that adds a double stop to make deserializing easier """
    return pickle.dumps(object)+b'.'

class newConnectionProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        transport.write(b'hello there')
        self.transport = transport
    def data_received(self, data):
        """ receive bam files that come back on request
            we can tag them with a request id if needs be
            this way we can also just start sending bam files
            as soon as the connection has been created if they
            arent cached
        """
        print("received",data)
    
    def connection_lost(self, exc):
        print('connection lost')
        asyncio.get_event_loop().close()


def main():
    clientLoop = asyncio.get_event_loop()
    coro_conClient = clientLoop.create_connection(newConnectionProtocol, '127.0.0.1', 55555, ssl=None)  # TODO ssl
    #embed()
    #transport, protocol = yield from clientLoop.create_connection(newConnectionProtocol, '127.0.0.1', 55555, ssl=None)  # TODO ssl
    #reader, writer = yield from asyncio.open_connection('127.0.0.1', 55555, loop=clientLoop, ssl=None)
    transport, protocol = clientLoop.run_until_complete(coro_conClient)
    transport.write(b'testing?')
    #writer.write('does this work?')
    for i in range(10):
        sleep(1E-4)  # FIXME around 1E-4 we switch from a single data stream to multiple streams...
        # clearly we should expect any data sent to act as a single stream (obviously given the doccumentation
        transport.write("testing post {} ?".format(i).encode())

    transport.write(dumps([random.random() for _ in range(100)]))
    transport.write(dumps([random.random() for _ in range(100)]))
    transport.write(dumps([random.random() for _ in range(100)]))
    transport.write(dumps([random.random() for _ in range(100)]))
    sleep(.001)
    transport.write(dumps('numpy?!'))
    sleep(.001)
    transport.write(dumps(rand(100)))
    transport.write(dumps(rand(100)))

    embed()  # if this is anything like calling run() .... this will work nicely
    #try:
        # TODO how to send in new writes??? yield or something?
        #clientLoop.run_forever()
    #except KeyboardInterrupt:
        #print('exiting...')
    #finally:
        #clientLoop.close()
    clientLoop.close()

if __name__ == "__main__":
    main()
        
