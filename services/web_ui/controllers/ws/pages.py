# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.plasmoids
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The plasmoid module's websocket routing logics

    :copyright: Copyright 2009-2011 OS-Networks.
    :license: BSD, see LICENSE for details.
"""
import os,sys
import uuid
from datetime import datetime
from twisted.internet import defer
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist

from core.application import HWIOS
from web_ui.models.ws_auth import WSAuth
from web_ui.models.pages import PageAnchor, PageEntity
from web_ui.models.infinote import InfinoteEditor, InfinotePool
from web_ui.forms.pages import CreateEntityForm, EditEntityForm, CreateAnchorForm, EditAnchorForm
from web_ui.models.notifications import *
from web_ui.models.activity import *


class WS_Pages(object):
    """
    Websocket controller class for the plasmoid module
    """

    def __init__(self, dispatcher):
        self.infinote_pool = InfinotePool(self)
        dispatcher.signals.subscribe('ws_disconnect', self.disconnect_plasmoid_editor)
        dispatcher.signals.subscribe('view_changed', self.disconnect_plasmoid_editor, filters = [(r'/plasmoids/(?P<plasmoid_uuid>[^/]+)/edit/',True),(r'/plasmoids/(?P<plasmoid_uuid>[^/]+)/edit/',False)])
        

    @WSAuth.is_staff
    def list_pages(self, client):
        """Render the view that shows an overview of all plasmoids

        :param Client client: The requesting client 
        :return: dict - Html-layout data response
        """
        pages = PageAnchor.objects.all()
        main = render_to_string("pages/list_pages.html", {'pages':pages})
        return {'data':{'dom':{'main':main}}}


    @WSAuth.is_staff
    def create_anchor(self, client, form = None):
        """Render and returns the create plasmoid view

        :param Client client: The requesting client
        :return: dict - Data and html-layout response
        """
        if form == None:
            form = CreateAnchorForm()
            page = PageAnchor()
            main = render_to_string("pages/create_anchor.html",{'page':page,'form': form})
            return {
                'data':{
                    'dom':{'main':main},
                }
            }
        else:
            _uuid = str(uuid.uuid4())
            form = CreateAnchorForm(form)
            response = self._try_save_page(client, _uuid, form)
            return response


    @WSAuth.is_staff
    def edit_anchor(self, client, uuid, form = None):
        """
        Edit an existing or a new plasmoid. In both cases, the infinote subscription pool defines the plasmoid view, not the model. This makes it
        possible to edit a new plasmoid, that's not yet in the database.

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to edit
        :return: dict - Data and html-layout response
        """
        if form == None:
            try:
                page = PageAnchor.objects.get(pk = uuid)
            except ObjectDoesNotExist:
                return {
                    'status':{
                        'code':'PAGE_INVALID',
                        'i18n':_('Invalid page!'),
                        'type': HWIOS.ws_realm._t['notify-error'],
                    }
                }
            client.role = 'edit'
            form = EditAnchorForm(initial={'slug':page.slug,'target':page.target,'access':page.access})
            main = render_to_string("pages/edit_anchor.html",{'page':page, 'form': form})
            #subscriber = self.infinote_pool.subscribe(client, plasmoid_uuid, plasmoid.script, 'plasmoids', self._signal_presence)
            publish_activity(client.profile, _('Page editing'),'/pages/%s/edit/' % uuid,[0,0,4,0,0])
            return {
                'data':{
                    'dom':{'main':main}
                }
            }
        else:
            form = EditAnchorForm(form)
            response = self._try_save_anchor(client, uuid, form)
            return response



    @WSAuth.is_staff
    def delete_anchors(self, client, params = None):
        """
        Delete an existing plasmoid from the database and subscription pool, render/show the general plasmoid overview and notify others.

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to delete
        :return: dict - Status and html-layout response
        """
        if params == None:
            dialog = render_to_string("pages/delete_anchor_confirmation.html")
            return {'data':{'dom':{'dialog':dialog}}}
        else:
            _count = 0
            regex_modifier = ''
            for slug in params:
                page = PageAnchor.objects.get(pk=slug)
                page.delete()
                if regex_modifier != '':
                    regex_modifier = '%s|%s' % (regex_modifier, slug)
                else:
                    regex_modifier = '%s' % slug
                _count +=1
            HWIOS.pages.get_routes()
            client_response, tpl_params = self._get_pages(client)
            _target_state = '/pages/'
            client_response.update({
                'status':{
                    'code':'DELETE_OK',
                    'i18n':_('%s page(s) deleted...' % _count),
                    'type': HWIOS.ws_realm._t['notify-info'],
                    'state': _target_state,
                }
            })
            notify_others(client, client_response,'/pages/modified/', '^/pages/(%s)/edit/$' % regex_modifier, tpl_params, _target_state)
            notify_others(client, client_response,'/pages/modified/', '^/pages/$', tpl_params, _target_state)
            publish_activity(client.profile, _('Page(s) deleted'),'/pages/',[0,0,4,0,0])
            return client_response
            
            

    @WSAuth.is_staff
    def _try_save_anchor(self, client, uuid, form):
        """
        Save an existing or a new page, render/show the general plasmoid overview and notify others.

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to save
        :return: dict - Status and html-layout response
        """
        if form.is_valid():
            try:
                page = PageAnchor.objects.get(pk = uuid)
            except PageAnchor.DoesNotExist:
                page = PageAnchor()
                publish_activity(client.profile, _('Page created'),'/pages/%s/edit/' % uuid,[0,0,4,0,0])
            page.slug = form.cleaned_data['slug']
            page.target = form.cleaned_data['target']
            page.access = int(form.cleaned_data['access'])
            page.last_modified = datetime.now()
            page.save()

            client_response, tpl_params = self._get_pages(client)
            #UPDATE ROUTES
            #HWIOS.pages.get_routes()
            client_response.update({
                'status':{
                    'code':'PAGE_EDIT_OK',
                    'i18n':_('Page %(slug)s stored...') % {'slug':page.slug},
                    'type': HWIOS.ws_realm._t['notify-info'],
                }
            })
            #notify_others(client, client_response,'/plasmoids/modified/', '^/plasmoids/$', tpl_params)
            #publish_activity(client.profile, _('Plasmoid saved'),'/plasmoids/%s/edit/' % plasmoid_uuid,[0,0,4,0,0])
            return client_response
        else:
            try:
                page = PageAnchor.objects.get(pk = uuid)
                main = render_to_string("pages/edit_anchor.html", {'page':page, "form":form})
            #new
            except ObjectDoesNotExist:
                page = PageAnchor()
                main = render_to_string("pages/create_anchor.html", {'form':form})
            response = {
                'status':{
                    'code':'FORM_INVALID',
                    'i18n':_('Invalid Form!'),
                    'type': HWIOS.ws_realm._t['notify-warning']
                },
                'data':{'dom':{'main':main}}
            }
            return response

                

    @WSAuth.is_staff
    def create_entity(self, client, form = None):
        """Render and returns the create plasmoid view

        :param Client client: The requesting client
        :return: dict - Data and html-layout response
        """
        if form == None:
            form = CreateEntityForm()
            page = PageEntity()
            main = render_to_string("pages/create_entity.html",{'page':page,'form': form})
            return {
                'data':{
                    'dom':{'main':main},
                }
            }
        else:
            _uuid = str(uuid.uuid4())
            form = CreateAnchorForm(form)
            response = self._try_save_page(client, _uuid, form)
            return response

        

    @WSAuth.is_staff
    def edit_entity(self, client, plasmoid_uuid):
        """
        Edit an existing or a new plasmoid. In both cases, the infinote subscription pool defines the plasmoid view, not the model. This makes it
        possible to edit a new plasmoid, that's not yet in the database.

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to edit
        :return: dict - Data and html-layout response
        """
        try:
            plasmoid = Plasmoid.objects.get(pk = plasmoid_uuid)
        except ObjectDoesNotExist:
            plasmoid = Plasmoid()
        client.role = 'edit'
        form = EditPlasmoidForm(initial={'slug':plasmoid.slug,'target':plasmoid.target,'visible':plasmoid.visible})
        main = render_to_string("plasmoids/edit_plasmoid.html",{'plasmoid':plasmoid, 'form': form})
        subscriber = self.infinote_pool.subscribe(client, plasmoid_uuid, plasmoid.script, 'plasmoids', self._signal_presence)
        publish_activity(client.profile, _('Plasmoid editing'),'/plasmoids/%s/edit/' % plasmoid_uuid,[0,0,4,0,0])
        return {
            'data':{
                'page':subscriber,
                'uid': client.profile.pk,
                'online':subscriber['online'],
                'dom':{'main':main}
            }
        }
        

    @WSAuth.is_staff
    def save_entity(self, client, plasmoid_uuid, form):
        """
        Save an existing or a new plasmoid, render/show the general plasmoid overview and notify others.

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to save
        :return: dict - Status and html-layout response
        """
        _content = form['content']
        del form['content']
        form = EditPlasmoidForm(form)
        if form.is_valid():
            try:
                plasmoid = Plasmoid.objects.get(pk = plasmoid_uuid)
            except Plasmoid.DoesNotExist:
                plasmoid = Plasmoid()
                publish_activity(client.profile, _('Plasmoid created'),'/plasmoids/%s/edit/' % plasmoid_uuid,[0,0,4,0,0])
            plasmoid.slug = form.cleaned_data['slug']
            plasmoid.script = _content
            plasmoid.type = form.cleaned_data['type']
            plasmoid.target = form.cleaned_data['target']
            plasmoid.visible = int(form.cleaned_data['visible'])
            plasmoid.last_modified = datetime.now()
            plasmoid.save()

            client_response, tpl_params = self._get_plasmoids(client)
            #UPDATE ROUTES
            HWIOS.plasmoids.get_routes()
            client_response.update({
                'status':{
                    'code':'PLASMOID_EDIT_OK',
                    'i18n':_('Plasmoid %(slug)s stored...') % {'slug':plasmoid.slug},
                    'type': HWIOS.ws_realm._t['notify-info'],
                }
            })
            notify_others(client, client_response,'/plasmoids/modified/', '^/plasmoids/$', tpl_params)
            publish_activity(client.profile, _('Plasmoid saved'),'/plasmoids/%s/edit/' % plasmoid_uuid,[0,0,4,0,0])
            return client_response
        else:
            try:
                plasmoid = Plasmoid.objects.get(pk = plasmoid_uuid)
            except ObjectDoesNotExist:
                plasmoid = Plasmoid()
            main = render_to_string("plasmoids/edit_plasmoid.html", {'plasmoid':plasmoid, "form":form})
            response = {
                'status':{
                    'code':'FORM_INVALID',
                    'i18n':_('Invalid Form!'),
                    'type': HWIOS.ws_realm._t['notify-warning']
                },
                'data':{'dom':{'main':main}}
            }
            return response
            


    @WSAuth.is_staff        
    def connect_plasmoid_editor(self, client, plasmoid_uuid):
        """
        Legacy code that's a bit redundant now. Problem was that we didn't want regular users to edit shared js-code. Will be revived
        later to add some interactivity to the pad' presentation functionality

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to connect to
        :return: dict - Data and html-layout response
        """
        try:
            hdjs_text = HDJS.objects.get(slug=plasmoid_uuid)   
        except ObjectDoesNotExist:
            hdjs_text = ''
        client.role = 'edit'
        subscriber = self.infinote_pool.subscribe(client, plasmoid_uuid, hdjs_text, 'plasmoids', self._signal_presence)
        return {'data':{'page':subscriber, 'uid': client.profile.pk,'online':subscriber['online']}}
        
        
    def disconnect_plasmoid_editor(self, client, plasmoid_uuid = None):
        """Unsubscribe from the infinote plasmoid pool on certain events like disconnect and view_changed
        
        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to disconnect from the infinote pool
        """
        self.infinote_pool.unsubscribe(client, 'plasmoids', self._signal_presence)

                        
    def request_plasmoid_insert(self, client, plasmoid_uuid, params):
        """Insert operation for a specific plasmoid in the infinote pool

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to operate on in the infinote pool
        :param dict params: The params that are used to succesfully perform the infinote operation
        """
        self.infinote_pool.request_insert(client,'plasmoids', plasmoid_uuid, params, self._signal_operation)
        
        
    def request_plasmoid_delete(self, client, plasmoid_uuid, params):
        """Delete operation for a specific plasmoid in the infinote pool

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to operate on in the infinote pool
        :param dict params: The params that are used to succesfully perform the infinote operation
        """
        self.infinote_pool.request_delete(client,'plasmoids', plasmoid_uuid, params, self._signal_operation)
        
        
    def request_plasmoid_undo(self, client, plasmoid_uuid, params):
        """Uno operation for a specific plasmoid in the infinote pool

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to operate on in the infinote pool
        :param dict params: The params that are used to succesfully perform the infinote operation
        """
        self.infinote_pool.request_undo(client,'plasmoids', plasmoid_uuid, params, self._signal_operation)
        

    def update_remote_caret(self, client, plasmoid_uuid, params):
        """Move caret operation for a specific plasmoid in the infinote pool

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to operate on in the infinote pool
        :param dict params: The params that are used to succesfully perform the infinote operation
        """
        self.infinote_pool.update_caret(client,'plasmoids', plasmoid_uuid, params, self._signal_caret)
        

    def _signal_presence(self, client, online, app_pool, item_id):
        client.remote('/data/%s/%s/online/update/' % (app_pool, item_id),{'online':online}) 
        
        
    def _signal_operation(self, client, app_pool, item_id, operation_type, params):
        client.remote('/data/%s/%s/%s/' % (app_pool, item_id, operation_type), params)  
        
        
    def _signal_caret(self, client, app_pool, item_id, params):
        client.remote('/data/%s/%s/caret/' % (app_pool, item_id), params)    
        

    def _get_pages(self, client):
        """Notify_others helper that renders and prepares the show plasmoids view"""
        pages = PageAnchor.objects.all()
        tpl_params = {"pages":pages}
        main = render_to_string("pages/list_pages.html", {'pages':pages})
        return [
            {'data':{'dom':{'main':main}}},
            {'main':{'tpl':'pages/list_pages.html','params':tpl_params}}
        ]
        
