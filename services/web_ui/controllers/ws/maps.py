# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.maps
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The websocket logics for the map. This is either going to the opensim module,
    or some code is going from the opensim module. It stays here until then.

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os,sys
import math
from django.core import serializers
from django.template.loader import render_to_string

from hwios.core.application import HWIOS
from web_ui.models.ws_auth import WSAuth
from web_ui.models.profiles import Profile
from web_ui.models.opensim import Regions, Maps
from web_ui.models.settings import Settings


class WS_Maps(object):
    """
    The websocket controller class for the mapping part in opensim
    """
    
    
    def __init__(self, dispatcher):
        pass  
    
    def load_maps(self, client):
        """Render the template for the worldmap to our client

        :param Client client: The requesting client
        :return: dict - Html-layout data response
        """
        main = render_to_string('maps/worldmap.html')
        return {'data':{'dom':{'main':main}}}


    def _lonlat2tile(self, zlevel, lonlat):
        """World offset helper, converts lattitude/longitude coordinates to a grid position

        :param int zlevel: The zoom-level at which to calculate
        :param list lonlat: The coordinates to use
        :return: tuple - The related grid-location 
        """
        tile_x = math.floor((float(lonlat[0])+180)/360 * math.pow(2, zlevel))
        tile_y = math.floor((1 - math.log(math.tan(float(lonlat[1])*math.pi/180) + 1/math.cos(float(lonlat[1]) * math.pi/180))/math.pi)/2 * pow(2, zlevel))
        return (int(tile_x), int(tile_y))
        
        
    def _tile2lonlat(self, zlevel,tile_xy):
        """World offset helper, converts grid position to a lattitude/longitude coordinate

        :param int zlevel: The zoom-level at which to calculate
        :param list tile_xy: The grid-coordinates to use
        :return: tuple - The related lattitude and longitude
        """
        n = math.pow(2, zlevel)
        lon_deg = (tile_xy[0] / n) * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile_xy[1] / n)))
        lat_deg = lat_rad * 180.0 / math.pi
        return (lon_deg,lat_deg)


    def read_cell(self, client,lonlat):
        """Get the position of the client's mouseclick in the map, and return region information if there is a region at that location

        :param Client client: The requesting client
        :param list lonlat: The world-coordinates to lookup
        :return: dict - Coordinate data containing region-information if related
        """
        if HWIOS.services['tms'].config.getboolean('map','osm') == True:
            click = self._lonlat2tile(HWIOS.services['tms'].config.getint('map','osm_ztop'), lonlat)
            self._tile2lonlat(17,click)
        else:
            #openlayers flipped y-coordinates
            click = [int(lonlat[0]/256),abs(int(lonlat[1]/256))-1]
        regions = Regions().get_regions()
        found = False
        for region in regions:
            x = int(region['Location'].split(',')[0])
            y = int(region['Location'].split(',')[1])
            if x == click[0] and y == click[1]:
                found = True
                response = { 'x':click[0],'y':click[1],'lonlat':lonlat,'name':region['name'],'ip':region['ExternalHostName'],'port':region['InternalPort']}
                break
        if not found:
            response = { 'x':click[0],'y':click[1],'lonlat':lonlat}
        return response