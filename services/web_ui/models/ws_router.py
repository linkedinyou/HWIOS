# -*- coding: utf-8 -*-
"""
    services.web_ui.models.ws_router
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Websocket routing handlers

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import random
from datetime import datetime
import uuid
from collections import deque

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation

from twisted.python import failure, log
from twisted.internet import defer
from twisted.python import log
from twisted.internet import reactor

from core.application import HWIOS
import web_ui.settings as settings

from web_ui.models.profiles import Profile
from web_ui.models.http import WebSocketHandler, WebSocketSite,WebSocketTransport

  
class WebSocketRouter(WebSocketHandler):
    """
    This is the main websocket router
    """
    
    def __init__(self, transport):
        self.transport = transport
        self.instance_paths = []
        self.transport.view_history = deque(maxlen=10)
        #translation.activate('nl')
        
        if self.transport.cookie:
            self.session_id = None
            cookie_params = self.transport.cookie[0].split(';')
            for param in cookie_params:
                if 'sessionid' in param:
                    self.session_id = param.split('=')[1]
            if self.session_id != None:
                try:
                    self.transport.session = Session.objects.get(pk=self.session_id).get_decoded()
                    self.transport.session_store = SessionStore(session_key=self.session_id)
                    self.transport.session_store['online_since'] = datetime.now()
                    self.transport.session_store.save()
                    if '_auth_user_id' in self.transport.session:
                        try:
                            self.transport.profile = Profile.objects.get(pk = self.transport.session['_auth_user_id'])
                            self.transport.profile.is_authenticated = True
                        except Profile.DoesNotExist:
                            try:
                                Session.objects.get(pk=self.session_id).delete()
                            except Session.DoesNotExist: pass  
                            self.transport.profile = self.get_anonymous_profile()
                    else: 
                        self.transport.profile = self.get_anonymous_profile()
                except ObjectDoesNotExist:
                    self.transport.session_store = SessionStore(session_key=self.session_id)
                    self.transport.session_store['online_since'] = datetime.now()
                    self.transport.session_store['language'] = 'en-us'
                    self.transport.session_store.save()
                    #print self.session_id
                    self.transport.session = Session.objects.get(pk=self.session_id).get_decoded()
                    self.transport.profile = self.get_anonymous_profile()
            else: 
                self.transport.profile = self.get_anonymous_profile()
        else:
            self.transport.profile = self.get_anonymous_profile()

    
    def connectionMade(self):
        self.transport._client = HWIOS.ws_realm.pool.add_client(self.transport)
        self.transport.view_history = []



    def frameReceived(self, frame):
        if 'language' in self.transport._client.session:
            translation.activate(self.transport._client.session['language'])
        else:
            translation.activate('en-us')
        res = {}
        plasmoids = None
        try:
            _decoded = HWIOS.tools.json_decode(frame)
            self.url = _decoded[0]
            params = _decoded[1]
            if len(_decoded) == 3:
                self.uuid = _decoded[2]
            else:
                self.uuid = ''
            #Data not in url means this is a view
            if 'data' not in self.url:
                self.transport.view_history.append(self.url)
                plasmoids = HWIOS.plasmoids.route(self.transport.view_history, self.transport._client.profile)
                if len(self.transport.view_history) >= 2:
                    HWIOS.ws_realm.pool.signals.send('view_changed', client = self.transport._client, filters = [self.transport.view_history[-2],self.transport.view_history[-1]])
            log.msg('%s WS/76/HRM' % self.url,system='%s,IN' % self.transport.getPeer().host)
        except ValueError as strerror:
            _errormsg = 'JSON Parsing error - %s' % strerror
            log.msg('%s WS/76/HRM' % _errormsg,system='%s,IN' % self.transport.getPeer().host)
            return False
        if self.url == None:
            raise InvalidReq()            
        method = HWIOS.ws_realm.dispatcher.route(self.url)
        if method is None:
            _errormsg = 'Error 404 - Resource route not found!'
            log.msg('%s WS/76/HRM' % _errormsg,system='%s,IN' % self.transport.getPeer().host)
            return False
        t = type(params)
        if t is list:
            #mix client and list params in
            method[2]['client'] = self.transport._client
            method[2]['params'] = params
            #get the websocket controller's result
            result = getattr(method[0],method[1])(**method[2])
        elif t is dict: 
            params.update(method[2])
            params['client'] = self.transport._client
            #get the websocket controller's result
            result = getattr(method[0],method[1])(**params)
        else: raise IOError()
        if isinstance(result, defer.Deferred):
            result.addBoth(self.respAny)
            return
        if plasmoids != None:
            result['data']['plasmoids'] = plasmoids
        self.respAny(result)



    def respAny(self, result):
        if not isinstance(result, failure.Failure) and not isinstance(result, Exception):
            #server forces client to a view state from a ws view
            if result != None and 'status' in result:
                if 'state' in result['status']:
                    self.transport.view_history.append(result['status']['state'])
            self.transport.write(HWIOS.tools.json_encode([result, self.url, self.uuid]))
        elif isinstance(result, failure.Failure):
            log.err(result)
            result = result.value
            self.transport.write(HWIOS.tools.json_encode({'error':result}))
        

        
    def notify(self, method, *params):
        self.transport.write(HWIOS.tools.json_encode([method, params]))
        
        
    def connectionLost(self,foo):
        HWIOS.ws_realm.pool.rm_client(self.transport)
        try:
            if 'online_since' in self.session_store:
                del self.session_store['online_since']
            self.session_store.save()
        except AttributeError:
            pass        
        

    def get_anonymous_profile(self):
        """Return a random anonymous profile object"""
        profile = Profile()
        profile.is_authenticated = False
        while True:
            #random id of a visitor is set in the http bootstrapping call, and transferred using the session object
            username = 'visitor_%s' % self.transport.session['id']
            if not HWIOS.ws_realm.pool.name_taken(username):
                profile.username = username
                profile.id = self.transport.session['id']
                try:
                    profile.uuid = uuid.uuid5(uuid.NAMESPACE_DNS, str(self.session_id))

                except AttributeError:
                    profile.uuid = uuid.uuid5(uuid.NAMESPACE_DNS, self.transport.getPeer().host)
                break
            else:
                self.transport.session['id'] = random.randint(1000,9999)
                self.get_anonymous_profile()
        return profile
        
        
    def remote_delay_client(self,method,params = None, delay=0):
        def remote_delay(self,method,params = None):
            self.transport.write(HWIOS.tools.json_encode([method, params])) 
            log.msg('%s WS/76/HRM' % (method),system='%s,OUT' % self.transport.getPeer().host) 
        reactor.callLater(self.remote_delay,method,params)
    
