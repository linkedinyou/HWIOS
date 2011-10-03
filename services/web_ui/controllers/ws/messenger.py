# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.messenger
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The messenger's module websocket routing logics

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os,sys
import time
from twisted.internet import defer
from django.template.loader import render_to_string
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist

from hwios.core.application import HWIOS
from web_ui.models.ws_auth import WSAuth
from web_ui.models.profiles import Profile


class WS_Messenger(object):    
    """
    Websocket controller class for the messenger module
    """
    
    def __init__(self, dispatcher):
        dispatcher.signals.subscribe('ws_connect', self.update_online)
        dispatcher.signals.subscribe('ws_disconnect', self.update_online)
        

    def init_messenger(self, client):
        """
        When websocket client connects, it will get it's online list from here
        """
        context = render_to_string("messenger/context_menu.html", {'profile':client.profile})
        _data = self.read_online(client)
        _data['data']['dom']= {'context':context}
        return _data

        
    def read_online(self, client):
        """Return an online list to all connected clients after one connects/disconnects

        :param Client client: The requesting client
        :return: dict - Data response containing the userlist            
        """
        user_list = []
        clients = HWIOS.ws_realm.pool.get_clients()
        for _client in clients:
            user_list.append({
                'id':_client.profile.id,
                'name':_client.profile.username,
                'avatar':_client.profile.photo
            })
        for _client in clients:
            if _client != client:
                _client.remote('/data/modules/messenger/online/update/',{'online':user_list})
        return {'data':{'online':user_list}}


    def update_online(self, client):
        """Return an online list to all connected clients after one connects/disconnects,
        and also return the context to the disconnecting/connecting user

        :param Client client: The requesting client
        :return: dict - Data response containing the userlist
        """
        _data = self.read_online(client)
        _data.update(self.init_messenger(client))
        return _data 
            
    def send_message(self, client, message):
        """Core business of the messenger. Sending messages to other clients

        :param Client client: The requesting client
        :param str message: Message that the client wants to send to other clients
        :return: dict - Data response containing the message and the client who sent the message
        """
        _time = time.strftime("%H:%M", time.localtime())
        for aclient in HWIOS.ws_realm.pool.get_clients():
            if aclient != client:             
                aclient.remote('/data/modules/messenger/messages/receive/',{'message':message,'from':client.profile.username,'time':_time})
        return {'data':{'message':message,'from':client.profile.username,'time':_time}}
        

    def send_private_message(self, client, to_client_uuid, message):
        """Sends a message only to a specified client. Not in use currently

        :param Client client: The requesting client
        :param str to_client_uuid: The uuid of the client to which send the message
        :param str message: Message that the client wants to send
        """
        target_message = ['/%s/frontend/personal/pm/pm/' % to_client_uuid,{'from':{'name':'%s %s' % (client.profile.first_name,client.profile.last_name)}, 'message':message}]
        HWIOS.ws_realm.queue.process(target_message)        
        
