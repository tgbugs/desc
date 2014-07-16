import unittest

from server import connectionServerProtocol

class testServer(unittest.TestCase):
    server = connectionServerProtocol()
    test_bytes = [
            b'\x80.',
            b'\x80..',
            b'\x80\x03.',
            b'\x80\x03..',
            b'\x80\x03C\x00q\x00.',  # b''
            b'\x80\x03C\x00q\x00..',
            b'\x80\x03C\x00q\x00.\x80\x03C\x00q\x00..',
            b'\x80\x03C\x00q\x00..\x80\x03C\x00q\x00..',
            b'\x80\x03C\x00q\x00...\x80\x03C\x00q\x00..',
            b'',
            b'\x80\x03C\x00q\x00.',  # these two combine for testing the split stop
            b'.\x80\x03C\x00q\x00..',
            b'as;dlfkja;lsdkjfa;lskdfj',
            b'.........................',
            b'\x80...................',
            b'asdfasdfasdfasdfasdf..',
            b'\x80.\x80.\x80..',
            b'\x80\x03C\x0bhello worldq\x00.',
            b'\x80\x03C\x0b',  # split the stream across lines, caught this one by hand
            b'hello worldq\x00.',
            b'',
            b'',
        ]
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_connection_made(self):
        pass
    def test_data_received(self):
        pass
    def test_process_data(self):
        for b in self.test_bytes:
            assert [result for result in self.server.process_data(b)]

if __name__ == "__main__":
    unittest.main()
