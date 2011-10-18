# -*- coding: utf-8 -*-
"""
    core.autoreload-twistd
    ~~~~~~~~~~~~~~~~~~~~~~

    Restarts HWIOS using the cherrypy autoreload script

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import sys
import autoreload
try:
    import twisted.scripts.twistd as t
    autoreload.main(t.run)
except ImportError:
    print "Failed to import twisted. Did you set PYTHONPATH yet?"
    print "Example: export PYTHONPATH=/usr/lib/python2.7/site-packages/"