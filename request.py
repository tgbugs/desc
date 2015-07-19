import hashlib
import pickle
import sys
import traceback
import zlib

from uuid import uuid4
import numpy as np

#from numpy import cumsum
from .util.ipython import embed
from .test_objects import makeSimpleGeom

#fix sys module reference
sys.modules['core'] = sys.modules['panda3d.core']

class Request:  # testing only since this will need to be in its own module to keep python happy
    """ the serializable object used for transporting the requested data
        (gleaned from UI input) and sending it to the server to retrieve
        this thing needs to have an injective mapping to the data
        
        fortunately all of the data used to generate the request is
        pulled from the datastore itself so that should simplifying things

        argh, since we probably shouldn't / can't dump whole collision trees
        to bam we *may* need to send the uuid data in the serialization of points
    """
    def __init__(self, request_type:'[raw (sql or something?), data view,'
                 ' type/knowledge view, any relationship view??]',
                 type_:'uuid', relationship:'currently active hierarchy'
                 '(set of hierarchies? dont think is possible)',
                 properties:'[0..n]', constraints:'a set of'
                 ' constraints on properties (cache/eager load the rest too so you change selectors locally '):
        #should properties be generated on the fly as an enum for the interface? no, they will bugger the hash
        self.request_type = request_type
        self.type_ = type_   #FIXME if the request type is for know then here we should expect a list... HRM
        self.relationship = relationship
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

        def __ne__(self, other):
            if type(self) != type(other):
                return True
            elif self.hash_ == other.hash_:  # TODO cache inval? goes here or elsewhere
                return False
                
        #def __hash__(self):
            #return self.hash_


class Response:
    def __init__(self, positions, geometry, colors, uuids, bounds, ui_data, makeBam = True):
        self.positions = positions
        self.geometry = geometry
        self.uuids = uuids
        self.bounds = bounds
        self.ui_data = ui_data  # this is where we are really going to need work
        if makeBam:
            self.bam = makeBam(positions, geometry, colors)
        else:
            self.bam = None





class requestProcessor:  # FIXME @classmethod?  #TODO multiple selected types??? yield only common properties?, TODO depth of childs, need to keep type level stuff in local memory/space so we can quickly rearrange based on the relationship selected :/
    def __init__(self, datastore):
        self.datastore = datastore
        self.request_types = {  # technically view types
            'new':self.newReq,
            'type':self.typeReq,
            'instance':self.instReq,
            'token':self.tokenReq,
        }

    def newReq(self, request):
        # return the default set of types to get everything off and running
        return None

    def typeReq(self, request):  # default request that boots everything up
        # return the scalar properties of the type
        # return the (scalar) properties of all instances >> ui
        # return the (scalar) properties of all tokens >> ui
        # return ALL children (under given hierarchy?) aka instances  # overlaying coordinate systems based on minimal quantitative data?

        # TODO if no properties requested: return some graph layout?
        # TODO in theory a type request could just be a name and we could go from there (have to start somewhere)
        objects = self.datastore[request.type_]

    def instReq(self, request):
        """ summary of direct subtypes """
        # return the positions of the subset of properties specified on the instances
        objects = self.datastore[request.type_].instances  # FIXME children of varying types

    def tokenReq(self, request):
        # return the positions of the subset of properties specified on the set of tokens in question
        objects = self.datastore[request.type_].tokens

    def processRequest(self, request):
        return self.request_types[request.type_](request)

def processRequest(request):
    """
        The code that processes the requests and returns the positions and UI elements
        the selected type/objects needs to persist when further manipulations are engaged
    """
    n = 9999
    positions = np.cumsum(np.random.randint(-1,2,(n,3)), axis=0)
    ui_data = b"GET OUT OF HERE STALKER"  # URG BYTES
    return positions, ui_data

class responseMaker:  # TODO we probably move this to its own file?
    npoints = 9999
    def __init__(self):
        #setup at connection to whatever database we are going to use
        pass

    def make_response(self, request):
        # TODO so encoding the collision nodes to a bam takes a REALLY LONG TIME
        # it seems like it might be more prudent to serialize to (x,y,z,radius) or maybe a type code?
        # yes, the size of the bam serialization is absolutely massive, easily 3x the size in memory
        # also if we send it already in tree form... so that the child node positions are just nested
        # it might be pretty quick to generate the collision nodes
        n = self.npoints
        np.random.seed()  # XXX MUST do this otherwise the same numbers pop out over and over, good case for cache invalidation though...

        positions, ui_data = processRequest(request)
        uuids = np.array(['%s'%uuid4() for _ in range(n)])
        bounds = np.ones(n) * .5
        example_coll = pickle.dumps((positions, uuids, bounds))  # FIXME putting pickles last can bollox the STOP
        #print('making example bam')
        example_bam = makeSimpleGeom(positions, np.random.rand(4)).__reduce__()[1][-1]  # the ONE way we can get this to work atm; GeomNode iirc; FIXME make sure -1 works every time  # FIXME FIXME FIXME __reduce__ causes an infinite hang
        #print('done making bam',example_bam)  # XXX if you want this use repr() ffs

        data_tuple = (example_bam, example_coll, ui_data)

        #code for testing threading and sending stuff
        #cnt = 9999999
        #if request.request_type is 'prediction':
            #data_tuple = [make_bytes(cnt) for _ in range(2)] + [b'THIS IS THE FIRST ONE']
        #else:
            #data_tuple = [make_bytes(cnt) for _ in range(2)] + [b'THIS IS THE SECOND ONE']

        return data_tuple

    def make_predictions(self, request):
        #TODO this is actually VERY easy, because all we need to do is use
            #the list of connected UI elements that we SEND OUT ANYWAY and
            #just prospectively load those models/views
        request = FAKE_PREDICT
        yield request  # XXX NOTE: yielding the request itself causes a second copy to be sent

