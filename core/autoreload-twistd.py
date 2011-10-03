# -*- coding: utf-8 -*-
"""
    core.autoreload-twistd
    ~~~~~~~~~~~~~~~~~~~~~~

    Restarts HWIOS using the cherrypy autoreload script

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""


import autoreload
import twisted.scripts.twistd as t
import sys
autoreload.main(t.run)

