# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.models.opensim
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The websocket controller for the wiki module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os
from stat import *
import time
from core.application import HWIOS
from web_ui.models.settings import Settings

class Maps():
    """Map specific handler for the TMS service"""

    @classmethod
    def update_client_settings(self):
        """Push map-settings update to all clients"""
        clients = HWIOS.ws_realm.pool.get_clients()
        client_settings = HWIOS.services['tms'].get_client_settings()
        for client in clients:
            client.remote('/data/modules/maps/settings/update/',client_settings)


    @classmethod
    def render_map(self):
        """Render all region cells"""
        HWIOS.services['tms'].tiler.cell_list = []
        queued = HWIOS.services['tms'].tiler.process_queue()
        self.update_client_settings()
        return queued


    @classmethod
    def update_service_settings(self,data):
        """A dummy to update map settings. Not in use currently..."""
        for section in HWIOS.services['tms'].config.sections():
            pass
            #setattr(HWIOS.services['tms'].config


    @classmethod
    def render_cell(self,x,y,image_loc=None):
        """Render a specific cell on the worldmap, based on a fixed start-z

        :param int x: the x grid-location on the worldmap to render
        :param int y: the y grid-location on the worldmap to render
        :param str image_loc: Optional; where to get the image from(region map-tile uri for instance). Empty fills with a not-available image
        """
        if not image_loc: HWIOS.services['tms'].tiler.cell_list = [{'x':x,'y':y}]
        else:
            HWIOS.services['tms'].tiler.cell_list = [{'x':x,'y':y,'image_loc':str(image_loc)}]
        queued = HWIOS.services['tms'].tiler.process_queue()
        self.update_client_settings()
        return queued


class Simulators:
    """
    Abstraction layer between teknon and general opensim concept of simulators.
    Handles basic commands that are involved with simulator management.
    """
    
    def __init__(self):
        pass
    
    
    @classmethod
    def get_simulators(self,online=False):
        """
        Get all simulators from all tms clients

        :param bool online: Returns only online simulators when true
        :return: dict - a list of simulators
        """
        teknon_clients = HWIOS.pb_server.get_clients()
        simulators = []
        for client in teknon_clients:
            for service in client.services:
                if service['type'] == 'SIM':
                    if online:
                        if service['status'] == 'ON':
                            simulators.append(service)
                    else:
                        simulators.append(service)
        return simulators
        
        
    @classmethod
    def get_simulator(self,uuid):
        """
        Get a simulator based on service uuid

        :param str uuid: The service uuid to get it from
        :return: dict - returns a client_service 
        """
        teknon_clients = HWIOS.pb_server.get_clients()
        simulators = []
        for client in teknon_clients:
            for service in client.services:
                if service['uuid'] == uuid:
                    return service
        return False


class Regions:
    """
    Abstraction layer between teknon and general opensim concept of regions.
    Handles basic commands that are involved with simulator management.
    """

    
    def __init__(self):
        pass
    
        
    def get_region_services(self,format=None):
        """
        Get a list of regions from each online teknon host

        :param str format: select output type ("tuple" or "dict")
        :return: dict or tuple - A list of region-services
        """
        clients = HWIOS.pb_server.get_clients()
        region_services = []
        for client in clients:
            region_services.extend(client.region_services)
        #for django forms
        if format == 'tuple':
            tuple_list = []
            for region_service in region_services:
                tuple_list.append((region_service['uuid'],region_service['name']))
            return tuple_list
        return region_services
        
    
    @classmethod
    def get_regions(self):
        """
        Get a list of regions from each online teknon host

        :return: list - A list of regions from each teknon service that is a region service
        """
        clients = HWIOS.pb_server.get_clients()
        regions = []
        for client in clients:
            for service in client.region_services:
                if service['status'] == 'ON':
                    for region in service['regions']:
                        region['service'] = service['name']
                        region['status'] = 'Online'
                        regions.append(region)
                else:
                    for region in service['regions']:
                        region['service'] = service['name']
                        region['status'] = 'Offline'
                        regions.append(region)
        return regions
    
    
    @classmethod
    def get_region(self,region_uuid):
        """
        Get region with uuid from Teknon clients
        
        :param str region_uuid: The uuid of the region to lookup
        :return: dict or False - Info about the region or False
        """
        teknon_clients = HWIOS.pb_server.get_clients()
        simulators = []
        for client in teknon_clients:
            for service in client.services:
                if service['type'] == 'SIM':
                    for region in service['regions']:
                        if region['RegionUUID'] == region_uuid:
                            region['service_uuid'] = service['uuid']
                            return region
        return False
        
        
