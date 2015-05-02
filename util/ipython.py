"""
    reimplementation of ipython functions that don't behave as expected
"""
#stuff to make our own embed() that can handle threads
from IPython.terminal.embed import InteractiveShellEmbed
from IPython.terminal.ipapp import load_default_config 
import sqlite3

def embed(**kwargs): #reimplementation of embed that can handle threads
    """ see IPython.terminal.embed for original impelmentation
        the only addition is check_same_thread=False to allow
        sqlite3 to exit property at shutdown
    """
    config = kwargs.get('config')
    header = kwargs.pop('header','')
    compile_flags = kwargs.pop('compile_flags', None)
    if config is None:
        config = load_default_config()
        config.InteractiveShellEmbed = config.TerminalInteractiveShell
        kwargs['config'] = config
    shell=InteractiveShellEmbed.instance(**kwargs)
    #/* added start
    hist_kwargs = dict(detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES,
                       check_same_thread=False, #XXX THIS
                      )
    shell.history_manager.db = sqlite3.connect(shell.history_manager.hist_file, **hist_kwargs)
    # added end */
    shell(header=header, stack_depth=2, compile_flags=compile_flags)
