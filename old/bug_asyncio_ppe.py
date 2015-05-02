import sys
import asyncio
from threading import Thread
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Pipe

from direct.showbase.DirectObject import DirectObject

def startup():
    return "started"

def broken(*args):
    print('This should print every time.')
    print(args)
    #for a in args:
        #print(a)

class thing(DirectObject):
    def __init__(self, event_loop, ppe):
        self.event_loop = event_loop
        self.ppe = ppe
        self.accept('d', self.do_thing)
        self.accept('escape',self.exit)

    def do_thing(self):
        # I think the error I get happens when ppe is started
        # in a callback that has been initiated from a Protocol?
        pass

    def _do_thing(self):
        def do():
            for i in range(3):
                print('submitting %s'%i)
                self.event_loop.run_in_executor(self.ppe, broken, "%s"%i)

        thread = Thread(target=do)
        thread.start()

    def _do_thing(self):
        def do(task):
            for i in range(3):
                print('submitting %s'%i)
                self.event_loop.run_in_executor(self.ppe, broken, "%s"%i)
            taskMgr.remove(task.getName())
            return task.cont

        taskMgr.add(do,'do_task')


    def exit(self):
        self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        sys.exit()


def main():
    from direct.showbase.ShowBase import ShowBase

    base = ShowBase()

    event_loop = asyncio.get_event_loop() 
    ppe = ProcessPoolExecutor()
    t = thing(event_loop, ppe)

    asyncThread = Thread(target=event_loop.run_forever)
    asyncThread.start()

    base.run()
    # there may be a locking error where ppe trys to create
    # multiple queue managment threads at the same time
    # but I get the error even when rie is called a single time


if __name__ == '__main__':
    main()
