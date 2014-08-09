import inspect
from collections import defaultdict
from functools import wraps

from direct.showbase.DirectObject import DirectObject

from ipython import embed

callbacks = defaultdict(dict)
callbacks['TO BIND']
callbacks['default']  # needs to exist before making it the default factory
callbacks.default_factory = lambda: {k:v for k,v in callbacks['default'].items()}

# FIXME need a way to pass in self...

class KeybindObject(DirectObject):
    def __new__(cls, *args, **kwargs):  # replace functions with methods
        def __init__(self, *args, **kwargs):
            print('Yes this gets called')
            embed()
            for name in self.__dir__():  # FIXME there must be a better way...
                method = getattr(self, name)
                if hasattr(method,'__event_callbacks__'):
                    for mode_dict, keyname in method.__event_callbacks__:
                        print(mode_dict, keyname, mode_dict[keyname], method)
                        mode_dict[keyname] = method
            cls._init_(self, *args,**kwargs)

        cls._init_ = cls.__init__
        cls.__init__ = __init__
        self = super().__new__(cls)
        return self


def event_callback(keybind, modes = ('default',)):  # something something changing the bind between modes a bad idea, accept a dict for
    """
        decorator that acceps:
        direct use -> register the function but no keys
        default event name string -> single key bind in default (and all if not overridden) modes
        den string, mode tuple -> single key bind across these modes
        den string mode dict -> key, mode pairs to set bind for each mode
    """
    if type(keybind) is dict:
        print(type(keybind))
        modes = keybind

    def register_callback(func):
        """ wrapper the collects all possible keyboard/mouse callbacks """
        indexes = func.__event_callbacks__ = []
        for mode in modes:
            if mode not in callbacks:  # FIXME dangerous possible for bad names to get in
                raise NameError('There is no mode with that name')
            if keybind is func:
                callbacks['TO BIND'][func.__qualname__] = func
                indexes.append((callbacks['TO BIND'], func.__qualname__))
            else:
                callbacks[mode][keybind] = func  # FIXME namespace collisions
                indexes.append((callbacks[mode], keybind))
        return func

    if inspect.isfunction(keybind):
        return register_callback(keybind)
    else:
        return register_callback

# panda3d event names
rel = '-up'  # release

key_events = [
]

mouse_events = [
    'mouse1',
    'mouse2',  # middle mouse
    'mouse3',
    'mouse4',
    'mouse5',
    'wheel_up',
    'wheel_down',
]

key_modifiers = [
    'alt-',
    'shift-',
    'control-',
]

class AcceptKeys(DirectObject):
    def __init__(self):
        for name, mode in callbacks.items():
            if name != 'TO BIND':
                self.set_mode(mode)

    def set_mode(self, mode):
        for event_name, function in mode.items():
            self.add_pair(event_name, function)

    def add_pair(self, event_name, function):  # actually, the way this works the default dict trick isn't even needed, but cool nonetheless
        self.accept(event_name, function)

