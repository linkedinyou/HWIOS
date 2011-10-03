# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.my_mod
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The my_mod example module explaining some concepts of HWIOS

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from twisted.internet.task import LoopingCall
from twisted.internet import reactor, defer

from django.utils.translation import ugettext as _
from django.template.loader import render_to_string

from core.application import HWIOS
from web_ui.models.ws_auth import WSAuth
from web_ui.models.signal import Signal


class WS_MyMod(object):
    '''Websocket controller class for the documentation example module'''

    def __init__(self, dispatcher):
        '''
        The WS Constructor is generally used to setup signals for events like disconnect or view_changed
        '''
        self.server_time = 0
        self._timer = False
        self.trip_counter = 0
        self.trip_max = 25000
        dispatcher.signals.subscribe('ws_disconnect', self.left_my_mod)



    def view_my_mod(self, client):
        """Gets the client data and renders the example module template

        :param Client client: The requesting client
        :return: dict - Html-layout data response
        """

        profiles_online = []
        _clients = HWIOS.ws_realm.pool.get_clients()
        for _client in _clients: profiles_online.append(_client.profile.username)
        main = render_to_string("my_mod/view_my_mod.html", {'profile':client.profile,'online':profiles_online})
        return {'data':{'dom':{'main':main}}}
        

    def left_my_mod(self, client = None):
        """Inform other clients when this client leaves, but only if the client was looking at this view while it left

        :param Client client: The requesting client
        :return: dict - Status and html-layout data response
        """
        if client != None:
            if len(client.view_history) > 0 and 'my_mod' in client.view_history[-1]:
                profiles_online = []
                _clients = HWIOS.ws_realm.pool.get_clients()
                for _client in _clients:
                    if _client != client:
                        profiles_online.append(_client.profile.username)
                response = {
                    'status':{
                        'code':'CLIENT_LEFT',
                        'i18n':_('%(username)s left the building!') % {'username':client.profile.username},
                        'type': HWIOS.ws_realm._t['notify-info'],
                    },
                    'data':{'online':profiles_online}
                }
                for _client in _clients:
                    if client != _client:
                        _client.remote('/my_app/notify_leave/',response)


    def notify(self, client, text):
        """send a message to all other clients

        :param Client client: The requesting client
        :param str text: The text to send to the other clients
        :return: dict - Status and html-layout data response
        """
        _clients = HWIOS.ws_realm.pool.get_clients()
        for _client in _clients:
            #send to each client, except the source-client
            if client != _client:
                #send the text message to the ws-method of each client
                _client.remote('/my_mod/message/',{'data':{'text':text}})
        #return some example data to the client that sent the message
        return {'data':{'sent':len(text),'clients':len(_clients) - 1}}


    def trip(self, client):
        """Little benchmarking tool for pypy/cpython comparison

        :param Client client: The requesting client
        :return: dict - Status and html-layout data response
        """
        #end recursion other clients, while reset hasnt been done yet
        if self.trip_counter == -1:
            client_response = {'data':{'trips':self.trip_max,'continue':False,'server_time':self.server_time}}
        if not self._timer and self.trip_counter == 0:
            self._start_timer()            
        #if within range and timer is running
        if self.trip_counter < self.trip_max:
            self.trip_counter += 1
            client_response = {'data':{'trips':self.trip_counter,'continue':True,'server_time':self.server_time}}
        else:     
            self._stop_timer()
            
            client_response = {'data':{'trips':self.trip_max,'continue':False,'server_time':self.server_time}}
        return client_response
        

    def _trip_timer(self):
        self.server_time += 1
        
        
    def _reset_trip_timer(self):
        self._timer = False
        self.trip_counter = 0
        

    def _start_timer(self):
        self._timer = True        
        self._repeater = LoopingCall(self._trip_timer)
        self._repeater.start(1)
        

    def _stop_timer(self):
        #allow other clients to get out of the recursion as well
        reactor.callLater(1, self._reset_trip_timer)
        self._repeater.stop()
        self._timer = False
        self.server_time = 0
        #set to negative value to prevent timer to be started by subsequent requesting client
        self.trip_counter = -1