class Scenes:
    """
    Abstraction layer between teknon and general opensim concept of scenes.
    Handles basic commands that are involved with simulator management.
    """
    
    def __init__(self):
        pass    
    
    @classmethod
    def get_scenes(self):
        """
        Get an overview of all available scenes in our webdav share

        :return: list or Exception - Info about all available files or an IOError exception
        """
        oar_path = os.path.join(HWIOS.services['web_ui'].config.location,'dav_store','oar')
        file_list = os.listdir(oar_path)        
        scenes= []
        for count,value in enumerate(file_list):  
            oar_location = os.path.join(oar_path,value)
            name, ext = os.path.splitext(oar_location)
            if ext == '.oar':
                scenes.append({'name': value})
                try:
                    st = os.stat(oar_location)
                    scenes[count]['size'] = '%s MB' % round(float(st[ST_SIZE]) / 1024 / 1024,3)
                    scenes[count]['modified'] = time.asctime(time.localtime(st[ST_MTIME]))
                except IOError:
                    print "failed to get information about", open(oar_location)
        return scenes

    
    @classmethod
    def delete_scenes(self,scene_list):
        """
        Delete a scene from the local webdav share

        :param list scene_list: A filename list of all the scenes to delete
        :return: int or False - The amount of deleted files or False
        """
        oar_path = os.path.join(HWIOS.services['web_ui'].config.location,'dav_store','oar')
        deleted = 0
        for scene in scene_list:
            if "/" not in scene and "\000" not in scene and len(scene) <=255:
                if os.path.splitext(scene)[1] == '.oar':
                    os.remove(os.path.join(oar_path, scene))
                    deleted += 1
            else:
                return False
        return deleted
        
        
class Luggage:
    """
    Abstraction layer between teknon and general opensim concept of luggage.
    Handles basic commands that are involved with simulator management.
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def get_luggage(self):
        """
        Get an overview of all available luggage files in our webdav share

        :return: list or Exception - Info about all available files or an IOError exception        
        """
        iar_path = os.path.join(HWIOS.services['web_ui'].config.location,'dav_store','iar')
        file_list = os.listdir(iar_path)
        luggage= []
        for count,value in enumerate(file_list):  
            iar_location = os.path.join(iar_path,value)
            name, ext = os.path.splitext(iar_location)
            if ext == '.iar':
                luggage.append({'name': value})
                try:
                    st = os.stat(iar_location)
                    luggage[count]['size'] = '%s MB' % round(float(st[ST_SIZE]) / 1024 / 1024,3)
                    luggage[count]['modified'] = time.asctime(time.localtime(st[ST_MTIME]))
                except IOError:
                    print "failed to get information about", open(iar_location)
        return luggage
    
    @classmethod
    def delete_luggage(self,luggage_list):
        """
        Delete a luggage file from the local webdav share

        :param list luggage_list: A filename list of all the luggage files to delete
        :return: int or False - The amount of deleted files or False
        
        """
        iar_path = os.path.join(HWIOS.services['web_ui'].config.location,'dav_store','iar')
        deleted = 0
        for luggage in luggage_list:
            if "/" not in luggage and len(luggage) <=255:
                if os.path.splitext(luggage)[1] == '.iar':
                    os.remove(os.path.join(iar_path, luggage))
                    deleted += 1
            else:
                return False
        return deleted