###
#   Byte stream definitions
###

class RequestByteStream:
    #request stream
    #pickle codes
    OP_PICKLE = b'\x80'
    OP_PICKLE_INT = OP_PICKLE[0]
    PICKLE_STOP = b'.'

    @classmethod
    def makeRequestStream(cls, object_):
        """ Special dumps that adds a double stop to make deserializing easier """
        return pickle.dumps(object_)+b'.'

    @classmethod
    def decodePickleStreams(cls, split):  # FIXME this fails HARD if there is another \x80
        for bytes_ in split:
            pickleStart = 0
            if bytes_[pickleStart] != cls.OP_PICKLE_INT: #apparently indexing into bytes returns ints not bytes
                if cls.DEBUG:
                    print('what the heck kind of data is this!?')
                    print(bytes_)
                    print('')
                pickleStart = bytes_.find(cls.OP_PICKLE)
                if pickleStart == -1:
                    if cls.DEBUG:
                        print('What is this garbage? You have a stop but no start?!')
                    yield None
            try:
                thing = pickle.loads(bytes_[pickleStart:]+cls.PICKLE_STOP)  # have to add the stop back in
                if type(thing) is not Request:
                    yield None
                else:
                    yield thing
            except (ValueError, EOFError, pickle.UnpicklingError) as e:  # ValueError is for bad pickle protocol
                if cls.DEBUG:
                    print('What is this garbage?',bytes_[pickleStart:])
                    print('Error was',e)  # TODO log this? or if these are know... then don't sweat it
                yield None  # we cannot raise here because we won't evaluate the rest of the loop


