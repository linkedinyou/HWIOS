# -*- coding: utf-8 -*-
"""
    services.dsm.service
    ~~~~~~~~~~~~~~~~~~~~

    The twisted service that takes care of the distributed service management daemon pool

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
from twisted.spread.pb import PBServerFactory
from twisted.cred import portal
from twisted.application import internet
from twisted.internet import defer
from twisted.python import failure, log

from hwios.core.application import HWIOS
from dsm_server import DSMServer,DSMRealm,DSMCredChecker,DSMPortalRoot


class DsmService(object): 
    """Twisted Perspective Broker service for remote service management"""
    
    def __init__(self,service_config, hwios_config):
        self.hwios_config = hwios_config 
        self.config = service_config 
        self.realm = DSMRealm()
        self.realm.server = DSMServer(self)
        django_checker = DSMCredChecker()
        p = portal.Portal(self.realm)
        p.registerChecker(django_checker)
        pr = DSMPortalRoot(p)
        if self.hwios_config.has_option('general','ssl'):
            from twisted.internet import ssl
            from hwios.core.connection import ServerContextFactory
            self.__service = internet.SSLServer(self.config.getint('service','port'),PBServerFactory(pr),ServerContextFactory())
        else:            
            if self.config.getboolean('service','ssl') == True:
                from twisted.internet import ssl
                from hwios.core.connection import ServerContextFactory
                self.__service = internet.SSLServer(self.config.getint('service','port'),PBServerFactory(pr),ServerContextFactory())
            else:
                self.__service = internet.TCPServer(self.config.getint('service','port'),PBServerFactory(pr))

    
    def get_service(self):
        """Get a reference to the actual twisted service

        :return: TCPServer or SSLServer
        """
        return self.__service
        
        
    def register_server(self,pb_server):
        """Initialize the pb_server in the HWIOS namespace after initializing

        :param DSMServer pb_server: The DSMServer that's registered
        """
        HWIOS.pb_server = pb_server
        
    
    def update_pb_pool(self,pb_clients):
        """Update the pb_pool variable in the HWIOS namespace when necessary

        :param list pb_clients: A list of connected pb clients
        """
        HWIOS.pb_pool = pb_clients
        
    
    def dispatch(self, url, params):
        """Dispatch a pb call to the matching websocket function


        :param str url: The url to route to
        :param dict params: The parameters to add to the function
        :return: None or Exception
        """
        try:
            method = HWIOS.ws_realm.dispatcher.route(url)
            if method is None: raise MethodNotFound()
            t = type(params)
            if t is list:
                #mix client and list params in
                method[2]['params'] = params
                res = getattr(method[0],method[1])(**method[2])
            elif t is dict: 
                params.update(method[2])
                res = getattr(method[0],method[1])(**params)
            else: raise InvalidParams()
            if isinstance(res, defer.Deferred):
                res.addBoth(self.respAny)
                return            
        except Exception, e:
            res = e