# -*- coding: utf-8 -*-
"""
    core.autoreload
    ~~~~~~~~~~~~~~~

    Autoreloading launcher detects changes in the HWIOS filesystem, after which it reloads the whole application.
    Makes debugging and developing a lot easier

    Borrowed from Peter Hunt and the CherryPy project (http://www.cherrypy.org).
    Some taken from Ian Bicking's Paste (http://pythonpaste.org/).
    Adjustments made by Michael Elsdoerfer (michael@elsdoerfer.com).

    :copyright: Portions (c) 2004, CherryPy Team (team@cherrypy.org)
    :license: BSD, see http://cherrypy.org/wiki/CherryPyLicense for details.
"""
import os, sys, time,fnmatch   

try:
    import thread
except ImportError:
    import dummy_thread as thread

# This import does nothing, but it's necessary to avoid some race conditions
# in the threading module. See http://code.djangoproject.com/ticket/2330 .
try:
    import threading
except ImportError:
    pass


RUN_RELOADER = True

_mtimes = {}
_win = (sys.platform == "win32")
extensions = ['py']

def get_files(root=os.curdir):
    """Get a list of files by walking the current directory

    :param str root: The root directory to start
    :return: list - A filelist
    """
    filelist = []
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for file in files:
            file_name = file.split('.')
            try:
                ext = file_name[1]
                if ext in extensions:
                    filelist.append(os.path.join(path,file))
            except IndexError:
                continue
    return filelist

all_files = get_files()

def code_changed():
    """Detect code changes

    :return: bool - Whether or not a change was detected
    """
    global _mtimes, _win
    for filename in all_files:
        _ext = filename.split('.')[1]
        if _ext not in extensions:
            filename = filename[:-1]
        if not os.path.exists(filename):
            continue # File might be in an egg, so it can't be reloaded.
        stat = os.stat(filename)
        mtime = stat.st_mtime
        if _win:
            mtime -= stat.st_ctime
        if filename not in _mtimes:
            _mtimes[filename] = mtime
            continue
        if mtime != _mtimes[filename]:
            _mtimes = {}
            return True
    return False

def reloader_thread(softexit=False):
    """If ``soft_exit`` is True, we use sys.exit(); otherwise ``os_exit`` will be used to end the process.

    :param bool softexit: Whether to force reload or not
    """
    while RUN_RELOADER:
        if code_changed():
            # force reload
            if softexit:
                sys.exit(3)
            else:
                os._exit(3)
        time.sleep(2)

def restart_with_reloader():
    """Try to restart the service"""
    while True:
        args = [sys.executable] + sys.argv
        if sys.platform == "win32":
            args = ['"%s"' % arg for arg in args]
        new_environ = os.environ.copy()
        new_environ["RUN_MAIN"] = 'true'
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
        if exit_code != 3:
            return exit_code
            

def python_reloader(main_func, args, kwargs, check_in_thread=True):
    """
    If ``check_in_thread`` is False, ``main_func`` will be run in a separate
    thread, and the code checker in the main thread. This was the original
    behavior of this module: I (Michael Elsdoerfer) changed the default
    to be the reverse: Code checker in thread, main func in main thread.
    This was necessary to make the thing work with Twisted
    (http://twistedmatrix.com/trac/ticket/4072).
    """
    if os.environ.get("RUN_MAIN") == "true":
        if check_in_thread:
            thread.start_new_thread(reloader_thread, (), {'softexit': False})
        else:
            thread.start_new_thread(main_func, args, kwargs)

        try:
            if not check_in_thread:
                reloader_thread(softexit=True)
            else:
                main_func(*args, **kwargs)
        except KeyboardInterrupt:
            pass
    else:
        try:
            sys.exit(restart_with_reloader())
        except KeyboardInterrupt:
            pass


def main(main_func, args=None, kwargs=None, **more_options):
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}
    reloader = python_reloader
    reloader(main_func, args, kwargs, **more_options)