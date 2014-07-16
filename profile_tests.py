from prof import profile_me
from numpy.random import bytes as make_bytes
from numpy.random import rand


test_bytes = make_bytes(20000)
keys = [hash(i) for i in rand(99999)]
bad_keys = [hash(i) for i in rand(99999)]
test_dict = {key:test_bytes for key in keys}

@profile_me
def in_keys(loops):  # this one actually seems faster!
    for _ in range(loops):
        for key in keys+bad_keys:
            try:
                a = test_dict[key]
                out = True
            except KeyError:
                out = False


@profile_me
def index_into(loops):
    for _ in range(loops):
        for key in keys+bad_keys:
            if key in test_dict.keys():
                out = True
            else:
                out = False

test_bytes = b'..'.join([make_bytes(9999) for _ in range(100)])


@profile_me
def split_t(loops):
    for _ in range(loops):
        out = test_bytes.split(b'..')


def fslice(b): # HOLY SLOW BATMAN
    index = b.find(b'..')
    if index != -1:
        try:
            #return [b[:index]]+[fslice(b[index+2:])]
            #return [index + offset] + fslice(b[index+2:],index+2)
            return fslice(b[index+2:])
        except IndexError:
            #return [index + offset]
            return
    else:
        #return []
        return

@profile_me
def find_slice_t(loops):
    for _ in range(loops):
        out = fslice(test_bytes)



def main():
    #loops = 10
    #in_keys(loops)
    #index_into(loops)

    loops = 99
    find_slice_t(loops)
    split_t(loops)
    

if __name__ == '__main__':
    main()