class ResponseByteStream:
    """ Named struct for defining fields of serialized byte streams """

    #switch for local vs network behavior
    LOCAL = False

    #opcodes
    STOP = b'..'  #FIXME this doesn't work for opcodes :(
    OP_TOKEN = b'.\x99'

    OP_DATA = b'.\x98'

    #shared filed lengths
    LEN_OPCODE = 2

    #token stream
    LEN_TOKEN = 256

    #response data stream
    BYTEORDER = 'little'  # this is NOT readable as a number, need big for that
    LEN_HASH = 16
    LEN_CDATA = 4
    LEN_FIELDS = 1
    LEN_OFFSET = 4
    LEN_HEADER_FIXED = LEN_OPCODE + LEN_HASH + LEN_CDATA + LEN_FIELDS
    #FIELDS_TYPE = 'B'  # this gives an 8bit unsigned int
    #OFFSET_TYPE = 'I'  # this gives a 32bit unsigned int

    DEBUG = False

    @classmethod
    def makeTokenStream(cls, token):
        if len(token) != cls.LEN_TOKEN:
            raise ValueError('Wrong token length! You have %s you need %s'%(len(token), cls.LEN_TOKEN))
        return cls.OP_TOKEN + token  # no stop needed here

    @classmethod
    def makeRequestStream(cls, request):  # TODO should pickle here too? since this doesn't take request_data
        return request + cls.STOP  # FIXME

    @classmethod
    def makeResponseStream(cls, request_hash, data_tuple):
        # headers have fixed length so no opcode is needed between the header and the first data block
        n_fields = int.to_bytes(len(data_tuple) - 1, cls.LEN_FIELDS, cls.BYTEORDER)  # this is actually N offsets.... fix?

        cumsum = 0
        offsets = b''
        for d in data_tuple[:-1]:
            cumsum+=len(d)
            offsets+=int.to_bytes(cumsum, cls.LEN_OFFSET, cls.BYTEORDER)

        if cls.LOCAL:
            data = b''.join(data_tuple)
        else:
            data = zlib.compress(b''.join(data_tuple))

        data_size = int.to_bytes(len(data), cls.LEN_CDATA, cls.BYTEORDER)

        if cls.DEBUG:
            print('length data',len(data))
            print("response stream is being made")
            print('compressed data tail',data[-100:])


        data_stream = cls.OP_DATA + request_hash + data_size + n_fields + offsets + data
        
        #linewidth = 30
        #block = ''.join([hex(c)[2:].ljust(3) for c in data_stream])
        #block = block.replace('0x',' ')
        #lims = zip(range(0,len(block)-linewidth,linewidth),range(linewidth,len(block),linewidth))
        #lines = '\n'.join([block[start:stop] for start,stop in lims])
        #with open('badbam', 'wt') as f:
            #f.write(''.join([str(i).ljust(3) for i in range(10)])+'\n')
            #f.write(lines)
            #f.write('\n\n')

        return data_stream

    @classmethod
    def decodeToken(cls, stream):
        start = stream.find(cls.OP_TOKEN)
        if start != -1:
            start += cls.LEN_OPCODE
            try:
                return stream[start:start + cls.LEN_TOKEN], start+cls.LEN_TOKEN
            except IndexError:
                raise IndexError('This token is not long enough!')

    @classmethod
    def decodeResponseHeader(cls, bytes_):
        headerStart = 0
        if bytes_[headerStart:headerStart + cls.LEN_OPCODE] != cls.OP_DATA:
            headerStart = bytes_.find(cls.OP_DATA)

        if len(bytes_[headerStart:]) < cls.LEN_HEADER_FIXED:
            return None

        dataSizeStart = headerStart + cls.LEN_OPCODE + cls.LEN_HASH
        fieldStart = dataSizeStart + cls.LEN_CDATA

        n_fields = int.from_bytes(bytes_[fieldStart:fieldStart + cls.LEN_FIELDS], cls.BYTEORDER)
        data_size = int.from_bytes(bytes_[dataSizeStart:dataSizeStart + cls.LEN_CDATA], cls.BYTEORDER)
        offLen = n_fields * cls.LEN_OFFSET 

        total_size = fieldStart + cls.LEN_FIELDS + offLen + data_size

        return total_size, (offLen, data_size)

    @classmethod
    def decodeResponseStream(cls, bytes_, offLen, data_size):
        hashStart = -data_size - offLen - cls.LEN_HEADER_FIXED + cls.LEN_OPCODE
        request_hash = bytes_[hashStart:hashStart + cls.LEN_HASH]


        offblock = bytes_[-data_size - offLen:-data_size]
        if cls.DEBUG:
            print('header',bytes_[:-data_size])
            print('compressed data length', len(bytes_[-data_size:]))
        if cls.LOCAL:
            data = bytes_[-data_size:]  # this is gurantted to end because of the code in data_received XXX
        else:
            data = zlib.decompress(bytes_[-data_size:])  # this is gurantted to end because of the code in data_received XXX


        offsets = [0] + [
            int.from_bytes(offblock[i:i + cls.LEN_OFFSET], cls.BYTEORDER)
            for i in range(0, offLen, cls.LEN_OFFSET)] + [None]

        offslice = zip(offsets[:-1],offsets[1:])
        data_tuple = tuple([ data[start:stop] for start, stop in offslice ])
        #data_tuple = tuple([ data[offsets[i] : offsets[i + 1]] for i in range(n_fields + 1) ])  # check perf?
        return request_hash, data_tuple

    @classmethod
    def decodeResponseStreams(cls, split):  # XXX deprecated
        for bytes_ in split:
            dataStart = 0
            if bytes_[dataStart:dataStart + cls.LEN_OPCODE] != cls.OP_DATA:
                dataStart = bytes_.find(cls.OP_DATA)
                if dataStart is -1:
                    yield None, None
            
            hashStart = dataStart + cls.LEN_OPCODE
            fieldStart = hashStart + cls.LEN_HASH
            dsStart = fieldStart + cls.LEN_CDATA
            offStart = dsStart + cls.LEN_FIELDS

            request_hash = bytes_[hashStart:hashStart + cls.LEN_HASH]
            data_size = bytes_[dsStart:dsStart + cls.LEN_CDATA]
            n_fields = int.from_bytes(bytes_[fieldStart:fieldStart + cls.LEN_FIELDS], cls.BYTEORDER)

            offLen = cls.LEN_OFFSET * n_fields
            compressStart = offStart + offLen
            if cls.DEBUG:
                print('header',bytes_[:compressStart])

            offblock = bytes_[offStart:offStart + offLen]
            data = zlib.decompress(bytes_[compressStart:])

            offsets = [0] + \
                list(cumsum([int.from_bytes(offblock[cls.LEN_OFFSET * i :
                                                     cls.LEN_OFFSET * (i + 1)],
                                            cls.BYTEORDER)
                            for i in range(n_fields)])) + [None]

            offslice = zip(offsets[:-1],offsets[1:])
            data_tuple = tuple([ data[start:stop] for start, stop in offslice ])
            #data_tuple = tuple([ data[offsets[i] : offsets[i + 1]] for i in range(n_fields + 1) ])  # check perf?
            yield request_hash, data_tuple


FAKE_REQUEST = Request('test.','test','default',(1,2,3),None)
FAKE_PREDICT = Request('prediction','who knows','default',(2,3,4),None)
RAND_REQUEST = lambda: Request('random','%s'%uuid4(),'default',(0,0,0),None)

def main():
    from enum import Enum
    from .util.ipython import embed

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
