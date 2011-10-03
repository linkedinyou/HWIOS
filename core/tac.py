# -*- coding: utf-8 -*-
"""
    core.tac
    ~~~~~~~~~~~~

    General twisted tac loader and service initializer. Both being used for autoreload and daemonizing

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""


import os, sys
from ConfigParser import ConfigParser
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except: pass

from twisted.application import internet, service
from twisted.internet import reactor

#Set our environment, so the hwios namespace can be found
os.environ['DJANGO_SETTINGS_MODULE'] = 'web_ui.settings'
HWIOS_ROOT = os.getcwd()
sys.path.append(os.path.join(HWIOS_ROOT,'./'))
sys.path.append(os.path.join(HWIOS_ROOT,'services'))

from core.application import HWIOS
from services.loader import ServiceLoader

application = service.Application('HWIOS')
HWIOS.application = application
HWIOS.config = ConfigParser()
HWIOS.config.read(os.path.join(HWIOS_ROOT,'hwios.ini'))
if 'autoreload-twistd.py' not in sys.argv[0]:
    service.IProcess(HWIOS.application).processName  ="hwios"
HWIOS.service_collection = service.IServiceCollection(application)
ServiceLoader(HWIOS.config)
reactor.suggestThreadPoolSize(HWIOS.config.getint('general','threadpool'))
