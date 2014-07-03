"""
    cProfile helper class that uses p.Before() and p.After('name')
    to delimit the code you want to profile
"""
import cProfile, pstats, io

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
def profile_me(function):
    def wrapped(*args,**kwargs):
        pr = cProfile.Profile()
        s = io.StringIO()
        pr.enable()
        function(*args,**kwargs)
        pr.disable()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()
        print(function.__name__,s.getvalue())
    wrapped.__name__ = function.__name__
    return wrapped

