import hashlib
import pickle
import sys
import traceback
import zlib

#from numpy import cumsum
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
    STOP = b'..'  #FIXME this doesn't work for opcodes :(
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
    BYTEORDER = 'little'  # this is NOT readable as a number, need big for that
    HASH_LEN = 16
    CDATA_LEN = 4
    FIELDS_LEN = 1
    OFFSET_LEN = 4
    HEADER_FIXED_LEN = OPCODE_LEN + HASH_LEN + CDATA_LEN + FIELDS_LEN
    #FIELDS_TYPE = 'B'  # this gives an 8bit unsigned int
    #OFFSET_TYPE = 'I'  # this gives a 32bit unsigned int

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
        n_fields = int.to_bytes(len(data_tuple) - 1, cls.FIELDS_LEN, cls.BYTEORDER)  # this is actually N offsets.... fix?

        cumsum = 0
        offsets = b''
        for d in data_tuple[:-1]:
            cumsum+=len(d)
            offsets+=int.to_bytes(cumsum, cls.OFFSET_LEN, cls.BYTEORDER)

        data = zlib.compress(b''.join(data_tuple))
        data_size = int.to_bytes(len(data), cls.CDATA_LEN, cls.BYTEORDER)

        print("response stream is being made")

        data_stream = cls.OP_DATA + request_hash + data_size + n_fields + offsets + data
        
        linewidth = 30
        block = ''.join([hex(c)[2:].ljust(3) for c in data_stream])
        #block = block.replace('0x',' ')
        lims = zip(range(0,len(block)-linewidth,linewidth),range(linewidth,len(block),linewidth))
        lines = '\n'.join([block[start:stop] for start,stop in lims])
        with open('badbam', 'wt') as f:
            f.write(''.join([str(i).ljust(3) for i in range(10)])+'\n')
            f.write(lines)
            f.write('\n\n')

        return data_stream

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
    def decodeReponseHeader(cls, bytes_):
        headerStart = 0
        if bytes_[headerStart:headerStart + cls.OPCODE_LEN] != cls.OP_DATA:
            headerStart = bytes_.find(cls.OP_DATA)

        if len(bytes_[headerStart:]) < cls.HEADER_FIXED_LEN:
            return None

        dataSizeStart = headerStart + cls.OPCODE_LEN + cls.HASH_LEN
        fieldStart = dataSizeStart + cls.CDATA_LEN

        n_fields = int.from_bytes(bytes_[fieldStart:fieldStart + cls.FIELDS_LEN], cls.BYTEORDER)
        data_size = int.from_bytes(bytes_[dsStart:dsStart + cls.CDATA_LEN], cls.BYTEORDER)
        offLen = n_fields * cls.OFFSET_LEN 

        total_size = fieldStart + cls.FIELDS_LEN + offLen + data_size

        return total_size, (offLen, data_size)


    @classmethod
    def decodeResponseStream(cls, bytes_, offLen, data_size):
        hashStart = -data_size - off_len - cls.HEADER_FIXEX_LEN + cls.OPCODE_LEN
        request_hash = bytes_[hashStart:hashStart + cls.HASH_LEN]

        print('header',bytes_[:-data_size])

        offblock = bytes_[-data_size - offLen:-data_size]
        data = zlib.decompress(bytes_[-data_size:])  # this is gurantted to end because of the code in data_received XXX

        offsets = [0] + [
            int.from_bytes(offblock[i:i + cls.OFFSET_LEN], cls.BYTEORDER)
            for i in range(0, offLen, cls.OFFSET_LEN)] + [None]

        offslice = zip(offsets[:-1],offsets[1:])
        data_tuple = tuple([ data[start:stop] for start, stop in offslice ])
        #data_tuple = tuple([ data[offsets[i] : offsets[i + 1]] for i in range(n_fields + 1) ])  # check perf?
        return request_hash, data_tuple



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
            dsStart = fieldStart + cls.CDATA_LEN
            offStart = dsStart + cls.FIELDS_LEN

            request_hash = bytes_[hashStart:hashStart + cls.HASH_LEN]
            data_size = bytes_[dsStart:dsStart + cls.CDATA_LEN]
            n_fields = int.from_bytes(bytes_[fieldStart:fieldStart + cls.FIELDS_LEN], cls.BYTEORDER)

            offLen = cls.OFFSET_LEN * n_fields
            compressStart = offStart + offLen
            print('header',bytes_[:compressStart])

            offblock = bytes_[offStart:offStart + offLen]
            data = zlib.decompress(bytes_[compressStart:])

            offsets = [0] + \
                list(cumsum([int.from_bytes(offblock[cls.OFFSET_LEN * i :
                                                     cls.OFFSET_LEN * (i + 1)],
                                            cls.BYTEORDER)
                            for i in range(n_fields)])) + [None]

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
