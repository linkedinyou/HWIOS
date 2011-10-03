# -*- coding: utf-8 -*-
"""
    services.tms.grabber
    ~~~~~~~~~~~~~~~~~~~~

    Grabber is a high-speed async image-grabber that gets the image-data from the simulators

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import sys

from twisted.internet import reactor
from twisted.web.client import getPage
from twisted.internet.defer import DeferredList
from twisted.python import threadable
from twisted.web import resource, server, http
from twisted.internet import defer, protocol, reactor
from twisted.python import log, reflect, failure


class Grabber(object):
    """The grabber class is responsible for managing the async image grabbing"""
    data_retrieved = 0.0
    images_retrieved = 0
    

    def __init__(self,cb_class, workers):
        self.cb_class = cb_class
        self.sem = defer.DeferredSemaphore(workers)
        
            
    def getData(self,url):
        """Some helper function for the grabber deferreds

        :param str url: The url to capture the image from
        :return: def - Twisted getPage function
        """
        return getPage(url, timeout=1)
        
        
    def grab(self,cell_list):
        """Async grabs a list of images, based on supplied cell_data

        :param list cell_list: A list of cells (grid-location and image-url)
        """
        self.cell_list = cell_list
        deferreds = []
        if len(self.cell_list) == 1 and not self.cell_list[0].has_key('image_loc'):
            self.cell_list[0]['data'] = ''
            return self.cb_class.queue_finished(self.cell_list)
        else:
            for count,cell in enumerate(self.cell_list):
                if cell.has_key('image_loc'):
                    deferreds.append(self.sem.run(self.getData, cell['image_loc']))
                    deferreds[-1].addCallback(self.grab_status,count)
                    deferreds[-1].addErrback(self.grab_error,count)
                else:
                    self.cell_list[count]['data'] = ''
            if len(deferreds) > 0:
                dl = defer.DeferredList(deferreds)
                dl.addCallback(self.finish)
                

    def grab_status(self,result,queue_number):
        """Give some stdout feedback while the grabber is doing it's thing
        :param str result: The image-data currently retrieved
        :param int queue_number: The current async worker reference
        """
        if result:
            self.cell_list[queue_number]['data'] = result
            self.data_retrieved +=float((len(result)/1024))
            self.images_retrieved +=1
            if self.data_retrieved < 1024:
                sys.stdout.write('\r%s images retrieved (%.4gkb)' % (self.images_retrieved,self.data_retrieved))
            else:
                sys.stdout.write('\r%s images retrieved (%.4gmb)' % (self.images_retrieved,self.data_retrieved/1024))
            sys.stdout.flush()
        else:
            self.cell_list[queue_number]['data'] = ''
            
        
    def grab_error(self,result,queue_number):
        """Error handler for the grabber

        :param str result: The image-data currently retrieved
        :param int queue_number: The current async worker reference
        """
        sys.stdout.write('Queue worker %s reported an error: %s\n' % (queue_number,result.getErrorMessage()))
        self.cell_list[queue_number]['data'] = '-1'
        

    def finish(self,results=False):
        """Execute the callback function supplied with the Grabber constructor
        :param result results: Doesn't seem to be used atm
        """
        self.cb_class.queue_finished(self.cell_list)
