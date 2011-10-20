Application
===========

All application-related code has to do with starting and managing the application and it's services. The hwios executable is an executable
python file, which has some parameter options to select the appropriate hwios action. When it starts the application through --debug or
--start, either the autoreload file is executed(--debug, just for debugging yes) or the twistd daemonizer is called directly to daemonize the
hwios process. The core.tac file is responsible to initialize the application and it's services. Use *./hwios --help* for a list of parameters:

::

    # ./hwios --help
    Usage: hwios [options]

    Options:
    -h, --help  show this help message and exit
    --setup     Setup HWIOS database and initial data
    --debug     Start HWIOS in debug modus
    --start     Start and daemonize HWIOS
    --pypy      Start HWIOS with PyPy JIT 1.4
    --stop      Stop HWIOS daemon
    --ulang     Updates or creates language files
    --dump      Dump Fixtures
    --syncdb    Synchronize Database
    --load      Load Fixtures
    --deploy    Optimizes web assets for deployment
    --test      Run debug tests

Code References
---------------

.. automodule:: core.tac
   :members:
   :show-inheritance:

.. automodule:: core.application
   :members:
   :show-inheritance:

.. automodule:: services.loader
   :members:
   :show-inheritance:

.. automodule:: core.autoreload
   :members:
   :show-inheritance:

.. automodule:: core.connection
   :members:
   :show-inheritance:

.. automodule:: core.static_file
   :members:
   :show-inheritance:

.. automodule:: core.tools
   :members:
   :show-inheritance: