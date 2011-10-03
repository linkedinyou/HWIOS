# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The websocket logics for HWIOS settings

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import os,sys
import math
from django.core import serializers
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from core.application import HWIOS
from web_ui.models.ws_auth import WSAuth
from web_ui.models.profiles import Profile
from web_ui.models.settings import Settings
from web_ui.models.notifications import *
from web_ui.models.activity import *
from web_ui.forms.settings import GeneralSettingsForm


class WS_Settings(object):
    """Websocket controller class for HWIOS settings"""
    
    def __init__(self, dispatcher):
        pass
    
    
    @WSAuth.is_staff
    def load_settings(self, client):
        """Renders the settings template for this client

        :param Client client: The requesting client
        :return: dict - Html-layout data response
        """
        response = {'status':{}}
        general_form = GeneralSettingsForm(instance=Settings.objects.all()[0])        
        main = render_to_string("settings/read_settings.html", {'general_form':general_form})
        return {'data':{'dom':{'main':main}}}
        
            
    @WSAuth.is_staff        
    def save_settings(self,client, params):
        """Handles saving of the settings and gettings the settings view again

        :param Client client: The requesting client
        :param dict params: The form-parameters from the settings view
        :return: dict - Status and html-layout data response
        """
        general_form = GeneralSettingsForm(params, instance=Settings.objects.all()[0])        
        if general_form.is_valid(): 
            general_form.save()
            client_response, tpl_params = self._get_settings(client, params)
            client_response.update({
                'status':{
                    'code':'SETTINGS_UPDATE_OK',
                    'i18n':_('Settings succesfully updated'),
                    'type': HWIOS.ws_realm._t['notify-info']
                }
            })
            print tpl_params
            notify_others(client, client_response,'/settings/modified/', r'^/settings/$', tpl_params)
            publish_activity(client.profile, _('Settings updated'),'/settings/',[0,0,4,0,0])
        else: 
            client_response.update({'status':{
                'code':'INVALID_FORM',
                'i18n':_('invalid form'),
                'type': HWIOS.ws_realm._t['notify-warning']
                }
            })
        return client_response
        

    def _get_settings(self, client, params):
        """Notify_others helper gets the general settings view"""
        general_form = GeneralSettingsForm(params, instance=Settings.objects.all()[0])    
        tpl_params = {'general_form':general_form}
        main = render_to_string("settings/read_settings.html", tpl_params)
        return [
            {'data':{'dom':{'main': main}}},
            {'main':{'tpl':'settings/read_settings.html','params':tpl_params}}
        ]
