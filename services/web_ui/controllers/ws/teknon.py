# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.teknon
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The websocket controller for the teknon service module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os,sys
from twisted.internet import defer

from django.contrib.auth.models import User
from django.core import serializers
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from hwios.core.application import HWIOS
from web_ui.forms.teknon import BackendOnlineServiceIniForm, BackendOfflineServiceIniForm, SERVICE_TYPES
from web_ui.models.ws_auth import WSAuth
from web_ui.models.notifications import *
from web_ui.models.activity import *

import web_ui.settings as settings


class WS_Teknon(object):
    """
    Websocket controller class for the teknon service module
    """
    
    console_subscribers = {}
    service_values = { 
    'SERVICE_STARTING': _('Service is starting...'),
    'SERVICE_ACTIVE': _('Service is already running...'),
    'SERVICE_INACTIVE': _('Service is not running...'),
    'SERVICE_CLOSING': _('Service is shutting down...'),
    'SERVICE_KILLING': _('Service is forced to shutdown...'),
    'SERVICE_UNKNOWN': _('Client doesn\'t know about this service...'),
    'SERVICE_BAD_OPTION': _('Invalid switch option...'),
    }    
    
    def __init__(self, dispatcher):
        pass
    
    
    @WSAuth.is_staff
    def view_pool(self, client):
        """Renders the service pool view

        :param Client client: The requesting client
        :return: dict - html-layout data response
        """
        clients = HWIOS.pb_server.get_clients()
        main = render_to_string("teknon/read_pool.html", {'clients':clients, 'service_types':SERVICE_TYPES})
        return {'data':{'dom':{'main':main}}}
        
        
    @WSAuth.is_staff
    def confirm_start_services(self, client):
        """Renders confirmation of starting services dialog view

        :param Client client: The requesting client
        :return: dict - html-layout data response
        """
        dialog = render_to_string("teknon/start_services_confirmation.html")
        return {'data':{'dom':{'dialog':dialog}}}


    @WSAuth.is_staff
    def confirm_stop_services(self, client):
        """Renders confirmation of stopping services dialog view

        :param Client client: The requesting client
        :return: dict - html-layout data response
        """
        dialog = render_to_string("teknon/stop_services_confirmation.html")
        return {'data':{'dom':{'dialog':dialog}}}
        

    @WSAuth.is_staff
    def confirm_kill_services(self, client):
        """Renders confirmation of killing services dialog view

        :param Client client: The requesting client
        :return: dict - html-layout data response
        """
        dialog = render_to_string("teknon/kill_services_confirmation.html")
        return {'data':{'dom':{'dialog':dialog}}}
        

    service_values = { 
    'SERVICE_STARTING': _('Service is starting...'),
    'SERVICE_ACTIVE': _('Service is already running...'),
    'SERVICE_INACTIVE': _('Service is not running...'),
    'SERVICE_CLOSING': _('Service is shutting down...'),
    'SERVICE_KILLING': _('Service is forced to shutdown...'),
    'SERVICE_UNKNOWN': _('Client doesn\'t know about this service...'),
    'SERVICE_BAD_OPTION': _('Invalid switch option...'),
    }    


    @defer.inlineCallbacks
    def switch_services(self, client, services, to_state):
        """Handle request to switch services on or off

        :param Client client: The requesting client
        :param list services: A list of service uuid's to process
        :param str to_state: The state to switch the service to (ON,OFF,KILL)
        :return: dict - html-layout data response
        """
        response = {'status':{}, 'data':{'start': 0,'stop':0,'kill':0}}
        for count,service_uuid in enumerate(services):
            pb_client = HWIOS.pb_server.search_client(service_uuid)
            result = yield pb_client.switch_service(service_uuid,to_state)
            if result['status']['code'] == 'SERVICE_STARTING': response['data']['start'] += 1
            elif result['status']['code'] == 'SERVICE_CLOSING': response['data']['stop'] += 1
            elif result['status']['code'] == 'SERVICE_KILLING': response['data']['kill'] += 1    
        response['status']['i18n'] = 'Service status:<br/>Started:%s, Stopped:%s, Killed:%s' % (response['data']['start'],response['data']['stop'],response['data']['kill'])
        result['status']['type'] = HWIOS.ws_realm._t['notify-info']
        print response
        defer.returnValue(response)
        
        
    @defer.inlineCallbacks
    def switch_watchdog(self, client, services, status):
        """Handle request to switch service watchdog on or off

        :param Client client: The requesting client
        :param list services: A list of service uuid's to process
        :param str status: The status to switch the service watchdog to (ON,OFF,TRIGGER)
        :return: dict - html-layout data response
        """
        response = []
        for count,service_uuid in enumerate(services):
            pb_client = HWIOS.pb_server.search_client(service_uuid)
            result = yield pb_client.switch_watchdog(service_uuid,status)
            response.append(result)
        if len(services) == 1: 
            defer.returnValue(response[0])
        else: defer.returnValue(response)


    def subscribe_console(self, client,services):
        """Add client to the pb-client-service subscriber pool

        :param Client client: The requesting client
        :param list services: A list of service uuid's to process
        :return: dict - html-layout data response
        """
        response = []
        for count,service_uuid in enumerate(services):
            pb_client = HWIOS.pb_server.search_client(service_uuid)
            service = HWIOS.pb_server.search_service(service_uuid)
            if service_uuid not in self.console_subscribers: self.console_subscribers[service_uuid] = []
            self.console_subscribers[service_uuid].append(client)
            response.append({'data':{'client':'%s:%s' % (service['client'].peer.host,service['client'].peer.port),'service':service['service']}})
        if len(services) == 1: return response[0]
        else: return response


    def unsubscribe_console(self, client,services):
        """Removes client from the pb-client-service subscriber pool

        :param Client client: The requesting client
        :param list services: A list of service uuid's to process
        :return: dict - data response
        """
        response = []
        for count,service_uuid in enumerate(services):
            for count, subscribed_client in enumerate(self.console_subscribers[service_uuid]):
                if subscribed_client == client:
                    del self.console_subscribers[service_uuid][count]
                    service = HWIOS.pb_server.search_service(service_uuid)
                    response.append({'data':{'client':'%s:%s' % (service['client'].peer.host,service['client'].peer.port),'service':service['service']}})
        if len(services) == 1: return response[0]
        else: return response
        
        
    @defer.inlineCallbacks
    def send_service_command(self, client, service_uuid, command):
        """Sends a console command to the appropriate service

        :param Client client: The requesting client
        :param str service_uuid: The uuid of the service to target
        :param str command: The command to send to the service's stdin
        :return: dict - data response from teknon service
        """

        pb_client = HWIOS.pb_server.search_client(service_uuid)
        print type(command)
        result = yield pb_client.command_service(service_uuid, command)
        if result['status']['code'] != "COMMAND_OK":
            result['status']['i18n'] = _('An error occured!')
            result['status']['type'] = HWIOS.ws_realm._t['notify-error']
        defer.returnValue(result)
        
        
    @defer.inlineCallbacks
    def edit_sim_slave_ini(self, client, service_uuid):
        """Renders the opensim's simulator ini view

        :param Client client: The requesting client
        :param str service_uuid: The uuid of the service to target
        :return: dict - html-layout data response
        """
        response = {}
        for count,service_uuid in enumerate(services):
            pb_client = HWIOS.pb_server.search_client(service_uuid)
            user_settings = yield pb_client.get_sim_slave_ini(service_uuid)
            service = HWIOS.pb_server.search_service(service_uuid)['service']
            if service['status'] == 'OFF':
                user_settings_form = OfflineServiceIniForm(initial={'user_settings': user_settings})
            else:
                user_settings_form = OnlineServiceIniForm(initial={'user_settings': user_settings})
        
        main = render_to_string("teknon/slave_ini.html", {'service': service,'form':user_settings_form})
        response.update({'dom':{'main':main}})
        defer.returnValue(response)


    @defer.inlineCallbacks
    def save_sim_slave_ini(self, client, service_uuid):
        """Save the changes to the opensim's simulator ini and render the general service pool

        :param Client client: The requesting client
        :param str service_uuid: The uuid of the service to target
        :return: dict - Status and html-layout data response
        """
        response = {'status':{}}
        for count,service_uuid in enumerate(services):
            pb_client = HWIOS.pb_server.search_client(service_uuid)
            result = yield pb_client.save_slave_sim_ini(service_uuid,data)
            response.update(result)
            if response['status']['code'] == 'CONFIG_SAVED':
                response['status']['i18n'] = _('Succesfully modified service configuration. Restart the service in order to test your custom settings...')
                response['status']['type'] = HWIOS.ws_realm._t['notify-info']
            elif response['status']['code'] == 'CONFIG_SAVED_OFFLINE':
                response['status']['i18n'] = _('Succesfully modified service configuration. Start the service in order to test your custom settings...')
                response['status']['type'] = HWIOS.ws_realm._t['notify-info']
            elif response['status']['code'] == 'CONFIG_SAVED_RESTARTING':
                response['status']['i18n'] = _('Succesfully modified online service configuration. The service will now be restarted...')
                response['status']['type'] = HWIOS.ws_realm._t['notify-info']
            else: 
                response['status']['i18n'] = _('Failed to modify configuration...')
                response['status']['type'] = HWIOS.ws_realm._t['notify-error']
        clients = HWIOS.pb_server.get_clients()
        main = render_to_string("teknon/read_pool.html", {'clients':clients, 'service_types':settings.SERVICE_TYPES})
        response.update({'dom':{'main':main}})
        defer.returnValue(response)
        
            
    def proxy_service_stdout(self, service_uuid, output):
        """Send the dsm-server dispatched stdout from teknon service-consoles to all subscribed ws-clients

        :param str service_uuid: The uuid of the service to target
        :param str output: The stdout from the service
        """
        if service_uuid in self.console_subscribers:
            for client in self.console_subscribers[service_uuid]:
                client.remote('/data/teknon/services/%s/console/update/' % service_uuid,{'output':output})
                

    def update_service_state(self, services):
        """Push a notification to ws-clients when a teknon-controlled service changes it status

        :param dict services: A collection of the services that have changed
        :return: dict - Status and data response
        """
        clients = HWIOS.ws_realm.pool.get_clients('moderators')        
        publish_activity(None, _('Service status changed'),'/teknon/',[0,0,4,0,0])
        for _client in clients:
            if '/teknon/' in _client.transport.view_history[-1]:
                _client.remote('/data/teknon/services/state/update/',{
                    'status':{
                        'code':'SERVICE_STATUS_UPDATE',
                        'i18n':_('A service changed it\'s status'),
                        'type': HWIOS.ws_realm._t['notify-info']
                    },
                    'services':services
                })

    
    def update_view(self):
        """Routes an update of the service pool view from the dsm-server, when a service state-change has been detected
        TODO: Move to notify_others
        """
        clients = HWIOS.ws_realm.pool.get_clients('moderators')
        pb_clients = HWIOS.pb_server.get_clients()
        main = render_to_string("teknon/read_pool.html", {'clients':pb_clients, 'service_types':SERVICE_TYPES})
        publish_activity(None, _('Service pool changed'),'/teknon/',[0,0,4,0,0])
        for _client in clients:
            if '/teknon/' in _client.transport.view_history[-1]:                
                _client.remote('/data/teknon/',{'data':{'dom':{'main':main}}})
        