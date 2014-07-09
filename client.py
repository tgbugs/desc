import asyncio

class newConnectionProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        self.transport.write(b'hello there')
    def data_received(self, data):
        print("We should not be receiving data!")

def main():
    clientLoop = asyncio.get_event_loop()
    coro_conClient = clientLoop.create_connection(newConnectionProtocol, '127.0.0.1', 55555, ssl=None)  # TODO ssl
    clientLoop.run_until_complete(coro_conClient)
    try:
        clientLoop.run_forever()
    except KeyboardInterrupt:
        print('exiting...')
    finally:
        clientLoop.close()

if __name__ == "__main__":
    main()
        
