import asyncio
import random
import pickle
import ssl
from time import sleep
from IPython import embed
from numpy.random import rand
from defaults import CONNECTION_PORT, DATA_PORT


def dumps(object):
    """ Special dumps that adds a double stop to make deserializing easier """
    return pickle.dumps(object)+b'.'

def run_for_time(loop,time):
    """ use this to view responses inside embed """
    loop.run_until_complete(asyncio.sleep(time))


class dataProtocol(asyncio.Protocol):
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
        self.data_callback(data)
    
    def connection_lost(self, exc):
        print('connection lost')
        asyncio.get_event_loop().close()

    def set_data_callback(self,callback_function):
        self.data_callback = callback_function
"""
authBytesPerBlock = 512
authOpCodes = {
    b'\x99\x99':'',
    b'\x98\x98':'',
    b'\x97\x97':'',
}
"""


class newConnectionProtocol(asyncio.Protocol):
    """ this is going to be done with fixed byte sizes known small headers """
    def connection_made(self, transport):
        self.transport = transport
        self.transport.write(b'I promis I real client, plz dataz')
        #send public key (ie the account we are looking for) #their password should unlock a local key which 

    def data_received(self, data):
        done = False
        if done:
            self.write_eof()
        
    def connection_lost(self, exc):
        pass

def main():
    conContext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cadata=None)  # TODO cadata should allow ONLY our self signed, severly annoying to develop...
    dataContext = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)

    clientLoop = asyncio.get_event_loop()
    coro_conClient = clientLoop.create_connection(newConnectionProtocol, '127.0.0.1', CONNECTION_PORT, ssl=None)  # TODO ssl
    coro_dataClient = clientLoop.create_connection(dataProtocol, '127.0.0.1', DATA_PORT, ssl=None)  # TODO ssl
    #embed()
    #transport, protocol = yield from clientLoop.create_connection(newConnectionProtocol, '127.0.0.1', 55555, ssl=None)  # TODO ssl
    #reader, writer = yield from asyncio.open_connection('127.0.0.1', 55555, loop=clientLoop, ssl=None)

    #transport, protocol = clientLoop.run_until_complete(coro_conClient)

    #TODO ONE way to make this synchronous so to add a coroutine that only completes when it gets a response
        #and then call run_until_complete on it :)
    test = []
    def myfunc(data):
        test.append(data)


    transport, protocol = clientLoop.run_until_complete(coro_dataClient)
    protocol.set_data_callback(myfunc)
    transport.write(b'testing?')
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
    #sleep(.001)
    transport.write(dumps('numpy?!'))
    #sleep(.001)
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
    #clientLoop.close()

#def main():
    #print("WHAT IS GOING ON HERE")

if __name__ == "__main__":
    main()
    print('ok')
