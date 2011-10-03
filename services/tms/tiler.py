# -*- coding: utf-8 -*-
"""
    services.tms.tiler
    ~~~~~~~~~~~~~~~~~~

    Provides an efficient tiling algorithm to render world-scale map-cells. 

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import ConfigParser, os, sys, time
import urllib
import re
import StringIO
import math
import shutil

from twisted.internet import reactor

from processor import Processor
from grabber import Grabber
from twisted.internet import defer
from web_ui.models.opensim import Regions

class Tiler(object):
    """The tiler class handling the grabbing, processing and tiling of maptiles like opensim regions"""
    countRegion = 0
    countComposite = 0
    cell_list = []
    
    def __init__(self, config):
        self.start_time = time.time()
        self.config = config
        self.processor = Processor(config)
        if not self.processor.valid:
            print 'Selected processor "%s" failed to initialize!\nValid options are PIL & PythonMagick...' % self.config.get('map','processor')
            
        
    def _clean_tilepath(self):
        """Clean and remove the whole tms filepath structure"""
        if os.path.isdir(self.config.tilepath): 
            shutil.rmtree(self.config.tilepath, True)
        try:
            os.mkdir(self.config.tilepath)
            if self.config.getboolean('service','ll_support'):
                os.mkdir(os.path.join(self.config.tilepath,'ll'))
        except OSError:
            print 'No permission to write tiles...'
            

    def _get_regions_from_dsm(self):
        """Get the region information from teknon dsm

        :return: list - A list of cell-information from dsm

        """
        region_services = Regions().get_region_services()
        cell_info = []
        for service in region_services:
            port = service['port']
            for region in service['regions']:
                image_loc = 'http://%s:%s/index.php?method=regionImage%s' % (region['ExternalHostName'], port, region['RegionUUID'].replace('-', ''))
                cell_info.append({'image_loc':image_loc,'x':float(int(region['Location'].split(',')[0])),'y':float(int(region['Location'].split(',')[1]))})
        return cell_info
        

    def _get_regions_from_apache_dir(self,url):
        """Was used to test an osgrid map rendering from an apache webdir

        :param str url: The url the apache webdir is accessible from
        :return: list - A list of cell-information from an apache directory
        """
        print 'Analysing apache web-directory...'
        cell_info = []
        total_image_data = 0
        parse_re = re.compile('href="([^"]*)".*(..-...-.... ..:..).*?(\d+[^\s<]*|-)')
        try:
            html = urllib.urlopen(url).read()
        except IOError, e:
            print 'error fetching %s: %s' % (url, e)
            return
        if not url.endswith('/'):
            url += '/'
        files = parse_re.findall(html)
        dirs = []
        for name, date, size in files:
            if size.strip() == '-':
                size = 'dir'
            if name.endswith('/'):
                dirs += [name]
            image_loc = url + name
            name = name.split('-')
            data = {'image_loc':image_loc,'x':float(int(name[2])),'y':float(int(name[3]))}
            cell_info.append(data)
            if size[0:-1]:
                total_image_data += float(size[0:-1])
        print 'Retrieving %s images (%.4gmb)' % (len(files),total_image_data / 1024)
        return cell_info
        
        
    def init_map(self,fromsettings=False):
        """Initializes the map

        :param bool fromsettings: Some ancient setting probably. Don't think it's used anymore
        :return: list - A list of cell-information
        """
        self.config.read(os.path.join(self.config.location,'service.ini'))
        if self.config.getboolean('map','osm'):
            self.ztop = self.config.getint('map','osm_ztop')
            if self.config.getint('map','zlevels') < self.ztop: 
                self.zlevels = self.config.getint('map','zlevels')
            else:
                self.zlevels = 10
        else:
            #We use a predefined grid-size for the sake of keeping new regions within the current boundaries
            if self.config.has_option('map','raw_ztop'):
                self.ztop = self.config.getint('map','raw_ztop')
            #If not defined, try to get the boundaries from the current regions
            else:
                locx_list = locy_list = []
                for cell in self.cell_list:
                    locx_list.append(cell['x'])
                    locy_list.append(cell['y'])
                locx_list = sorted(locx_list)
                locy_list = sorted(locy_list)
                if locx_list[-1] < locy_list[-1]: peak=int(locy_list[-1])
                else: peak=int(locx_list[-1])
                self.ztop = int(math.ceil(math.log(peak, 2)))
            #We will impose a minimum of 6 zoom levels
            if self.ztop < 5: self.ztop = 5
            gridsize = int(math.pow(2,self.ztop))
            #Make sure that the amount of zoomlevels never exceeds the top zoom
            self.zlevels = self.ztop
            print 'Raw map initialization. Setting mapspace to  %s zlevels on a %sx%s grid...' % (self.zlevels,gridsize,gridsize)
        self.config.set('map','zlevels',self.zlevels)
        self.config.set('map','raw_ztop',self.ztop)
        for count,cell in enumerate(self.cell_list):
            self.cell_list[count]['z'] = {self.ztop:{'x':float(cell['x']),'y':float(cell['y'])}}
        self.config.set('map','cache',int(time.time()))
        self.config.write(open(os.path.join(self.config.location,'service.ini'),'wb'))
        self.config.read(os.path.join(self.config.location,'service.ini'))
        return self.cell_list
        
        
    def process_queue(self):
        """Starts to render a queue of cell-information

        :return: dict - Cell-information
        """
        map_fromsettings = True
        if not self.cell_list:
            self.cell_list = []
            if self.config.get('map','render_from') == 'webdir':
                self.cell_list.extend(self._get_regions_from_apache_dir(self.config.get('service','render_webdir')))
            elif self.config.get('map','render_from') == 'dsm':
                self.cell_list.extend(self._get_regions_from_dsm())
            else:
                print 'select a valid(db/webdir) scavenging method!'
                return
            self._clean_tilepath()
            self.processor.write_helpers()
            map_fromsettings = False
        self.init_map(map_fromsettings)
        grabber = Grabber(self,self.config.getint('service','grab_workers'))
        grabber.grab(self.cell_list)
        return {'cells':len(self.cell_list)}
        
        
    def queue_finished(self,cell_list):
        """Called when the queue is empty and all grabbing has been done

        :param list cell_list: The cell_list that has been rendered
        """
        self.queue_time = (time.time() - self.start_time) 
        if self.queue_time < 60:
            print '\nQueued: %s cells in %.2g seconds' % (len(cell_list),self.queue_time)
        else:
            print '\nQueued: %s cells in %.2g minutes' % (len(cell_list),self.queue_time/60)
        print 'Starting rendering process. Please wait...'
        d = self.render_cell()
        

    def render_cell(self):
        """The actual algorithm. It takes shortcuts by using existing zoom-level tiles where possible for composition"""
        subdx = subdy = 0
        for z in xrange(self.ztop,self.ztop-self.zlevels,-1):
            for count, cell in enumerate(self.cell_list):
                if z == self.ztop:
                    if len(cell['data']) == 0: image = self.processor.get_image()
                    elif cell['data'] == '-1': image = self.processor.offline_image
                    else: image = self.processor.get_image(data=cell['data'])
                    #WRITE
                    self.processor.write_tile(image,z,cell)
                    self.countRegion += 1
                else:
                    self.cell_list[count]['z'][z] = {'x': self.cell_list[count]['z'][z+1]['x'] / 2, 'y': self.cell_list[count]['z'][z+1]['y'] / 2}
                    dx = 0
                    zx = int(self.cell_list[count]['z'][z+1]['x'])
                    #WRITE CHECK
                    if os.path.isfile('%s.%s' % (os.path.join(self.config.tilepath,str(z),str(int(cell['z'][z]['x'])),str(int(cell['z'][z]['y']))),self.config.get('map','format'))):
                        canvas = self.processor.get_image(file=[z,cell['z'][z]['x'],cell['z'][z]['y']])
                    else:
                        canvas = self.processor.get_image()
                    for zx in xrange(zx, zx + 2,  +1):
                        dy = 0
                        zy = int(self.cell_list[count]['z'][z+1]['y'])
                        for zy in xrange(zy, zy + 2,  +1):
                            #WRITE CHECK
                            if os.path.isfile('%s.%s' % (os.path.join(self.config.tilepath,str(z+1),str(zx),str(zy)),self.config.get('map','format'))):
                                image = self.processor.get_image(file=[z+1,zx,zy])
                                image = self.processor.resize_image(image,128,128)
                                if self.cell_list[count]['z'][z]['x']%1 >= 0.5: subdx = 128
                                else: subdx = 0
                                if self.cell_list[count]['z'][z]['y']%1 >= 0.5: subdy = 128
                                else: subdy = 0
                                self.processor.compose_image(canvas,image,(128*dx+subdx),(128*dy+subdy))
                                self.countComposite += 1
                            dy+=1
                        dx+=1
                    #WRITE
                    self.processor.write_tile(canvas,z,cell)
        self.render_finished({'cells':self.countRegion,'composites':self.countComposite})
        
        
    def render_finished(self,results):
        """Called when the queue is empty and all cell-rendering has been done

        :param dict results: General information about the rendered cells
        """
        self.end_time = (time.time() - self.start_time) 
        if self.end_time < 60:
            print 'Composited: %s/%s (%s composites/cell) in %.5g seconds (%.5g seconds/cell)' % (results['composites'],results['cells'],results['composites']/results['cells'],self.end_time,self.end_time/results['cells'])
        else:
            print 'Composited: %s/%s (%s composites/cell) in %.5g minutes (%.5g seconds/cell)' % (results['composites'],results['cells'],results['composites']/results['cells'],self.end_time/60,self.end_time/results['cells'])
        #clean cell-list
        self.cell_list = []