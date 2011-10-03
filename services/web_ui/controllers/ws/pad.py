# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.pad
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Websocket handling for the pad module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os,sys
from twisted.internet import defer
from django.template.loader import render_to_string
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _

from core.application import HWIOS
from web_ui.models.pad import Pad
from web_ui.models.ws_auth import WSAuth
from web_ui.models.profiles import Profile
from web_ui.models.infinote import InfinoteEditor
from web_ui.forms.profiles import *

from web_ui.models.activity import *

class WS_Pad(object):
    """
    Websocket controller class for the pad module
    """
    
    def __init__(self, dispatcher):
        #dispatcher.signals.subscribe('ws_disconnect', self.leave_mouse)
        dispatcher.signals.subscribe('ws_disconnect', self._unsubscribe_client)
        dispatcher.signals.subscribe('view_changed', self._unsubscribe_client, filters = [(r'/views/pad/(?P<pad_id>[^/]+)/',True),(r'/views/pad/(?P<pad_id>[^/]+)/',False)]) 
        self.id = 1  


    def get_context(self, client):
        context = render_to_string("pad/context_menu.html", {'profile':client.profile})
        return {'data':{'dom':{'context':context}}}
    

    def sync_pad(self, client, pad_id):
        """Gets the current pad drawing state and renders the pad view

        :param Client client: The requesting client
        :param int pad_id: The pad_id of the pad to modify
        :return: dict - data and html-layout data response
        """
        self._subscribe_client(client, pad_id)
        main = render_to_string('pad/read_pad.html')
        left_widget = render_to_string('pad/layers.html')
        return  {'data':{'dom':{'main':main,'left':left_widget},
                'layers':HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers']}
                }       
        
        
    def _subscribe_client(self, client, pad_id):
        """Helper function to subscribe to a pad pool."""
        if 'pad' not in HWIOS.ws_realm.pool.subscription:
            HWIOS.ws_realm.pool.subscription['pad'] = {}
        if pad_id not in HWIOS.ws_realm.pool.subscription['pad']:
            try:      
                HWIOS.ws_realm.pool.subscription['pad'][pad_id] = HWIOS.tools.json_decode(str(Pad.objects.get(slug = pad_id).data))     
                HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients'] = []
            except Pad.DoesNotExist:
                HWIOS.ws_realm.pool.subscription['pad'][pad_id] = {'clients':[],'layers':[{'id':self.id,'name':'Unnamed','log':[]}]}
        HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients'].append(client) 
        
        
    def _unsubscribe_client(self, client):
        """Helper function to unsubscribe from a pad pool"""
        if 'pad' in HWIOS.ws_realm.pool.subscription:
            for _pad in HWIOS.ws_realm.pool.subscription['pad']:
                for _client in HWIOS.ws_realm.pool.subscription['pad'][_pad]['clients']: 
                    if _client.profile.uuid == client.profile.uuid:
                        HWIOS.ws_realm.pool.subscription['pad'][_pad]['clients'].remove(_client)
                        for _client in HWIOS.ws_realm.pool.subscription['pad'][_pad]['clients']:
                            _client.remote('/data/pad/'+_pad+'/mouse/leave/', [client.profile.username])
        

    def save_pad(self, client, pad_id):
        """Saves a pad and notify others of this event

        :param Client client: The requesting client
        :param int pad_id: The pad_id of the pad to modify
        :return: dict - Status and html-layout data response
        """
        try:
            pad = Pad.objects.get(slug = pad_id)
            operation_data = HWIOS.ws_realm.pool.subscription['pad'][pad_id].copy()
            del(operation_data['clients'])
            pad.data = HWIOS.tools.json_encode(operation_data)
            pad.save()
            publish_activity(client.profile, _('Pad drawing saved'),'/pad/%s/' % pad_id,[0,2,2,0,0])
        except Pad.DoesNotExist:   
            pad = Pad()
            pad.slug = pad_id
            operation_data = HWIOS.ws_realm.pool.subscription['pad'][pad_id].copy()
            del(operation_data['clients'])
            pad.data = HWIOS.tools.json_encode(operation_data)
            pad.save()
            publish_activity(client.profile, _('Pad drawing created'),'/pad/%s/' % pad_id,[0,2,2,0,0])
        for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']:
            #this client is watching our attempt to create a new article. Send it a request to resubscribe to the article                      
            _client.remote('/views/pad/%s/' % pad_id,{
                'status':{
                    'code':'PAD_SAVED',
                    'i18n':_('%(first_name)s %(last_name)s just saved pad %(pad_id)s!') % {'first_name':client.profile.first_name,'last_name': client.profile.last_name,'pad_id':pad_id},
                    'type': HWIOS.ws_realm._t['notify-info']
                }
            })
        
    def bc_mouse_position(self, client, pad_id, params):
        """Broadcast a client's mouse location to other connected clients
        
        :param Client client: The requesting client
        :param int pad_id: The pad_id to specify the broadcast pool
        """
        params.append(client.profile.username)
        clients = HWIOS.ws_realm.pool.get_clients()
        for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']: 
            if _client != client:                
                _client.remote('/data/pad/'+pad_id+'/mouse/receive/', params)


    def leave_mouse(self, client, pad_id):
        """Flag other clients to hide this client's mouse position, because it's out of bounds

        :param Client client: The requesting client
        :param int pad_id: The pad_id to specify the broadcast pool
        """
        clients = HWIOS.ws_realm.pool.get_clients()
        for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']: 
            if _client != client:                
                _client.remote('/data/pad/'+pad_id+'/mouse/leave/', [client.profile.username])
                
                
    def draw_brush(self, client, pad_id, layer_id, params):
        """Broadcast that the client is drawing a brush. Params looks like:
        [x,y,color,dragging,size,brush_type,delta_time]

        :param Client client: The requesting client
        :param int pad_id: The pad_id to specify the broadcast pool
        :param str layer_id: The id of the layer to draw on
        :param dict params: The parameters that come with drawing a brush.
        """
        params.append(client.profile.username)
        clients = HWIOS.ws_realm.pool.get_clients()
        for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']:  
            if _client != client:                
                _client.remote('/data/pad/'+pad_id+'/layers/'+layer_id+'/draw/brush/', params)  
        self._log2layer(pad_id, layer_id,['brush', params])
        
        
    def draw_shape(self, client, pad_id, layer_id, params):
        """Broadcast that the client is drawing a shape. Params looks like:
        [x[],y[],color[],border,type,layer]

        :param Client client: The requesting client
        :param int pad_id: The pad_id to specify the broadcast pool
        :param str layer_id: The id of the layer to draw on
        :param dict params: The parameters that come with drawing a shape.
        """
        params.append(client.profile.username)
        clients = HWIOS.ws_realm.pool.get_clients()
        for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']: 
            if _client != client:                
                _client.remote('/data/pad/'+pad_id+'/layers/'+layer_id+'/draw/shape/', params)
        self._log2layer(pad_id, layer_id,['shape', params])
        
        
    def draw_text(self, client, pad_id, layer_id, params):
        """Broadcast that the client is drawing text. Params looks like:
        [x,y,color[],border,font,text,layer]

        :param Client client: The requesting client
        :param int pad_id: The pad_id to specify the broadcast pool
        :param str layer_id: The id of the layer to draw on
        :param dict params: The parameters that come with drawing text.
        """
        params.append(client.profile.username)
        clients = HWIOS.ws_realm.pool.get_clients()
        for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']:  
            if _client != client:                
                _client.remote('/data/pad/'+pad_id+'/layers/'+layer_id+'/draw/text/', params)
        print params
        self._log2layer(pad_id, layer_id,['text', params])
        
        
    def draw_fill(self, client, pad_id, layer_id, params):
        """Broadcast that the client is drawing a fill. Params looks like:
        [x,y,color[],border,font,text,layer]

        :param Client client: The requesting client
        :param int pad_id: The pad_id to specify the broadcast pool
        :param str layer_id: The id of the layer to draw on
        :param dict params: The parameters that come with drawing a fill.
        """
        params.append(client.profile.username)
        clients = HWIOS.ws_realm.pool.get_clients()
        for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']:  
            if _client != client:                
                _client.remote('/data/pad/'+pad_id+'/layers/'+layer_id+'/draw/fill/', params)
        self._log2layer(pad_id, layer_id,['fill', params])
                
                
    def clear_pad(self, client, pad_id, params):
        """Broadcast that the client is clearing the whole pad.
        TODO: make it only clear a layer instead

        :param Client client: The requesting client
        :param int pad_id: The pad_id to specify the broadcast pool
        :param dict params: The parameters that come with clearing the pad.
        """
        for _layer in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers']:
            _layer['log'][:] = []
        clients = HWIOS.ws_realm.pool.get_clients()
        publish_activity(client.profile, _('Pad drawing cleared'),'/pad/%s/' % pad_id,[0,2,2,0,0])
        for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']: 
            if _client != client:
                _client.remote('/data/pad/'+pad_id+'/clear/', params)
                
                
    def create_layer(self, client, pad_id, layer_name):
        """Broadcast that the client has created a new layer

        :param Client client: The requesting client
        :param int pad_id: The pad_id to specify the broadcast pool
        :param str layer_name: Name of the layer to create
        """
        exists = False
        for _layer in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers']:
            if _layer['name'] == layer_name:
                exists = True
        if not exists:
            self.id += 1
            HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers'].append({'id':self.id,'name':layer_name,'log':[]})
            clients = HWIOS.ws_realm.pool.get_clients()
            for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']: 
                _client.remote('/data/pad/'+pad_id+'/layers/'+layer_name+'/create/', {
                    'data':{
                        'layer':{
                            'id':self.id,
                            'name':layer_name,
                            'log':[]
                        }
                    }
                })
        
        
    def delete_layer(self, client, pad_id, layer_name):
        """Broadcast that the client has deleted a layer

        :param Client client: The requesting client
        :param int pad_id: The pad_id to specify the broadcast pool
        :param str layer_name: Name of the layer to delete
        """
        exists = False
        deleted = {}
        for count, _layer in enumerate(HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers']):
            if _layer['name'] == layer_name:
                deleted = _layer
                del HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers'][count]
        clients = HWIOS.ws_realm.pool.get_clients()
        for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']: 
            _client.remote('/data/pad/'+pad_id+'/layers/'+layer_name+'/delete/', {'data':{'layer':deleted}})
            
            
    def change_layer_order(self, client, pad_id, layer_id, to_position):
        """Broadcast that the client has changed the ordening of layers.
        HWIOS keeps a serverside mirror of these layer-ordening as well.

        :param Client client: The requesting client
        :param int pad_id: The pad_id to specify the broadcast pool
        :param int to_position: The list-position the layer is supposed to go to
        """
        if to_position >=0 and to_position < len(HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers']):
            for idx, _layer in enumerate(HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers']):
                if _layer['id'] == int(layer_id):
                    _tmplayer = HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers'].pop(idx)
                    HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers'].insert(to_position, _tmplayer)
        clients = HWIOS.ws_realm.pool.get_clients()
        for _client in HWIOS.ws_realm.pool.subscription['pad'][pad_id]['clients']: 
            _client.remote('/data/pad/'+pad_id+'/layers/'+str(layer_id)+'/order/', {'data':{'layers':HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers'],'id':int(layer_id)}})

  
    def _log2layer(self, pad_id, layer_id, action):
        """Small helper that writes the action to the log pool"""
        for idx, _layer in enumerate(HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers']): 
            if _layer['id'] == int(layer_id):
                HWIOS.ws_realm.pool.subscription['pad'][pad_id]['layers'][idx]['log'].append(action)
            
        
