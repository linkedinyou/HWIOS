# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.plasmoids
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The plasmoid module's websocket routing logics

    :copyright: Copyright 2009-2011 OS-Networks.
    :license: BSD, see LICENSE for details.
"""
import os,sys
import uuid as UUID
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
from web_ui.forms.pages import EntityForm, CreateAnchorForm, EditAnchorForm
from web_ui.models.notifications import *
from web_ui.models.activity import *


class WS_Pages(object):
    """
    Websocket controller class for the plasmoid module
    """

    def __init__(self, dispatcher):
        self.infinote_pool = InfinotePool(self)
        dispatcher.signals.subscribe('ws_disconnect', self.disconnect_entity_editor)
        dispatcher.signals.subscribe('view_changed', self.disconnect_entity_editor, filters = [(r'/pages/entities/(?P<uuid>[^/]+)/edit/',True),(r'/pages/entities/(?P<uuid>[^/]+)/edit/',False)])
        

    @WSAuth.is_staff
    def list_pages(self, client):
        """Render the view that shows an overview of all plasmoids

        :param Client client: The requesting client 
        :return: dict - Html-layout data response
        """
        anchors = PageAnchor.objects.all()
        entities = PageEntity.objects.all()
        main = render_to_string("pages/list_pages.html", {'anchors':anchors,'entities':entities})
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
            response = self._try_save_anchor(client, _uuid, form)
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
            HWIOS.anchors.get_routes()
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
    def create_entity(self, client, uuid, form = None):
        """Render and returns the create plasmoid view

        :param Client client: The requesting client
        :return: dict - Data and html-layout response
        """
        if form == None:
            form = EntityForm()
            entity = PageEntity()
            entity.uuid = uuid
            subscriber = self.infinote_pool.subscribe(client, uuid, '', 'entities', self._signal_presence)
            main = render_to_string("pages/create_entity.html",{'entity':entity,'form': form})
            return {
                'data':{
                    'ce':subscriber,
                    'uid': client.profile.pk,
                    'dom':{'main':main},
                }
            }
        else:
            print "PROCESS NEW!"
            _content = form['content']
            del form['content']
            form = EntityForm(form)
            form.content = _content
            response = self._try_save_entity(client, uuid, form)
            return response

        

    @WSAuth.is_staff
    def edit_entity(self, client, uuid, form = None):
        """
        Edit an existing or a new plasmoid. In both cases, the infinote subscription pool defines the plasmoid view, not the model. This makes it
        possible to edit a new plasmoid, that's not yet in the database.

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to edit
        :return: dict - Data and html-layout response
        """
        if form == None:
            try:
                entity = PageEntity.objects.get(pk = uuid)
            except ObjectDoesNotExist:
                entity = PageEntity()
                entity.code = ''
            client.role = 'edit'
            form = EntityForm(initial={'slug':entity.slug,'anchor':entity.anchor,'type':entity.type})
            main = render_to_string("pages/edit_entity.html",{'entity':entity, 'form': form})
            subscriber = self.infinote_pool.subscribe(client, uuid, entity.code, 'entities', self._signal_presence)
            publish_activity(client.profile, _('Entity editing'),'/pages/entities/%s/edit/' % uuid,[0,0,4,0,0])
            return {
                'data':{
                    'ce':subscriber,
                    'uid': client.profile.pk,
                    'dom':{'main':main}
                }
            } 
        else:
            print "PROCESS NEW!"
            _content = form['content']
            del form['content']
            form = EntityForm(form)
            form.content = _content
            response = self._try_save_entity(client, uuid, form)
            return response

        

    @WSAuth.is_staff
    def _try_save_entity(self, client, uuid, form):
        """
        Save an existing or a new plasmoid, render/show the general plasmoid overview and notify others.

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to save
        :return: dict - Status and html-layout response
        """
        if form.is_valid():
            try:
                entity = PageEntity.objects.get(pk = uuid)
                entity.slug = form.cleaned_data['slug']
                entity.anchor = form.cleaned_data['anchor']
                entity.code = form.content
                entity.type = form.cleaned_data['type']
                entity.last_modified = datetime.now()
                entity.save()
                client_response, tpl_params = self._get_pages(client)
                client_response.update({
                    'status':{
                        'code':'ENTITY_EDIT_OK',
                        'i18n':_('Page entity %(slug)s updated...') % {'slug':entity.slug},
                        'type': HWIOS.ws_realm._t['notify-info'],
                        'state': '/pages/',
                    }
                })
            except PageEntity.DoesNotExist:
                entity = PageEntity()
                publish_activity(client.profile, _('Page entity created'),'/pages/entities/%s/edit/' % uuid,[0,0,4,0,0])
                entity.slug = form.cleaned_data['slug']
                entity.anchor = form.cleaned_data['anchor']
                entity.code = form.content
                entity.type = form.cleaned_data['type']
                entity.last_modified = datetime.now()
                entity.save()
                client_response, tpl_params = self._get_pages(client)
                client_response.update({
                    'status':{
                        'code':'ENTITY_CREATE_OK',
                        'i18n':_('Page entity %(slug)s created...') % {'slug':entity.slug},
                        'type': HWIOS.ws_realm._t['notify-info'],
                        'state': '/pages/',
                    }
                })
            
            #UPDATE ROUTES
            HWIOS.anchors.get_routes()
            notify_others(client, client_response,'/pages/entities/modified/', '^/pages/$', tpl_params)
            publish_activity(client.profile, _('Page entity saved'),'/pages/entities/%s/edit/' % uuid,[0,0,4,0,0])
            return client_response
        else:
            try:
                entity = PageEntity.objects.get(pk = uuid)
                main = render_to_string("pages/edit_entity.html", {'entity':entity, "form":form})
            except ObjectDoesNotExist:
                entity = PageEntity()
                entity.slug = _('New Entity')
                entity.uuid = uuid
                main = render_to_string("pages/create_entity.html", {'entity':entity, "form":form})
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
    def delete_entities(self, client, params = None):
        """
        Delete an existing plasmoid from the database and subscription pool, render/show the general plasmoid overview and notify others.

        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to delete
        :return: dict - Status and html-layout response
        """
        if params == None:
            dialog = render_to_string("pages/delete_entity_confirmation.html")
            return {'data':{'dom':{'dialog':dialog}}}
        else:
            _count = 0
            regex_modifier = ''
            for slug in params:
                entity = PageEntity.objects.get(pk=slug)
                entity.delete()
                if regex_modifier != '':
                    regex_modifier = '%s|%s' % (regex_modifier, slug)
                else:
                    regex_modifier = '%s' % slug
                _count +=1
            HWIOS.anchors.get_routes()
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
            notify_others(client, client_response,'/pages/modified/', '^/pages/entities/(%s)/edit/$' % regex_modifier, tpl_params, _target_state)
            notify_others(client, client_response,'/pages/modified/', '^/pages/$', tpl_params, _target_state)
            publish_activity(client.profile, _('Entities deleted'),'/pages/',[0,0,4,0,0])
            return client_response
            


    @WSAuth.is_staff        
    def connect_entity_editor(self, client, uuid):
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
        
        
    def disconnect_entity_editor(self, client, uuid = None):
        """Unsubscribe from the infinote plasmoid pool on certain events like disconnect and view_changed
        
        :param Client client: The requesting client
        :param str plasmoid_uuid: The uuid of the plasmoid to disconnect from the infinote pool
        """
        self.infinote_pool.unsubscribe(client, 'entities', self._signal_presence)

                        
    def request_entity_insert(self, client, uuid, params):
        """Insert operation for a specific plasmoid in the infinote pool

        :param Client client: The requesting client
        :param str uuid: The uuid of the plasmoid to operate on in the infinote pool
        :param dict params: The params that are used to succesfully perform the infinote operation
        """
        self.infinote_pool.request_insert(client,'entities', uuid, params, self._signal_operation)
        
        
    def request_entity_delete(self, client, uuid, params):
        """Delete operation for a specific plasmoid in the infinote pool

        :param Client client: The requesting client
        :param str uuid: The uuid of the plasmoid to operate on in the infinote pool
        :param dict params: The params that are used to succesfully perform the infinote operation
        """
        self.infinote_pool.request_delete(client,'entities', uuid, params, self._signal_operation)
        
        
    def request_entity_undo(self, client, uuid, params):
        """Uno operation for a specific plasmoid in the infinote pool

        :param Client client: The requesting client
        :param str uuid: The uuid of the plasmoid to operate on in the infinote pool
        :param dict params: The params that are used to succesfully perform the infinote operation
        """
        self.infinote_pool.request_undo(client,'entities', uuid, params, self._signal_operation)
        

    def update_remote_caret(self, client, uuid, params):
        """Move caret operation for a specific plasmoid in the infinote pool

        :param Client client: The requesting client
        :param str uuid: The uuid of the plasmoid to operate on in the infinote pool
        :param dict params: The params that are used to succesfully perform the infinote operation
        """
        self.infinote_pool.update_caret(client,'entities', uuid, params, self._signal_caret)
        

    def _signal_presence(self, client, online, app_pool, item_id):
        client.remote('/data/pages/%s/%s/online/update/' % (app_pool, item_id),{'online':online}) 
        
        
    def _signal_operation(self, client, app_pool, item_id, operation_type, params):
        client.remote('/data/pages/%s/%s/%s/' % (app_pool, item_id, operation_type), params)  
        
        
    def _signal_caret(self, client, app_pool, item_id, params):
        client.remote('/data/pages/%s/%s/caret/' % (app_pool, item_id), params)
        

    def _get_pages(self, client):
        """Notify_others helper that renders and prepares the show plasmoids view"""
        anchors = PageAnchor.objects.all()
        entities = PageEntity.objects.all()
        main = render_to_string("pages/list_pages.html", {'anchors':anchors,'entities':entities})
        tpl_params = {'anchors':anchors,'entities':entities}
        main = render_to_string("pages/list_pages.html", tpl_params)
        return [
            {'data':{'dom':{'main':main}}},
            {'main':{'tpl':'pages/list_pages.html','params':tpl_params}}
        ]
        
