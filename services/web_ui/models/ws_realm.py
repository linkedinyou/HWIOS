# -*- coding: utf-8 -*-
"""
    services.web_ui.models.ws_realm    
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Websocket pooling and dispatching handlers

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os
import re
import uuid
import random
from twisted.internet import reactor, defer
from twisted.python import failure, log
from django.contrib.sessions.models import Session


from core.application import HWIOS
from web_ui.models.signal import Signal, SignalPool
import web_ui.urls as urls

from web_ui.models.statics import *
from web_ui.models.profiles import Profile
from web_ui.models.client import Client



class WebSocketDispatcher(object):
    """
    The websocket dispatcher takes care of routing and matching of urls to the appropriate controller
    """
    signals = SignalPool()
    
    compiled_ws_patterns = []
    valid_routes = {}
   
    def __init__(self):
        '''
        Initialize all modules that are specified in urls.py
        '''
        self.pool = WebSocketPool(self.signals)  
        for pattern in urls.ws_patterns:
            p = re.compile(pattern[0])
            module = __import__(pattern[1], globals(), locals(), [pattern[2]],-1)
            self.compiled_ws_patterns.append((p,module,pattern[2],pattern[3]))    
        for pattern in self.compiled_ws_patterns:
            if pattern[2] not in self.valid_routes:
                self.valid_routes[pattern[2]] ={'instance': getattr(pattern[1],pattern[2])(self),'methods':[]}
            self.valid_routes[pattern[2]]['methods'].append(pattern[3])
            
            
    def _match(self, url):
        '''Loops though regex patterns to search for a match'''
        for pattern in self.compiled_ws_patterns:
            rp = pattern[0].match(url) 
            if rp != None:
                return (pattern[2],pattern[3], rp.groupdict())
        return None
        
    
    def route(self, url):
        '''Routes urls to the appropriate websocket controller

        :param str url: the url to match the pattern-collection with
        :return: list or None - reference-list to a websocket controller or None
        '''
        cls, method, params = self._match(url)
        if cls in self.valid_routes:
            instance = self.valid_routes[cls]['instance']
            if hasattr(instance, method):
                return [instance, method, params]
            else:
                return None
        return None

    
class WebSocketPool(object):
    '''
    The websocket pool is used to keep track of subscriptions and clients in the websocket domain
    '''
    clients = []
    subscription = {}
    
    def __init__(self, signals):
        self.signals = signals
        self.userlist = []
        #register signals
        #TODO: move to it's own signal initializing
        self.signals.append(Signal('view_changed'))
        self.signals.append(Signal('ws_connect'))
        self.signals.append(Signal('ws_disconnect'))
        self.signals.append(Signal('profile_changed'))
        self.signals.append(Signal('profile_created'))
        self.signals.append(Signal('profile_deleted'))
        
    
    def name_taken(self, username):
        """Checks if the username exists in our list of anonymous and registered clients

        :param str username: the username to check for
        :return: bool - Acknowledgement whether username exists or not
        """
        for _client in self.clients:
            if _client.profile != None:
                if _client.profile.username == username:
                    return True
            else:
                return False
        return False        
        

        
    def _clear_subscriptions(self, client):
        """When a client disconnects, remove all subscription references that may be left"""
        for area in self.subscription: 
            for cid in self.subscription[area]:
                for _client in self.subscription[area][cid]['clients']:
                    if _client.profile.uuid == client.profile.uuid:
                        self.subscription[area][cid]['clients'].remove(_client)


    def add_client(self, transport):
        """Setup a client instance for this transport, and add it to the general client-list

        :param transport transport: A representation of the socket connection
        :return: client - Return the client object for further processing
        """
        new_client = Client(transport.profile, transport.session, 'nl')
        new_client.transport = transport 
        self.clients.append(new_client)
        log.msg('%s WS/76/HRM' % ('New client added...'),system='%s,IN' % transport.getPeer().host) 
        self.signals.send('ws_connect', client = new_client) 
        return new_client

            
    def rm_client(self, transport):
        """Remove a client from the general client-list when the client websocket connection is terminated

        :param transport transport: A representation of the socket connection
        """        
        try:        
            for _client in self.clients:
                if _client.transport == transport:
                    self.clients.remove(_client)
                    self._clear_subscriptions(_client)
        except ValueError: pass
        self.signals.send('ws_disconnect', client = transport)
            
        
    def get_clients(self, client_filter = None):
        """Find clients in the general client-list, and optionally apply a filter.
        Filter options are: 'all','users' or 'moderators'.

        :param str client_filter: a predefined filter to operate on the general client-list
        :return: list - Return a list of clients
        """
        __clients = []
        if client_filter == 'all' or client_filter == None:
            return self.clients 
        elif client_filter == 'users':
            for _client in self.clients:
                if _client.profile.is_authenticated:
                    __clients.append(_client)
        elif client_filter == 'moderators':
            for _client in self.clients:
                if _client.profile.is_staff:
                    __clients.append(_client)
        #:todo: friends and groups added later
        return __clients        
    
        
    def get_client(self, uuid = None, username = None):
        """Find a client in the general client-list, based on it's profile uuid

        :param str profile_uuid: The profile uuid to find the client with
        :return: client or None 
        """
        if uuid != None:
            for _client in self.clients:
                if _client.profile.uuid == uuid:
                    return _client
        elif username != None:
            for _client in self.clients:
                if _client.profile.username == username:
                    return _client
        return None
        
        

class WSRealm(object):
    """
    Initializes and keeps all websocket related handlers together.
    """
    
    def __init__(self):
        self.dispatcher = WebSocketDispatcher()
        self.pool = self.dispatcher.pool
        #self.queue = HWM_Queue()
        self._t = ws_table   
