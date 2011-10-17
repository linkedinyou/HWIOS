# -*- coding: utf-8 -*-
"""
    services.web_ui.service
    ~~~~~~~~~~~~~~~~~~~~~~~

    The twisted service that takes care of websocket and HTTP traffic

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os
import sys

from django.core.handlers.wsgi import WSGIHandler
from twisted.application.internet import TCPServer, SSLServer
from twisted.web import static,server, resource, wsgi
from twisted.web.server import NOT_DONE_YET
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.python import threadpool
from twisted.web import http

import web_ui.settings as settings
from core.application import HWIOS
from core.static_file import StaticFile

from web_ui.models.http import WebSocketHandler, WebSocketSite
from web_ui.models.ws_router import WebSocketRouter
from web_ui.models.ws_realm import WSRealm
from web_ui.models.webdav import WebDAV
from web_ui.models.settings import Settings
import web_ui.settings as settings
from web_ui.models.plasmoids import Plasmoids



class MainThreadWSGIResource(wsgi.WSGIResource):
    """Runs twisted in the main thread. This is necessary when running hwios in debug mode,
    a file changes and hwios is reloaded"""
    
    def __init__(self,reactor,app):
        wsgi.WSGIResource.__init__(self,reactor,None,app)


    def render(self,request):
        """Render the wsgi response

        :param Request request: A wsgi request
        :return: NOT_DONE_YET - Some twisted-related return
        """
        response = wsgi._WSGIResponse(self._reactor, self._threadpool, self._application, request)
        response.run()
        return NOT_DONE_YET

class RootResource(resource.Resource):
    """The root resource is where other resources like static files or more dynamic resources can be added to"""

    def __init__(self, wsgi_resource):
        resource.Resource.__init__(self)
        self.wsgi_resource = wsgi_resource


    def getChild(self, path, request):
        """Handles child resource

        :param str path: The path to the resource
        :param Request request: The Twisted request
        :return: WSGI-Resource - Returns a wsgi resource

        """
        request.prepath.pop()
        request.postpath.insert(0,path)
        return self.wsgi_resource
        
        
class Web_uiService(object): 
    """HWIOS Web Service with WSGIDav, Django WSGI and Static Media resources"""
    
    client_settings = {}    
    
    def __init__(self,service_config, hwios_config):
        wsgi_handler = WSGIHandler()
        self.hwios_config = hwios_config
        self.config = service_config
        if sys.argv[0] == 'core/autoreload-twistd.py':
            root = RootResource(self._single_threaded_wsgi_resource(wsgi_handler))
        else:
            root = RootResource(self._multi_threaded_wsgi_resource(wsgi_handler))
        root.putChild("dav", WebDAV(self).get_resource())
        root.putChild("media", StaticFile(os.path.join(os.path.join(self.config.location, 'media'))))
        root.putChild("docs", StaticFile(os.path.join(os.path.join(self.config.location, '../','../','docs','_build','html'))))
        HWIOS.ws_realm = WSRealm()
        HWIOS.plasmoids = Plasmoids()
        site = WebSocketSite(root)
        site.addHandler("/ws", WebSocketRouter)
        site.displayTracebacks = False        
        #override hwios general ssl setting
        if self.hwios_config.has_option('general','ssl'):
            from twisted.internet import ssl
            from hwios.core.connection import ServerContextFactory
            self.__service = SSLServer(self.config.getint('service', 'port'),site,ServerContextFactory())
        else: 
            if self.config.getboolean('service','ssl'):
                from twisted.internet import ssl
                from hwios.core.connection import ServerContextFactory
                self.__service = SSLServer(self.config.getint('service', 'port'),site,ServerContextFactory())
            else:
                self.__service = TCPServer(self.config.getint('service','port'),site,0,self.config.get('service','listen'))

            
    
    def _multi_threaded_wsgi_resource(self,wsgi_handler):
        """runs twisted in a thread-pool for production mode"""
        pool = threadpool.ThreadPool()
        pool.start()
        reactor.addSystemEventTrigger('after', 'shutdown', pool.stop)
        wsgi_resource = wsgi.WSGIResource(reactor, reactor.getThreadPool(), wsgi_handler)
        return wsgi_resource
        
        
    
    def _single_threaded_wsgi_resource(self,wsgi_handler):
        """runs twisted in a single thread (debug-mode) so autoreload works properly"""
        wsgi_resource = MainThreadWSGIResource(reactor, wsgi_handler)
        return wsgi_resource
                
    
    def get_client_settings(self):
        """Client-settings are parsed with the bootstrapping process to communicate vital information about the service

        :return: dict - Some useful information about this service
        """
        self.client_settings['uri'] = '%s:%s' % (self.hwios_config.get('general','uri'),self.config.get('service','port'))
        self.client_settings['ssl'] = self.config.getboolean('service','ssl')
        self.client_settings['default_theme'] = settings.HWIOS_THEME
        return self.client_settings
        
        
    def get_service(self):
        """Get a reference to the actual twisted service

        :return: TCPServer or SSLServer
        """
        return self.__service        
            
    
    def drop_privileges(self):
        """Drop privileges after starting hwios as root (Unix only)"""
        import pwd
        import grp
        
        uid_name = self.config.get('system','unprivileged_user')
        gid_name = self.config.get('system','unprivileged_group')
        
        # Get the uid/gid from the name
        running_uid = pwd.getpwnam(uid_name)[2]
        running_gid = grp.getgrnam(gid_name)[2]

        # Try setting the new uid/gid
        try:
            os.setgid(running_gid)
        except OSError, e:
            print 'Could not set effective group id: %s' % e
            exit()

        try:
            os.setuid(running_uid)
        except OSError, e:
            print 'Could not set effective user id: %s' % e
            exit()

        # Ensure a very convervative umask
        new_umask = 077
        old_umask = os.umask(new_umask)
        print 'drop_privileges: Old umask: %s, new umask: %s' % \
                 (oct(old_umask), oct(new_umask))

        final_uid = os.getuid()
        final_gid = os.getgid()
        print 'drop_privileges: running as %s/%s' % \
                 (pwd.getpwuid(final_uid)[0],
                  grp.getgrgid(final_gid)[0])        
