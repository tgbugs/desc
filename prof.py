"""
    cProfile helper class that uses p.Before() and p.After('name')
    to delimit the code you want to profile
"""
import cProfile, pstats, io
from functools import wraps, partial

class Prof:
    def __init__(self,sortby = 'cumulative'):
        self.sortby = sortby

    def Before(self):
        self.pr = cProfile.Profile()
        self.s = io.StringIO()
        self.pr.enable()

    def After(self,name='WHO KNOWS!'):
        self.pr.disable()
        ps = pstats.Stats(self.pr, stream=self.s).sort_stats(self.sortby)
        ps.print_stats()
        print(name,self.s.getvalue())

#decorator to do this

def doublewrap(decorator_function):
    @wraps(decorator_function)
    def new_dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return decorator_function(args[0])
        else:
            def actual_decorator(function):
                return decorator_function(function, *args, **kwargs)
            return actual_decorator

    return new_dec

@doublewrap
def profile_me(function, sort='tottime'):
    @wraps(function)
    def wrapped(*args, **kwargs):
        if not globals()['profile_me_already_run'+function.__qualname__]:
            globals()['profile_me_already_run'+function.__qualname__] = True
            pr = cProfile.Profile()
            s = io.StringIO()
            pr.enable()
            out = function(*args, **kwargs)
            globals()['profile_me_already_run'+function.__qualname__] = False  # recursion complete
            pr.disable()
            ps = pstats.Stats(pr, stream=s).sort_stats(sort)
            ps.print_stats()
            print(function.__name__,s.getvalue())
            return out
        else:
            return function(*args, **kwargs)

    globals()['profile_me_already_run'+function.__qualname__] = False  # this fails hard with asnycio heh
    return wrapped

