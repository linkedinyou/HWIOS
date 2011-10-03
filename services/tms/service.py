# -*- coding: utf-8 -*-
"""
    services.tms.service
    ~~~~~~~~~~~~~~~~~~~~

    The tms service is a tilemap service that's mainly used for opensim-related maps currently, but can be extended for usage
    with other virtual world platforms like RealXtend Tundra or MV3D. 

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os,sys
from ConfigParser import ConfigParser

from hwios.core.static_file import StaticFile

from twisted.application.internet import TCPServer, SSLServer
from twisted.web import static, server
from twisted.web.static import File, Registry
from twisted.web.resource import Resource
from tiler import Tiler



class TmsService(object):
    """HWIOS HTTP Service for mapping purposes"""
    
    client_settings = {}

    def __init__(self,service_config, hwios_config):
        self.hwios_config = hwios_config
        self.config = service_config
        root = Resource()
        root.putChild("tiles",TileService(os.path.join(self.config.location,self.config.get('map','tilepath'))))
        site = server.Site(root)
        site.displayTracebacks = False
        self.config.tilepath = os.path.join(self.config.location,'tiles')
        self.tiler = Tiler(self.config)
        self.get_client_settings()

        #override hwios general ssl setting
        if self.hwios_config.has_option('general','ssl'):
            from twisted.internet import ssl
            from hwios.core.connection import ServerContextFactory
            self.__service = SSLServer(self.config.getint('service', 'port'),site,ServerContextFactory())
        else: 
            if self.config.getboolean('service','ssl'):
                from twisted.internet import ssl
                from hwios.core.connection import ServerContextFactory
                self.client_settings['ssl'] = True
                self.__service = SSLServer(self.config.getint('service', 'port'),site,ServerContextFactory())
            else: 
                self.client_settings['ssl'] = False
                self.__service = TCPServer(self.config.getint('service','port'),site,100,self.config.get('service','listen'))				

    def get_service(self):
        """Get a reference to the actual twisted service

        :return: TCPServer or SSLServer
        """
        return self.__service
        
    def get_client_settings(self):
        """Client-settings are parsed with the bootstrapping process to communicate vital information about the service

        :return: dict - Some useful information about this service
        """
        self.client_settings['uri'] = '%s:%s' % (self.hwios_config.get('general','uri'),self.config.get('service','port'))
        self.client_settings['center'] = [self.config.getint('map','center_x'),self.config.getint('map','center_y'),self.config.getint('map','center_z')]
        self.client_settings['osm_ztop'] = self.config.getint('map','osm_ztop')
        self.client_settings['raw_ztop'] = self.config.getint('map','raw_ztop')
        self.client_settings['zlevels'] = self.config.getint('map','zlevels')
        self.client_settings['osm'] = self.config.getboolean('map','osm')
        self.client_settings['theme'] = self.config.get('map','theme')
        self.client_settings['cache'] = self.config.get('map','cache')
        return self.client_settings
        
        
class TileService(StaticFile):
    """A modified StaticFile resource, to return opaque images on a 404"""
    
    def __init__(self, path, defaultType="text/html", ignoredExts=(), registry=None, allowExt=0):
        StaticFile.__init__(self, path)
        self.childNotFound = StaticFile('%s/404.png' % path)
        self.childNotFound.isLeaf=True