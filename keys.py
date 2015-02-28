import inspect
from collections import defaultdict
from functools import wraps

from direct.showbase.DirectObject import DirectObject

from .ipython import embed

# TODO we will need a good way to replace the default keybinds with ones from a config, probably based on qualname
    # possibly we can store the default binds and the just fill in overwritten binds and just always use qualname in the decorator

callbacks = defaultdict(dict)
callbacks['TO BIND']
callbacks['default']  # needs to exist before making it the default factory
callbacks.default_factory = lambda: {k:v for k,v in callbacks['default'].items()}

class HasKeybinds:  # FIXME should this inherit from direct object?? I don't think so...
    """ a mixin that is requred when using the event_callback
        decorator, it automatically populates the callbacks with methods at init
    """
    def __new__(cls, *args, **kwargs):
        def __init__(self, *args, **kwargs):
            for name in self.__dir__():
                method = getattr(self, name)
                if hasattr(method,'__event_callbacks__'):
                    for mode_dict, keyname in method.__event_callbacks__:
                        mode_dict[keyname] = method
            cls._init_(self, *args,**kwargs)
            cls.__init__ = cls._init_  # this way __new__ keeps working

        cls._init_ = cls.__init__
        cls.__init__ = __init__
        self = super().__new__(cls)
        return self


def event_callback(keybinds, modes = ('default',)):  # something something changing the bind between modes a bad idea, accept a dict for
    """
        decorator that acceps:
        direct use -> register the function but no keys
        default event name string -> single key bind in default (and all if not overridden) modes
        den string, mode tuple -> single key bind across these modes
        den string mode dict -> key, mode pairs to set bind for each mode
    """
    #print(type(keybinds) is not tuple)
    if inspect.isfunction(keybinds):
        pass

    elif type(keybinds) is dict:
        modes = keybinds

    elif type(keybinds) is not tuple:
        # TODO need a way to bind multiple event names to the same callback!
        # double decorator?
        keybinds = (keybinds,)

    def register_callback(func):
        """ wrapper the collects all possible keyboard/mouse callbacks """
        indexes = func.__event_callbacks__ = []
        for mode in modes:
            if mode not in callbacks:  # FIXME dangerous possible for bad names to get in
                raise NameError('There is no mode with that name')
            if keybinds is func:
                callbacks['TO BIND'][func.__qualname__] = func
                indexes.append((callbacks['TO BIND'], func.__qualname__))
            else:
                for keybind in keybinds:
                    callbacks[mode][keybind] = func  # FIXME namespace collisions and failed calls
                    indexes.append((callbacks[mode], keybind))
        return func

    if inspect.isfunction(keybinds):
        return register_callback(keybinds)
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
                # TODO make sure we can actually call it, otherwise don't set it or raise an error?
                self.set_mode(mode)

    def set_mode(self, mode):
        for event_name, function in mode.items():
            self.add_pair(event_name, function)

    def add_pair(self, event_name, function):  # actually, the way this works the default dict trick isn't even needed, but cool nonetheless
        self.accept(event_name, function)

