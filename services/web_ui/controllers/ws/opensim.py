# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.opensim
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The websocket controller for the wiki module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os,sys,uuid,time, uuid, random, hashlib
from datetime import datetime
import pymysql

from twisted.internet import defer, reactor
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.db import models
from django.db import connections
from django.core.exceptions import ObjectDoesNotExist

from core.application import HWIOS
from web_ui.models.ws_auth import WSAuth
from web_ui.models.opensim import Simulators, Luggage, Regions, Scenes, Maps

from web_ui.models.profiles import Profile
from web_ui.forms.opensim import RegionForm, BackupRegionForm, LoadSceneForm, UploadSceneForm, BackupLuggageForm, LoadLuggageForm, UploadLuggageForm, SimulatorSettingsForm, MapSettingsForm

from web_ui.models.notifications import *
from web_ui.models.activity import *



class OSauth(models.Model):
    """Representation of vanilla Opensim's auth table"""
    connection_name="grid"

    UUID = models.CharField(primary_key=True, max_length=36, unique = True,db_column='UUID')
    passwordHash = models.CharField(max_length=32)
    passwordSalt = models.CharField(max_length=32)
    webLoginKey = models.CharField(max_length=36,default='00000000-0000-0000-0000-000000000000')

    class Meta:
        db_table = 'auth'
        app_label = 'core'
        managed = False


class OSUserAccounts(models.Model):
    """Representation of vanilla Opensim's user account table"""
    connection_name="grid"

    PrincipalID = models.OneToOneField(OSauth, primary_key=True, db_column='PrincipalID', null=True)
    ScopeID = models.CharField(max_length=36, unique = True,default='00000000-0000-0000-0000-000000000000')
    FirstName = models.CharField(max_length=64)
    LastName = models.CharField(max_length=64)
    Email = models.EmailField(max_length=64)
    ServiceURLS = models.TextField(default='HomeURI= GatekeeperURI= InventoryServerURI= AssetServerURI=')
    Created = models.IntegerField(default=time.time())
    UserLevel = models.IntegerField(default=0)
    UserFlags = models.IntegerField(default=0)
    UserTitle = models.CharField(max_length=64)

    class Meta:
        db_table = 'UserAccounts'
        app_label = 'core'
        managed = False


class OSinventoryfolders(models.Model):
    """Representation of vanilla Opensim's inventory table"""
    connection_name="grid"

    foldername = models.CharField(max_length=64,default="My Inventory")
    type = models.IntegerField(default=9)
    version = models.IntegerField(default=1)
    folderID = models.CharField(primary_key=True, max_length=36,db_column='folderID')
    agentID = models.CharField(max_length=36)
    parentFolderID = models.CharField(max_length=36,default='00000000-0000-0000-0000-000000000000')

    class Meta:
        db_table = 'inventoryfolders'
        app_label = 'core'
        managed = False
        
        
