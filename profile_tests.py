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



def main():
    loops = 10
    in_keys(loops)
    index_into(loops)
    

if __name__ == '__main__':
    main()
