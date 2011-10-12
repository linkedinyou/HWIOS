# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.profiles
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The websocket controller for the profiles module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os,sys
import time

from datetime import datetime
from twisted.internet import defer, reactor


from django.template.loader import render_to_string
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _


from core.application import HWIOS
from web_ui.models.ws_auth import WSAuth
from web_ui.models.profiles import Profile
from web_ui.models.notifications import *
from web_ui.models.activity import *
from web_ui.models.settings import Settings

from web_ui.forms.profiles import *


class WS_Profiles(object):
    """
    Websocket controller class for the profiles module
    """
    
    def __init__(self, dispatcher):
        pass


    def get_context(self, client):
        context = render_to_string("profiles/context_menu.html", {'profile':client.profile})
        return {'data':{'dom':{'context':context}}}
        
    
    @WSAuth.is_staff
    def manage_profiles(self, client):
        """Renders the manage profiles view

        :param Client client: The requesting client
        :return: dict - html-layout data response
        """
        profiles = Profile.objects.all()
        main = render_to_string("profiles/manage_profiles.html", {'profiles':Profile.objects.all()})
        return {'data':{'dom':{'main':main}}}
        
        
    @WSAuth.is_staff
    def create_profile(self, client, params = None):
        """Either renders the create-profiles view or handle the creation of a new profile

        :param Client client: The requesting client
        :param dict params: Optional; contains the form parameters
        :return: dict - html-layout data response
        """
        if params == None:
            main = render_to_string("profiles/create_profile.html", {'form':NewProfileForm()})
            return {'data':{'dom':{'main':main}}}
        else:
            form = NewProfileForm(params)
            if form.is_valid():
                profile_data = {'first_name': form.cleaned_data['first_name'], 
                                'last_name': form.cleaned_data['last_name'], 
                                'email': form.cleaned_data['email'], 
                                'password': form.cleaned_data['password'], 
                                'is_staff': form.cleaned_data['is_staff'], 
                                'is_active': form.cleaned_data['is_active'], 
                                'is_superuser': form.cleaned_data['is_superuser'], 
                                'organisation': form.cleaned_data['organisation'], 
                                'timezone': 'Europe/Amsterdam', 
                                'karma': 0, 
                                'ip': client.transport.getPeer().host
                                }
                profile = Profile.objects.create_profile(profile_data, acp = True, client = client)
                client_response, tpl_params = self._get_manage_profiles()
                client_response.update({
                    'status':{
                        'code':'PROFILE_CREATE_OK',
                        'i18n':_('New user created!'),
                        'type': HWIOS.ws_realm._t['notify-info'],
                        'state': '/profiles/manage/',
                    }
                })
                notify_others(client, client_response,'/profiles/manage/modified/', '/profiles/manage/', tpl_params)
                publish_activity(client.profile, _('Profile created'),'/profiles/manage/',[0,0,4,0,0])
                return client_response                
            else:
                main = render_to_string('profiles/create_profile.html', {'form': form})
                return {
                    'status':{
                        'code':'FORM_INVALID',
                        'i18n':_('Please pay attention to the profile details...'),
                        'type': HWIOS.ws_realm._t['notify-warning']
                    },
                    'data':{'dom':{'main':main}}
                }

               
    @defer.inlineCallbacks
    def whois_profile(self, client, username):
        """
        Lookup info about a client
        """
        target_client = HWIOS.ws_realm.pool.get_client(username = username)
        if target_client != None:
            ip = target_client.get_ip()
            hostname = yield target_client.get_hostname()
            geoip = target_client.get_geoip()
        else:
            _ip = _('Unknown')
        main = render_to_string('profiles/whois_profile.html', {'ip': ip,'hostname':hostname,'geoip':geoip,'target_profile':target_client.profile})
        defer.returnValue({'data':{'dom':{'main':main}}})
    

    @WSAuth.is_authenticated
    def edit_profile(self, client, username, params = None):
        """Either renders the edit-profiles view or handle the update to an existing profile

        :param Client client: The requesting client
        :param str profile_name: The profile to change, based on firstname and lastname
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and html-layout data response
        """
        profile = Profile.objects.get(username = username)
        if params == None:
            #users own profile         
            data = {'first_name':profile.first_name, 
                    'last_name':profile.last_name,
                    'username':profile.username,
                    'email':profile.email,
                    'is_active':profile.is_active,
                    'is_staff':profile.is_staff,
                    'is_superuser':profile.is_superuser,
                }
            if client.profile == profile:
                form = EditMyProfileForm(initial={'email': profile.email,'about':profile.about})
            else:
                form = EditProfileForm(initial=data) 
            main = render_to_string('profiles/edit_profile.html', {'form': form, 'profile':client.profile, 'target_profile': profile})
            return {'data':{'dom':{'main':main}}} 
        else:
            if client.profile == profile:
                form = EditMyProfileForm(params)
            else:
                form = EditProfileForm(params)
            #our user sends in an avatar update
            if 'avatar' in params:
                profile = Profile.objects.update_profile(profile.uuid, params, client)                     
                response = {
                    'status':{
                        'code':'AVATAR_UPDATE_OK',
                        'i18n':_('Avatar succesfully updated'),
                        'type': HWIOS.ws_realm._t['notify-info'],
                    },
                    'data':{
                        'avatar':profile.photo
                    }
                }
                return response
            if form.is_valid():
                #try to get client instance for modified profile
                
                _client = HWIOS.ws_realm.pool.get_client(profile.uuid)
                profile = Profile.objects.update_profile(profile.uuid,form.cleaned_data, client)
                #update client profile *if* online
                if _client != None:
                    _client.profile = profile
                
                #we have a two-fold audience: overview => /profiles/manage and edit => /profiles/<some_profile>/edit/                    
                client_edit_response, __tpl_params = self._get_profile(client, profile)
                #profile overview update
                client_overview_response, _tpl_params = self._get_manage_profiles()
                _status = {
                    'status':{
                        'code':'PROFILE_EDIT_OK',
                        'i18n':_('Profile succesfully updated'),
                        'type': HWIOS.ws_realm._t['notify-info'],
                    }
                }
                client_edit_response.update(_status)
                client_overview_response.update(_status)                
                #notify edit this profile viewer
                data = {'first_name':profile.first_name,
                        'last_name':profile.last_name,
                        'username':profile.username,
                        'email':profile.email,
                        'is_active':profile.is_active,
                        'is_staff':profile.is_staff,
                        'is_superuser':profile.is_superuser,
                    }
                if client.profile == profile:
                    form = EditMyProfileForm(initial=data)
                else:
                    form = EditProfileForm(initial=data)
                #notify other editors
                _target_state = '/profiles/%s/edit/' % username
                client_edit_response['status']['state'] = _target_state
                notify_others(
                    client, client_edit_response,
                    '/profiles/manage/modified/',
                    r'^/profiles/%s/edit/$' % username,
                    {'main':{'tpl':'profiles/edit_profile.html','params': {'form':form,'profile':client.profile,'target_profile': profile}}},
                    _target_state
                )
                #notify manage profile viewers
                _target_state = '/profiles/manage/'
                client_overview_response['status']['state'] = _target_state
                notify_others(client, client_overview_response,'/profiles/manage/modified/', r'^/profiles/manage/$', _tpl_params, _target_state)
                if client.profile == profile:
                    publish_activity(client.profile, _('Profile own user change'),'/profiles/manage/',[0,0,1,0,0])
                else:
                    publish_activity(client.profile, _('Profile moderator change'),'/profiles/manage/',[0,0,1,0,0])
                return client_overview_response
            else:
                main = render_to_string("profiles/edit_profile.html", {'form':form,'profile':client.profile, 'target_profile': profile})
                return {
                    'status':{
                        'code':'FORM_INVALID',
                        'i18n':_('Invalid Form!'),
                        'type': HWIOS.ws_realm._t['notify-info']
                    },
                    'data':{'dom':{'main':main}}
                }                    

    
    @WSAuth.is_staff
    def delete_profiles(self, client, params = None):
        """Either renders the delete-profiles confirmation view or handle the deletion of one or more profiles

        :param Client client: The requesting client
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and html-layout data response
        """
        if params == None:
            dialog = render_to_string("profiles/delete_profile_confirmation.html")
            return {'data':{'dom':{'dialog':dialog}}}
        else:
            deleted_list = []
            profile_collide = False
            uuids = params
            regex_modifier = ''
            for uuid in uuids:
                #Prevent removal of user's own profile                
                if client.profile.uuid != uuid:
                    deleted_profile = Profile.objects.delete_profile(uuid, client = client)
                    deleted_list.append({deleted_profile['name']:deleted_profile['status']})
                    _profile_name = deleted_profile['name'].replace(' ', '_')
                    if regex_modifier != '':
                        regex_modifier = '%s|%s' % (regex_modifier, _profile_name)
                    else:
                        regex_modifier = '%s' % _profile_name
                    deleted_profile['name'].split(' ')
                else:
                    profile_collide = True       
            client_response, tpl_params = self._get_manage_profiles()
            _target_state = '/profiles/manage/'
            if not profile_collide:
                client_response.update({
                    'status':{
                        'code':'PROFILE_DELETE_OK',
                        'i18n':_('Succesfully removed %(profiles)s profile(s)!') % {'profiles':len(deleted_list)},
                        'type': HWIOS.ws_realm._t['notify-info'],
                        'state': _target_state,
                    }
                })
            else:
                client_response.update({
                    'status':{
                        'code':'PROFILE_DELETE_OK',
                        'i18n':_('%(profiles)s profile(s) removed succesfully; you can\'t remove your own profile!') % {'profiles':len(deleted_list)},
                        'type': HWIOS.ws_realm._t['notify-info'],
                        'state': _target_state,
                    }
                })
            notify_others(client, client_response,'/profiles/manage/modified/', '^/profiles/(%s)/edit/$' % regex_modifier, tpl_params, _target_state)
            notify_others(client, client_response,'/profiles/manage/modified/', '^/profiles/manage/$', tpl_params, _target_state)
            publish_activity(client.profile, _('Profile deleted'),'/profiles/manage/',[0,0,4,0,0])
            return client_response


    def login_profile(self, client):
        """Renders the login dialog template
        TODO: Currently we only supply the form layout here. Actual login could be done through websockets as well though, but that
        requires manupilation of the django session object, and clientside cookie handling.

        :param Client client: The requesting client
        """        
        form = LoginForm()
        dialog = render_to_string('profiles/login.html', {'form': form})
        response = {'data':{'dom':{'dialog':dialog}}}
        return response
        
        
    def register_profile(self, client, params = None):
        """Either renders the register-dialog view or handle the registration form-request

        :param Client client: The requesting client
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and html-layout data response
        """
        if params == None:
            form = RegisterProfileForm()
            dialog = render_to_string('profiles/register.html', {'form': form})
            client_response = {'data':{'dom':{'dialog':dialog}}}
        else:
            form = RegisterProfileForm(params)
            if form.is_valid():
                profile_data = {'username': form.cleaned_data['username'],
                                'email': form.cleaned_data['email'], 
                                'password': form.cleaned_data['password'], 
                                'is_staff': 0, 
                                'is_active': 0, 
                                'timezone': 'Europe/Amsterdam', 
                                'karma': 0, 
                                'ip': client.transport.getPeer().host
                                }
                profile = Profile.objects.create_profile(profile_data, client = client)
                acp_settings = Settings.objects.all()[0]
                #general return template within the webinterface
                dialog = render_to_string('profiles/registration_complete.html', {'profile': profile, 'activation_type': acp_settings.activation_type})
                client_response, tpl_params = self._get_manage_profiles()
                client_response.update({
                    'status':{'code':'REGISTER_OK',
                    'i18n':_('New account registered'),
                    'type': HWIOS.ws_realm._t['notify-info']
                    }
                })
                notify_others(client, client_response,'/profiles/manage/modified/', '/profiles/manage/', tpl_params)
                publish_activity(profile, _('Profile registered'),'/profiles/manage/',[0,0,1,0,0])
                client_response.update({'data':{'dom':{'dialog':dialog}}})
            else:                
                feedback = 'Invalid form. Please check your credentials...'
                dialog = render_to_string('profiles/register.html', {'form': form})
                client_response = {
                    'status':{
                        'code':'FORM_INVALID',
                        'i18n':_('Invalid form. Please check your credentials...'),
                        'type': HWIOS.ws_realm._t['notify-warning']
                    },
                    'data':{'dom':{'dialog':dialog}}
                }
        return client_response


    def activate_profile(self, client, profile_uuid):
        """Try to set the profile to active, or return a notification that the profile is already active

        :param Client client: The requesting client
        :param str profile_uuid: The profile's uuid to use
        :return: dict - Status and html-layout data response
        """
        activated_profile = Profile.objects.activate_profile(profile_uuid)
        if activated_profile:
            from web_ui.models.settings import Settings
            from django.core import mail
            acp_settings = Settings.objects.all()[0]
            dialog = render_to_string('profiles/registration_user_approved.html', {'profile': activated_profile, 'host': client.transport.getPeer().host})
            response = {
                'status':{
                    'code':'PROFILE_ACTIVATED',
                    'i18n':_('Your account has been activated...'),
                    'type': HWIOS.ws_realm._t['notify-info']
                },
                'data':{'dom':{'dialog':dialog}}
            }
            publish_activity(activated_profile, _('Profile activated'),'/profiles/manage/',[0,0,1,0,0])
        else:
            response = {
                'status':{
                    'code':'PROFILE_ALREADY_ACTIVATED',
                    'i18n':_('This account is already active...'),
                    'type': HWIOS.ws_realm._t['notify-info']
                }
            }
        return response
    
    
    def view_profile(self, client, username):
        """View a profile's details, whether it's our own profile or another profile is determined in the template

        :param Client client: The requesting client
        :param str profile_name: The profile's username to use
        :return: dict - Status and html-layout data response
        """
        profile = Profile.objects.get(username = username)
        main = render_to_string('profiles/view_profile.html', {'target_profile': profile,'profile':client.profile})
        return {'data':{'dom':{'main':main}}}
            
        
    def _get_manage_profiles(self):
        """
        Small helper function that returns template and html-layout references of all profiles,
        that work well with the notify-others action
        """
        profiles = Profile.objects.all()
        main = render_to_string("profiles/manage_profiles.html", {'profiles':profiles})
        tpl_params = {'profiles':profiles}
        return [
            {'data':{'dom':{'main':main}}},
            {'main':{'tpl':'profiles/manage_profiles.html','params':tpl_params}}
        ]
        
        
    def _get_profile(self, client, profile):
        """
        Small helper function that returns template and html-layout references to a profile,
        that work well with the notify-others action
        """
        tpl_params = {'profile':profile}
        main = render_to_string('profiles/view_profile.html', tpl_params)
        return [
            {'data':{'dom':{'main':main}}},
            {'main':{'tpl':'profiles/view_profile.html','params':tpl_params}}
        ]
