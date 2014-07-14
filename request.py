import hashlib

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
