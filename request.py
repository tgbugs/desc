import hashlib
import pickle
import sys
import traceback
import struct

from numpy import cumsum
from IPython import embed

class Request:  # testing only since this will need to be in its own module to keep python happy
    """ the serializable object used for transporting the requested data
        (gleaned from UI input) and sending it to the server to retrieve
        this thing needs to have an injective mapping to the data
        
        fortunately all of the data used to generate the request is
        pulled from the datastore itself so that should simplifying things

        argh, since we probably shouldn't / can't dump whole collision trees
        to bam we *may* need to send the uuid data in the serialization of points
    """
    def __init__(self,request_type:'[raw (sql or something?), data view,'
                 ' type/knowledge view, any relationship view??]',
                 type_:'uuid', properties:'[0..n]', constraints:'a set of'
                 ' constraints on properties (cache/eager load the rest too so you change selectors locally '):
        #should properties be generated on the fly as an enum for the interface? no, they will bugger the hash
        self.request_type = request_type
        self.type_ = type_   #FIXME if the request type is for know then here we should expect a list... HRM
        self.properties = properties
        pbytes = ''.join(['{}'.format(p) for p in properties])
        md5 = hashlib.md5()
        md5.update((request_type+type_+pbytes).encode())
        self.hash_ = md5.digest()
        def __eq__(self, other):
            if type(self) != type(other):
                return False
            elif self.hash_ == other.hash_:  # TODO cache inval? goes here or elsewhere
                return True
                
        #def __hash__(self):
            #return self.hash_

class DataByteStream:
    """ Named struct for defining fields of serialized byte streams """

    #opcodes
    STOP = b'..'
    OP_TOKEN = b'.\x99'

    OP_DATA = b'.\x98'

    #shared filed lengths
    OPCODE_LEN = 2

    #token stream
    TOKEN_LEN = 256

    #request stream
    #pickle codes
    OP_PICKLE = b'\x80'
    OP_PICKLE_INT = OP_PICKLE[0]
    PICKLE_STOP = b'.'

    #request response data stream
    HASH_LEN = 16
    FIELDS_LEN = 1
    OFFSET_LEN = 4
    FIELDS_TYPE = 'B'  # this gives an 8bit unsigned int
    OFFSET_TYPE = 'I'  # this gives a 32bit unsigned int

    @classmethod
    def makeTokenStream(cls, token):
        if len(token) != cls.TOKEN_LEN:
            raise ValueError('Wrong token length! You have %s you need %s'%(len(token), cls.TOKEN_LEN))
        return cls.OP_TOKEN + token  # no stop needed here

    @classmethod
    def makeRequestStream(cls, request):  # TODO should pickle here too? since this doesn't take request_data
        return request + cls.STOP  # FIXME

    @classmethod
    def makeResponseStream(cls, request_hash, data_tuple):
        # headers have fixed length so no opcode is needed between the header and the first data block
        n_fields = struct.pack(cls.FIELDS_TYPE, len(data_tuple) - 1)  # this is actually N offsets.... fix?
        offsets = b''.join([struct.pack(cls.OFFSET_TYPE, len(data)) for data in data_tuple[:-1]])
        data = zlib.compress(b''.join(data_tuple))

        print("response stream is being made")

        return cls.OP_DATA + request_hash + n_fields + offsets + data + cls.STOP

    @classmethod
    def decodeToken(cls, stream):
        start = stream.find(cls.OP_TOKEN)
        if start != -1:
            start += cls.OPCODE_LEN
            try:
                return stream[start:start + cls.TOKEN_LEN]
            except IndexError:
                raise IndexError('This token is not long enough!')

    @classmethod
    def decodePickleStreams(cls, split):
        for bytes_ in split:
            pickleStart = 0
            if bytes_[pickleStart] != cls.OP_PICKLE_INT: #apparently indexing into bytes returns ints not bytes
                print('what the heck kind of data is this!?')
                print(bytes_)
                print('')
                pickleStart = bytes_.find(cls.OP_PICKLE)
                if pickleStart == -1:
                    print('What is this garbage? You have a stop but no start?!')
                    yield None
            try:
                thing = pickle.loads(bytes_[pickleStart:]+cls.PICKLE_STOP)  # have to add the stop back in
                if type(thing) is not Request:
                    yield None
                else:
                    yield thing
            except (ValueError, EOFError, pickle.UnpicklingError) as e:  # ValueError is for bad pickle protocol
                print('What is this garbage?',bytes_)
                print('Error was',e)  # TODO log this? or if these are know... then don't sweat it
                yield None  # we cannot raise here because we won't evaluate the rest of the loop

    @classmethod
    def decodeResponseStreams(cls, split):
        for bytes_ in split:
            dataStart = 0
            if bytes_[dataStart:dataStart + cls.OPCODE_LEN] != cls.OP_DATA:
                dataStart = bytes_.find(cls.OP_DATA)
                if dataStart is -1:
                    yield None, None
            
            hashStart = dataStart + cls.OPCODE_LEN
            fieldStart = hashStart + cls.HASH_LEN
            offStart = fieldStart + cls.FILEDS_LEN

            request_hash = bytes_[hashStart:hashStart + cls.HASH_LEN]
            n_fileds = bytes_[fieldStart:fieldStart + cls.FIELDS_LEN]  # FIXME if it is a single byte it will decode automatically

            offLen = cls.OFFSET_LEN * n_fields
            compressStart = offStart + offLen

            offblock = bytes_[offStart:offStart + offLen]
            data = zlib.decompress(bytes_[compressStart:])

            offsets = [0] + \
                list(cumsum([struct.unpack(cls.OFFSET_TYPE,
                    offblock[cls.OFFSET_LEN * i : cls.OFFSET_LEN * (i + 1)])
                            for b in range(n_fields)])) + [None]

            offslice = zip(offsets[:-1],offsets[1:])
            data_tuple = tuple([ data[start:stop] for start, stop in offslice ])
            #data_tuple = tuple([ data[offsets[i] : offsets[i + 1]] for i in range(n_fields + 1) ])  # check perf?
            yield request_hash, data_tuple



def main():
    from enum import Enum
    from IPython import embed

    class REQUEST_TYPES(Enum):
        # for some reason I think we really do not want to hard code this since request types seem likely to ... grow?
        # actually the function API seems pretty cool...
        Data = 0
        Type = 1
        Rel = 2
        Cookies = 3

    print([hash(t) for t in REQUEST_TYPES])  # hash is not consistent across sessions, to be fair that is probably correct given the definition of hash
    print([hash(t) for t in range(4)])

    

if __name__ == '__main__':
    main()
