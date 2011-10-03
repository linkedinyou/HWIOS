# -*- coding: utf-8 -*-
"""
    services.web_ui.models.webdav
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Simple WSGI-Dav implementation for webdav filesharing

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import os,sys

from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.dav_provider import _DAVResource
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.wsgidav_app import DEFAULT_CONFIG
from wsgidav.http_authenticator import HTTPAuthenticator

from twisted.web import resource, server, static
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login

from web_ui.models.profiles import Profile


class DjangoDomainController(object):
    

    def __init__(self, userMap =None):
        self.userMap = userMap
        

    def __repr__(self):
        return self.__class__.__name__
        

    def getDomainRealm(self, inputURL, environ):
        davProvider = environ["wsgidav.provider"]
        if not davProvider:
            if environ["wsgidav.verbose"] >= 2:
                print >>sys.stderr, "getDomainRealm(%s): '%s'" %(inputURL, None)
            return None
        realm = davProvider.sharePath
        if realm == "":
            realm = "/"
        return realm
    
    
    def requireAuthentication(self, realmname, environ):
        return True
        
    
    def isRealmUser(self, realmname, username, environ):
        raise NotImplementedError("We need a raw password in order to authenticate properly against django. Please disable digest authentication!")
    
            
    def getRealmUserPassword(self, realmname, username, environ):
        raise NotImplementedError("We need a raw password in order to authenticate properly against django. Please disable digest authentication!")
    
    def getRealmUserPassword(self, realmname, username, environ):
        return self.userMap.get(realmname, {}).get(username, {}).get("password")
        
    
    def authDomainUser(self, realmname, username, password, environ):
        try:
            username = username.split(' ')
            if len(username) == 2:
                user = authenticate(username=username, password = password)
            else: return False
            if user != None:
                if realmname == '/config':
                    if user.is_active and user.is_staff: return True
                elif realmname == '/':
                    if user.is_active == 1: return True
        except ObjectDoesNotExist:
            pass
        return False
        
        
class WebDAV(object):
    
    
    def __init__(self,service):
        root_dav= FilesystemProvider(os.path.join(service.config.location,'dav_store'))
        config_dav = FilesystemProvider(os.path.join(service.config.location,'dav_store','config'))
        domain_controller = DjangoDomainController()
        config = DEFAULT_CONFIG.copy()
        config.update({
            "mount_path": "/dav",
            "provider_mapping": {"/": root_dav,'/config':config_dav},
            "verbose": 1,
            "enable_loggers": [],
            "acceptbasic": True,      
            "acceptdigest": False,    
            "defaultdigest": False,
            "propsmanager": True,      # True: use property_manager.PropertyManager                    
            "locksmanager": True,      # True: use lock_manager.LockManager                   
            "domaincontroller": domain_controller,
        })
        self.wsgidav = WsgiDAVApp(config)
        
    
    def wsgidav_application(self,environ, start_response): 
        return self.wsgidav(environ, start_response)
        
        
    def get_resource(self):
        return WSGIResource(reactor, reactor.getThreadPool(), self.wsgidav_application)