class WS_OpenSim(object):
    """Websocket handler for the opensim module."""
    
    def __init__(self, dispatcher):
        dispatcher.signals.subscribe('profile_changed', self.change_avatar)
        dispatcher.signals.subscribe('profile_created', self.change_avatar)
        dispatcher.signals.subscribe('profile_deleted', self.delete_avatar)

    
    def change_avatar(self, client, profile):
        """After hwios changes the profile, this observer takes care of updating the opensim profile.
        
        :param Client client: The requesting client
        :param Profile profile: The profile that got updated
        """
        #check if grid db exists first. For now use pymysql handling(so, mysql only for now)
        try:            
            cursor = connections['grid'].cursor()
        except pymysql.err.InternalError:
            return False            
        try:
            osprofile = OSUserAccounts.objects.using('grid').get(PrincipalID = profile.uuid)            
            osauth=OSauth.objects.using('grid').get(UUID=profile.uuid)
            osauth.passwordSalt = profile.salt
            osauth.passwordHash = profile.password
            osauth.save()
            
            osprofile.FirstName = profile.first_name
            osprofile.LastName = profile.last_name
            osprofile.Email = profile.email
            osprofile.save()
        except ObjectDoesNotExist:
            #a user with this name already exist
            try:
                osprofile = OSUserAccounts.objects.using('grid').get(FirstName=profile.first_name, LastName=profile.last_name)
                self.delete_avatar(client, profile.uuid)
            except ObjectDoesNotExist:
                pass
            try:
                osauth=OSauth.objects.create(UUID=profile.uuid, passwordHash= profile.password, passwordSalt = profile.salt)
                osprofile = OSUserAccounts.objects.using('grid').create(PrincipalID=osauth, FirstName=profile.first_name, LastName=profile.last_name, Email=profile.email)
                osfolder = OSinventoryfolders.objects.using('grid').create(folderID=uuid.uuid4(),agentID=profile.uuid)
            except ObjectDoesNotExist:
                pass
        if hasattr(profile,'raw_password'):
            del profile.raw_password


    def delete_avatar(self, client, profile_uuid):
        """After hwios changes the profile, this observer takes care of deleting the opensim profile.

        :param Client client: The requesting client
        :param str profile_uuid: The uuid of the profile to delete
        """
        #check if grid db exists first.
        try:
            cursor = connections['grid'].cursor()
        except pymysql.err.InternalError:
            return False
        try: osprofile = OSUserAccounts.objects.using('grid').get(pk = profile_uuid).delete()
        except ObjectDoesNotExist: pass
        try: osauth = OSauth.objects.using('grid').get(pk = profile_uuid).delete()
        except ObjectDoesNotExist: pass
        try:
            osfolders = OSinventoryfolders.objects.using('grid').filter(agentID = profile_uuid)
            for osfolder in osfolders:
                osfolder.delete()
        except ObjectDoesNotExist: pass    
    
    
    @WSAuth.is_staff
    def view_regions(self, client):
        """Renders the current available regions view

        :param Client client: The requesting client
        :return: dict - Html-layout data response
        """
        #check if grid db exists first.
        scenes = Scenes.get_scenes()
        regions = Regions.get_regions()
        region_services = Regions().get_region_services()
        for count1,region_service in enumerate(region_services):
            for count2,region in enumerate(region_service['regions']):
                try:
                    if 'MasterAvatarUUID' in region:
                        profile = Profile.objects.get(uuid = region['MasterAvatarUUID'])
                        region_services[count1]['regions'][count2]['profile'] = {'first_name':profile.first_name,'last_name':profile.last_name}
                    else:
                        region_services[count1]['regions'][count2]['profile'] = {'first_name':'Invalid','last_name':'Invalid'}
                except ObjectDoesNotExist,KeyError:
                    region_services[count1]['regions'][count2]['profile'] = {'first_name':'Invalid','last_name':'Invalid'}
        main = render_to_string("opensim/read_regions.html", {'regions': regions,'scenes':scenes})
        return {'data':{'dom':{'main':main}}}
        
    
    @defer.inlineCallbacks
    @WSAuth.is_staff
    def create_region(self, client, params = None):
        """Either renders the template to create a new region, or handle the creation process

        :param Client client: The requesting client
        :param dict params: Optional; contains the form parameters
        :return: dict - Html-layout data response
        """
        if params == None:
            form = RegionForm()
            main = render_to_string("opensim/create_region.html", {'form':form})
            response = {'data':{'dom':{'main':main}}} 
            defer.returnValue(response)
        else:
            form = RegionForm(params)
            if form.is_valid():
                response = {'status':{}}
                profile = Profile.objects.get(pk = params['owner'])
                radmin_params = {
                'region_name':params['name'],
                'region_id':str(uuid.uuid4()),
                'region_x':params['sim_location_x'],
                'region_y':params['sim_location_y'],
                'estate_owner_uuid':profile.uuid,
                'estate_owner_first':profile.first_name,
                'estate_owner_last':profile.last_name,
                'estate_name':'My Estate',
                'public':'true',
                'enable_voice':'true'
                }
                result = yield HWIOS.pb_server.radmin_proxy(params['service'],'admin_create_region',radmin_params)
                client_response, tpl_params = self._get_regions(client)
                if 'success' in result: 
                    if result['success']:
                        #queued = Maps.render_cell(params['sim_location_x'],params['sim_location_y'],image_loc)
                        #map-image is not ready yet at this point. Call a little later                        
                        def _map_cb(params, region_uuid):
                            service_client = HWIOS.pb_server.search_service(params['service'])
                            image_loc = 'http://%s:%s/index.php?method=regionImage%s' % (service_client['client'].peer.host, service_client['service']['port'], region_uuid.replace('-', ''))
                            queued = Maps.render_cell(params['sim_location_x'],params['sim_location_y'],image_loc)
                        reactor.callLater(3, _map_cb, params, result['region_uuid'])
                        client_response.update({'status': {
                            'code':'REGION_CREATED',
                            'i18n':_('Succesfully created region in simulator!'),
                            'type': HWIOS.ws_realm._t['notify-info']
                            }
                        })
                    else:
                        if result['error'] == 'SIM_OFFLINE':
                            client_response.update({'status': {
                                'code':'REGION_CREATED',
                                'i18n':_('Region created on offline simulator. Please verify that the simulator still boots correctly...'),
                                'type': HWIOS.ws_realm._t['notify-info']
                                }
                            })
                    notify_others(client, client_response,'/opensim/regions/modified/', '^/opensim/regions/$', tpl_params)
                    publish_activity(client.profile, _('Region created'),'/opensim/regions/',[0,0,4,0,0])
                else:
                    if result['status']['code'] == 'RADMIN_FAILED':
                        result['status']['feedback'] = 'Remote Admin OpenSimulator Interface Failure!'
                    client_response.update({'status': {
                        'code':result['status']['code'],
                        'i18n':_(result['status']['feedback']),
                        'type': HWIOS.ws_realm._t['notify-info']
                        }
                    })               
            else:
                main = render_to_string("opensim/create_region.html", {'form':form})
                client_response = {
                    'status':{
                        'code':'FORM_INVALID',
                        'i18n':_('Please pay attention to the region details...'),
                        'type': HWIOS.ws_realm._t['notify-warning']
                    },
                    'data':{'dom':{'main':main}}
                } 
            defer.returnValue(client_response)


    def _get_regions(self, client):
        """Notify_others helper that gets the template-info and rendering of the regions view"""
        scenes = Scenes.get_scenes()
        regions = Regions.get_regions()
        tpl_params = {'regions': regions,'scenes':scenes}
        main = render_to_string("opensim/read_regions.html", tpl_params)
        return [
            {'data':{'dom':{'main':main}}},
            {'main':{'tpl':'opensim/read_regions.html','params':tpl_params}}
        ]
        
            
    @WSAuth.is_staff
    @defer.inlineCallbacks
    def edit_region(self, client, region_uuid, params = None):
        """Either renders the template to edit an existing region, or handle the update process

        :param Client client: The requesting client
        :param str region_uuid: The region uuid reference to select the appropriate region for updating
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and Html-layout data response
        """
        if params == None:
            region = Regions().get_region(region_uuid)
            data = {'sim_uuid': region['RegionUUID'], 
                    'internal_ip_address':region['InternalAddress'],
                    'internal_ip_port':region['InternalPort'],
                    'external_host_name':region['ExternalHostName'],
                    'object_capacity':15000,
                    'sim_location_x':region['Location'].split(',')[0],
                    'sim_location_y':region['Location'].split(',')[1],
                    'name':region['name'],
                    'owner':None,
                    'service':region['service_uuid']}
            form = RegionForm(initial=data)
            main = render_to_string("opensim/edit_region.html", {'form':form,'region_uuid':region_uuid})
            defer.returnValue({'data':{'dom':{'main':main}}})
        else:        
            response = {'status':{}}
            profile = Profile.objects.get(pk = params['owner'])
            radmin_params = {
            'region_name':params['name'],
            'region_id':region_uuid,
            'region_x':params['sim_location_x'],
            'region_y':params['sim_location_y'],
            'region_master_uuid':profile.uuid,
            'region_master_first':profile.first_name,
            'region_master_last':profile.last_name,
            'region_master_password':'foo',
            'public':'true',
            'enable_voice':'true'
            }
            #clean old map-location with an opaque tile
            region_old = Regions().get_region(region_uuid)
            old_xy = [region_old['Location'].split(',')[0],region_old['Location'].split(',')[1]]
            queued = Maps.render_cell(old_xy[0],old_xy[1])
            service_client = yield HWIOS.pb_server.search_service(params['service'])
            #if the service is not online, take the existing image
            tms_config = HWIOS.services['tms'].config
            if tms_config.getboolean('map','osm'): ztop = tms_config.get('map','osm_ztop')
            else: ztop = tms_config.get('map','raw_ztop')
            
            if service_client['service']['status'] == 'OFF':
                if tms_config.getboolean('service','ssl'):
                    image_loc = 'https://%s:%s/tiles/%s/%s/%s.%s' % (HWIOS.config.get('general','uri'),tms_config.getint('service','port'), ztop ,old_xy[0],old_xy[1],tms_config.get('map','format'))
                else:
                    image_loc = 'http://%s:%s/tiles/%s/%s/%s.%s' % (HWIOS.config.get('general','uri'),tms_config.getint('service','port'), ztop ,old_xy[0],old_xy[1],tms_config.get('map','format'))
            else:
                image_loc = 'http://%s:%s/index.php?method=regionImage%s' % (service_client['client'].peer.host, service_client['service']['port'], region_uuid.replace('-', ''))
            queued = Maps.render_cell(params['sim_location_x'],params['sim_location_y'],image_loc)
            pb_client = HWIOS.pb_server.search_client(params['service'])
            watchdog = yield pb_client.switch_watchdog(params['service'],'TRIGGER')            
            result = yield HWIOS.pb_server.radmin_proxy(params['service'],'admin_shutdown',radmin_params)
            client_response, tpl_params = self._get_regions(client)
            if 'error' in result:
                if result['error'] == 'SIM_OFFLINE': 
                    client_response.update({'status': {
                        'code':'REGION_UPDATED',
                        'i18n':_('Updated region in offline simulator!'),
                        'type': HWIOS.ws_realm._t['notify-info']
                        }
                    })
                else: 
                    client_response.update({'status': {
                        'code':result['error'],
                        'i18n':_(result['error']),
                        'type': HWIOS.ws_realm._t['notify-error']
                        }
                    })
            else: 
                client_response.update({'status': {
                    'code':'REGION_UPDATED',
                    'i18n':_('Region updated. Region service restarting with watchdog...'),
                    'type': HWIOS.ws_realm._t['notify-info']
                    }
                })
            notify_others(client, client_response,'/opensim/regions/modified/', '^/opensim/regions/$', tpl_params)
            publish_activity(client.profile, _('Region modified'),'/opensim/regions/',[0,0,4,0,0])
            defer.returnValue(client_response)


    @WSAuth.is_staff
    @defer.inlineCallbacks
    def delete_regions(self, client, params = None):
        """Either renders the template to confirm deleting a region, or handle the deletion process ifself

        :param Client client: The requesting client
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and Html-layout data response
        """
        if params == None:
            dialog = render_to_string("opensim/delete_region_confirmation.html")
            defer.returnValue({'data':{'dom':{'dialog':dialog}}})
        else:
            deleted_offline = []
            deleted_online = []
            for region_uuid in params:
                region = Regions().get_region(region_uuid)
                queued = Maps.render_cell(region['Location'].split(',')[0],region['Location'].split(',')[1])
                result = yield HWIOS.pb_server.radmin_proxy(region['service_uuid'],'admin_delete_region',{'region_id':region_uuid})
                if 'error' in result and result['error'] == 'SIM_OFFLINE':
                    deleted_offline.append(result['error'])
                elif 'success' in result:
                    deleted_online.append(result['success'])            
            client_response, tpl_params = self._get_regions(client)
            client_response.update({
                'status':{
                    'code':'DELETE_OK',
                    'i18n':_('Deleted: %(online)s online and %(offline)s offline region(s) ') % {'online':len(deleted_online),'offline':len(deleted_offline)},
                    'type': HWIOS.ws_realm._t['notify-info']
                },
            })
            notify_others(client, client_response,'/opensim/regions/modified/', '^/opensim/regions/$', tpl_params)
            publish_activity(client.profile, _('Region deleted'),'/opensim/regions/',[0,0,4,0,0])
            defer.returnValue(client_response)
            

    @WSAuth.is_staff
    @defer.inlineCallbacks
    def backup_region(self, client, region_uuid, params = None):
        """Either renders the template to confirm backing up a region, or handle the backup process ifself

        :param Client client: The requesting client
        :param str region_uuid: The region's uuid to operate on
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and Html-layout data response
        """
        if params == None:
            region = Regions().get_region(region_uuid)
            current_time = time.strftime('%Y-%m-%d-%H.%M')
            proposed_name = '%s-%s' % (region['name'],current_time)
            form = BackupRegionForm(initial={'name':proposed_name,'region_uuid':region['RegionUUID'],'service_uuid':region['service_uuid']}) 
            dialog = render_to_string("opensim/backup_region_confirmation.html", {'form':form})
            defer.returnValue({'data':{'dom':{'dialog':dialog}}})
        else:
            response = {'status':{}}
            region = Regions().get_region(region_uuid)
            service_client = HWIOS.pb_server.search_service(region['service_uuid'])
            result = yield service_client['client'].backup_region(region['service_uuid'],region_uuid,params['name'])
            print result
            if 'saved' in result:
                if result['saved']:
                    response['status'] = {
                        'code':'BACKUP_MADE',
                        'i18n':_('Backup of region %(name)s finished...') % {'name':region['name']},
                        'type': HWIOS.ws_realm._t['notify-info']
                    }
            else:
                if result['status']['code'] == 'RADMIN_FAILED':
                    response['status']['i18n'] = _('Backup failed! Region must be online when creating a backup...')
                    response['status']['type'] = HWIOS.ws_realm._t['notify-error']
                else:
                    response['status']['i18n'] = _('This may take a while...')
                    response['status']['type'] = HWIOS.ws_realm._t['notify-info']
                    
            main = render_to_string("opensim/read_regions.html", {'region_services': Regions().get_region_services(),'scenes':Scenes.get_scenes()})
            response.update({'data':{'dom':{'main':main}}})
            defer.returnValue(response)
        

    @WSAuth.is_staff
    def delete_scenes(self, client, params = None):
        """Either renders the template to confirm deleting a scene, or handle the scene deletion process ifself

        :param Client client: The requesting client
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and Html-layout data response
        """
        if params == None:
            dialog = render_to_string("opensim/delete_scene_confirmation.html")
            return {'data':{'dom':{'dialog':dialog}}}   
        else:
            deleted = Scenes.delete_scenes(params)
            main = render_to_string("opensim/read_regions.html", {'region_services': Regions().get_region_services(),'scenes':Scenes.get_scenes()})
            if deleted:
                response = {
                    'status':{
                        'code':'SCENES_DELETE_OK',
                        'i18n':_('Deleted: %(deleted)s scene(s)') % {'deleted':deleted},
                        'type': HWIOS.ws_realm._t['notify-info']
                    }
                }
            else:
                response = {
                    'status':{
                        'code':'SCENES_DELETE_FAIL',
                        'i18n':_('Failed to delete scenes. Invalid characters!'),
                        'type': HWIOS.ws_realm._t['notify-error']
                    }
                }
            response.update({'data':{'dom':{'main':main}}})
            return response
        

    @WSAuth.is_staff
    @defer.inlineCallbacks
    def load_scene(self, client, scene_name, params = None):
        """Either renders the template to confirm loading up a region, or handle the scene loading process ifself

        :param Client client: The requesting client
        :param str scene_name: The scene's name to operate on
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and Html-layout data response
        """
        if params == None:
            regions = Regions.get_regions()
            selection = []
            for region in regions:
                selection.append((region['RegionUUID'],region['name']))
            form = LoadSceneForm(choices=selection,initial={'scene_name':scene_name})
            dialog = render_to_string("opensim/load_scene_confirmation.html", {'form':form})
            defer.returnValue({'data':{'dom':{'dialog':dialog}}})
        else:
            response = {'status':{}}
            region = Regions.get_region(params['region_uuid'])
            service_client = HWIOS.pb_server.search_service(region['service_uuid'])
            result = yield service_client['client'].load_scene(region['service_uuid'],params['region_uuid'], params['scene_name'])
            if 'loaded' in result:
                if result['loaded']:
                    response = {
                        'status':{
                            'code':'RESTORE_MADE',
                            'i18n':_('Succesfully restored scene %(scene)s in region %(region)s...') % {'scene':params['scene_name'],'region':region['name']},
                            'type': HWIOS.ws_realm._t['notify-info']
                        }
                    }
            else:
                if 'RADMIN_FAILED' in result['status']['code']:
                    response = {
                        'status':{
                            'code':'RADMIN_FAILED',
                            'i18n':_(result['status']['feedback']),
                            'type': HWIOS.ws_realm._t['notify-error']
                        }
                    }
                elif 'error' in result:
                    if result['error'] == 'SIM_OFFLINE':
                        response = {
                            'status':{
                                'code':'RESTORE_FAILED',
                                'i18n':_('Restore failed! Region must be online when loading a scene...'),
                                'type': HWIOS.ws_realm._t['notify-error']
                            }
                        }
                    elif result['error'] == 'radmin response timed out':
                        response = {
                            'status':{
                                'code':'RESTORE_RUNNING',
                                'i18n':_('Loading this OAR may take a while. Check the console for the current progress...'),
                                'type': HWIOS.ws_realm._t['notify-info']
                            }
                        }
            main = render_to_string("opensim/read_regions.html", {'region_services': Regions().get_region_services(),'scenes':Scenes.get_scenes()})
            response.update({'data':{'dom':{'main':main}}})
            defer.returnValue(response)
            
            
    @WSAuth.is_staff        
    def upload_scenes(self, client, params = None):
        """Renders the template that shows an upload overview of scenes. We only provide the view here.
        File uploads over websocket doesn't make sense atm with utf-8 only.

        :param Client client: The requesting client
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and Html-layout data response
        """

        if params == None:
            form = UploadSceneForm()
            main = render_to_string("opensim/upload_scene.html", {'form':form})
            return {'data':{'dom':{'main':main}}}
            
            
    @WSAuth.is_staff
    @defer.inlineCallbacks
    def load_luggage(self, client, luggage_name, params = None):
        """Either renders the template that shows the dialog to load lugguge,
        or handle the load luggage process itself.

        :param Client client: The requesting client
        :param str luggage_name: The luggage's name to operate on
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and Html-layout data response
        """
        if params == None:
            online_simulators = Simulators.get_simulators(online=True)
            selection = []
            for simulator in online_simulators:
                selection.append((simulator['uuid'],simulator['name']))
            form = LoadLuggageForm(choices=selection,initial={'luggage_name':luggage_name})
            dialog = render_to_string("opensim/load_luggage_confirmation.html", {'form':form})
            response = {'data':{'dom':{'dialog':dialog}}}
            defer.returnValue(response)
        else:
            #{'simulator_uuid': '5ced4744-f5b7-4100-9a4e-40ab73ec5c0c', 'inventory_dir': '/', 'luggage_name': 'InventoryDump.iar', 'avatar': '13'}
            response = {'status':{}}
            online_simulators = Simulators.get_simulators(online=True)
            selection = []
            for simulator in online_simulators:
                selection.append((simulator['uuid'],simulator['name']))
            form = LoadLuggageForm(params,choices=selection)
            if form.is_valid():
                profile = form.cleaned_data['avatar']
                simulator = Simulators.get_simulator(params['simulator_uuid'])
                service_client = HWIOS.pb_server.search_service(params['simulator_uuid'])
                result = yield service_client['client'].load_luggage(params['simulator_uuid'],[profile.first_name,profile.last_name,params['password']],params['inventory_dir'],params['luggage_name'])
                luggage = Luggage.get_luggage()
                profiles = Profile.objects.all()
                main = render_to_string("opensim/read_avatars.html", {'profiles':profiles,'luggage':luggage,'online_simulators':len(online_simulators)})
                response['status'] = {
                    'code':'LUGGAGE_LOAD_OK',
                    'i18n':_('Trying to load luggage file. Check your avatar in-world for the notification, or open the remote console for further information...'),
                    'type': HWIOS.ws_realm._t['notify-info']
                }
                response['dom'] = {'main':main}
            else:
                response['status'] = {
                    'code':'FORM_INVALID',
                    'i18n':_('Invalid form...'),
                    'type': HWIOS.ws_realm._t['notify-warning']
                }
                dialog = render_to_string("opensim/load_luggage_confirmation.html", {'form':form})
                response['dom'] = {'dialog':dialog}
            defer.returnValue(response)
        

    @WSAuth.is_staff
    @defer.inlineCallbacks
    def backup_luggage(self, client, profile_uuid = None, params = None):
        """Either renders the template that shows the dialog to backup lugguge,
        or handle the backup luggage process itself.

        :param Client client: The requesting client
        :param str profile_uuid: The profile's uuid to operate on
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and Html-layout data response
        """
        if params == None:
            online_simulators = Simulators.get_simulators(online=True)
            selection = []
            profile = Profile.objects.get(uuid=profile_uuid)
            for simulator in online_simulators:
                selection.append((simulator['uuid'],simulator['name']))
            current_time = time.strftime('%Y-%m-%d-%H.%M')
            proposed_name = '%s_%s-%s' % (profile.first_name,profile.last_name,current_time)
            form = BackupLuggageForm(choices=selection,initial={'luggage_name':proposed_name})
            dialog = render_to_string("opensim/backup_luggage_confirmation.html", {'form':form})
            response ={'data':{'dom':{'dialog':dialog}}}
            defer.returnValue(response) 
        else:
            #{'simulator_uuid': '5ced4744-f5b7-4100-9a4e-40ab73ec5c0c', 'inventory_dir': '/', 'luggage_name': 'InventoryDump.iar', 'avatar': '13'}
            response = {'status':{},'data':{}}
            online_simulators = Simulators.get_simulators(online=True)
            profile = Profile.objects.get(uuid=params['profile_uuid'])
            selection = []
            for simulator in online_simulators:
                selection.append((simulator['uuid'],simulator['name']))
            form = BackupLuggageForm(params,choices=selection,profile=profile)
            if form.is_valid():
                simulator = Simulators.get_simulator(params['simulator_uuid'])
                service_client = HWIOS.pb_server.search_service(params['simulator_uuid'])
                result = yield service_client['client'].backup_luggage(params['simulator_uuid'],[profile.first_name,profile.last_name,params['password']],params['inventory_dir'],params['luggage_name'])
                luggage = Luggage.get_luggage()
                profiles = Profile.objects.all()
                main = render_to_string("opensim/read_avatars.html", {'profiles':profiles,'luggage':luggage,'online_simulators':len(online_simulators)})
                response['status'] = {
                    'code':'LUGGAGE_LOAD_OK',
                    'i18n':_('Trying to backup luggage file. Check your avatar in-world for the notification, or open the remote console for further information...'),
                    'type': HWIOS.ws_realm._t['notify-info']
                }                
                response['data']['dom'] = {'main':main}
            else:
                response['status'] = {
                    'code':'FORM_INVALID',
                    'i18n':_('Invalid form...'),
                    'type': HWIOS.ws_realm._t['notify-warning']
                }
                dialog = render_to_string("opensim/backup_luggage_confirmation.html", {'form':form})
                response['data']['dom'] = {'dialog':dialog}
            defer.returnValue(response)
            
            
    @WSAuth.is_staff
    def delete_luggage(self, client, params = None):
        """Either renders the template that shows the dialog to confirm lugguge deletion,
        or handle the luggage deletion process itself.

        :param Client client: The requesting client
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and Html-layout data response
        """
        if params == None:
            dialog = render_to_string("opensim/delete_luggage_confirmation.html")
            return {'data':{'dom':{'dialog':dialog}}}
        else:
            deleted = Luggage.delete_luggage(params)
            online_simulators = Simulators.get_simulators(online=True)
            if deleted: 
                response = {
                    'status':{
                        'code':'SCENES_DELETE_OK',
                        'i18n':_('Deleted: %(deleted)s inventory archive file(s) ') % {'deleted':deleted},
                        'type': HWIOS.ws_realm._t['notify-info']
                    }
                }
            else: 
                response = {
                    'status':{
                        'code':'SCENES_DELETE_FAIL',
                        'i18n':_('Failed to delete inventory archive file(s). Invalid characters!'),
                        'type': HWIOS.ws_realm._t['notify-error']
                    }
                }
            response.update(self.view_avatars(client))
            return response

            
    @WSAuth.is_staff
    def upload_luggage(self, client, params = None):
        """Renders the template that shows the upload luggage overview. We only provide the view here.
        File uploads over websocket doesn't make sense atm with utf-8 only

        :param Client client: The requesting client
        :param dict params: Optional; contains the form parameters
        :return: dict - Html-layout data response
        """
        if params == None:
            form = UploadLuggageForm()
            main = render_to_string("opensim/upload_luggage.html", {'form':form})
            return {'data':{'dom':{'main':main}}}
            
            
    @WSAuth.is_staff
    def view_avatars(self, client):
        """Renders the template that shows the avatars available. 

        :param Client client: The requesting client
        :return: dict - Html-layout data response
        """        
        profiles = OSUserAccounts.objects.using('grid').all()
        luggage = Luggage.get_luggage()
        online_simulators = Simulators.get_simulators(online=True)
        main = render_to_string("opensim/read_avatars.html", {'profiles':profiles,'luggage':luggage,'online_simulators':len(online_simulators)})
        return {'data':{'dom':{'main':main}}}


    @WSAuth.is_staff
    def sync_avatars(self, client):
        """Synchronizes between hwios and opensim accounts in both ways. Only works while opensim's hashing method
        is used in HWIOS(default).

        :param Client client: The requesting client
        :return: dict - Status and Html-layout data response
        """   
        response = {'data':{'synced':[]}}
        new_profiles = []
        profiles = Profile.objects.all()
        os_profiles = OSUserAccounts.objects.using('grid').all()
        new_profiles = []
        new_osprofiles = []
        #sync osprofile to profile
        for os_profile in os_profiles:
            match = False
            for profile in profiles:
                profile_name = '%s %s' % (profile.first_name,profile.last_name)
                osprofile_name = '%s %s' % (os_profile.FirstName, os_profile.LastName)
                if profile.uuid == os_profile.PrincipalID.UUID:
                    match = True
                elif (profile_name == osprofile_name):
                    match = True
            if match == False: new_profiles.append(os_profile)
        for new_profile in new_profiles:
            profile = Profile()
            profile.username = '%s %s' % (new_profile.FirstName, new_profile.LastName)
            profile.first_name = new_profile.FirstName
            profile.last_name = new_profile.LastName
            profile.email = new_profile.Email
            profile.is_active = 1
            profile.uuid = new_profile.PrincipalID.UUID
            profile.salt = new_profile.PrincipalID.passwordSalt
            profile.password = new_profile.PrincipalID.passwordHash
            profile.ip = '0.0.0.0'
            profile.date_joined = datetime.now()
            profile.save()
        #sync profile to osprofile
        for profile in profiles:
            match = False
            for os_profile in os_profiles:
                profile_name = '%s %s' % (profile.first_name,profile.last_name)
                osprofile_name = '%s %s' % (os_profile.FirstName, os_profile.LastName)
                if profile.uuid == os_profile.PrincipalID.UUID:
                    match = True
                elif (profile_name == osprofile_name):
                    match = True
            if match == False:
                new_osprofiles.append(profile)
        for _profile in new_osprofiles:
            self.change_avatar(client, _profile)
        client_response, tpl_params = self._get_avatars(client)
        _target_state = '/opensim/avatars/'
        client_response.update({
            'status':{
                'code':'PROFILE_SYNC_OK',
                'i18n':_('%(profiles)s/%(osprofiles)s profile(s)/avatar(s) were synced!') % {'profiles':len(new_profiles),'osprofiles':len(new_osprofiles)},
                'type': HWIOS.ws_realm._t['notify-info']
            }
        })
        notify_others(client, client_response,'/opensim/avatars/modified/', '^/opensim/avatars/$', tpl_params, _target_state)
        publish_activity(client.profile, _('Avatar(s) synced'),'/opensim/avatars/',[0,0,1,0,0])
        return client_response    


    def _get_avatars(self, client):
        """Notify_others helper function that prepares an overview of avatars"""
        profiles = OSUserAccounts.objects.using('grid').all()
        luggage = Luggage.get_luggage()
        online_simulators = Simulators.get_simulators(online=True)
        tpl_params = {'profiles':profiles,'luggage':luggage,'online_simulators':len(online_simulators)}
        main = render_to_string("opensim/read_avatars.html", tpl_params)
        return [
            {'data':{'dom':{'main':main}}},
            {'main':{'tpl':'opensim/read_avatars.html','params':tpl_params}}
        ]
        
        
    def _get_map_form(self):
        """Prepare map ini-data to fit in a django form"""
        form_fields = {}
        service_config = HWIOS.services['tms'].config
        for section in service_config.sections():
            for key,value in service_config.items(section):
                if value == 'False':
                    form_fields[key] = False
                else:
                    form_fields[key] = value
        return MapSettingsForm(initial=form_fields)
        
        
    @WSAuth.is_staff
    def handle_settings(self, client, params = None):
        """Either renders the template to change opensim's settings, or handle the update settings process itself

        :param Client client: The requesting client
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and Html-layout data response
        """   
        if params == None:
            response = {'status':{}}
            simulator_form = SimulatorSettingsForm(initial={'master_ini': open("./services/web_ui/dav_store/config/grid_master.ini","r").read()})       
            main = render_to_string("opensim/read_settings.html", {'simulator_form':simulator_form,'map_form':self._get_map_form()})
            return {'data':{'dom':{'main':main}}}
        else:
            if 'master_ini' in params:
                simulator_form = SimulatorSettingsForm(params)
                if simulator_form.is_valid():
                    infile = open("./services/web_ui/dav_store/config/grid_master.ini","w")
                    infile.write(simulator_form.cleaned_data['master_ini'])
                    response = {'status':{
                        'code':'SETTINGS_UPDATE_OK',
                        'i18n':_('Simulator settings succesfully updated'),
                        'type': HWIOS.ws_realm._t['notify-info']
                        }
                    }
                else: 
                    response = {'status':{
                        'code':'INVALID_FORM',
                        'i18n':_('Invalid form'),
                        'type': HWIOS.ws_realm._t['notify-info']
                        }
                    }
            elif 'center_z' in params:
                simulator_form = SimulatorSettingsForm(initial={'master_ini': open("./services/web_ui/dav_store/config/grid_master.ini","r").read()})     
                if 'osm' not in params:
                    params['osm'] = False
                response = {'status':{}}
                map_form = MapSettingsForm(params)
                if map_form.is_valid():
                    service_config = HWIOS.services['tms'].config
                    for section in service_config.sections():
                        for key,value in service_config.items(section):
                            if key in params:
                                service_config.set(section,key,params[key])
                    service_config.write(open(os.path.join(service_config.location,'service.ini'),'wb'))
                    service_config.read(os.path.join(service_config.location,'service.ini'))
                    response['status'] = {
                        'code':'CONFIG_UPDATE_OK',
                        'i18n':_('Configuration updated...'),
                        'type': HWIOS.ws_realm._t['notify-info']
                    }
                else:
                    response['status'] = {
                        'code':'FORM_INVALID',
                        'i18n':_('Invalid form!'),
                        'type': HWIOS.ws_realm._t['notify-warning']
                    }
                Maps.update_client_settings()
            client_response, tpl_params = self._get_settings(client)
            client_response.update(response)
            _target_state = '/opensim/settings/'
            notify_others(client, client_response,'/opensim/settings/modified/', '^/opensim/settings/$', tpl_params, _target_state)
            publish_activity(client.profile, _('OpenSim Settings updated'),'/opensim/settings/',[0,0,4,0,0])
            return client_response    


    def _get_settings(self, client):
        """Notify_others helper function that creates an overview of the settings view"""
        simulator_form = SimulatorSettingsForm(initial={'master_ini': open("./services/web_ui/dav_store/config/grid_master.ini","r").read()})     
        tpl_params = {'simulator_form':simulator_form,'map_form':self._get_map_form()}
        main = render_to_string('opensim/read_settings.html', tpl_params)        
        return [
            {'data':{'dom':{'main':main}}},
            {'main':{'tpl':'opensim/read_settings.html','params':tpl_params}}
        ]


    @WSAuth.is_staff
    def render_maps(self, client):
        """Renders all opensim region cells of the map

        :param Client client: The requesting client
        :return: dict - Status data response
        """   
        result = Maps().render_map()
        response = {
            'status':{
                'code':'MAP_RENDER_OK',
                'i18n':_('Map succesfully rendered from %(cells)s cells...') % {'cells':result['cells']},
                'type': HWIOS.ws_realm._t['notify-info']
            }
        }
        return response
