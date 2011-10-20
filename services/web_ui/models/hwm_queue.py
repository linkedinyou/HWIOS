# -*- coding: utf-8 -*-
"""
    services.web_ui.models.hwm_queue
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A queueing mechanism for websocket messages.
    TODO: Actually make it work

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

from core.application import HWIOS

class HWM_Queue(object):
    """Queueing mechanism for the websocket. Not functional yet"""
    
    data_retrieved = 0.0
    images_retrieved = 0
    message_list = []

    def __init__(self):
        self.sem = defer.DeferredSemaphore(10)
            
    def push_to_transport(self,transport, message):
        transport.write(HWIOS.tools.json_encode(message))
        
        
    def _process(self, transport, message):
        """Think i wanted to write some non-blocking way of processing a message list here"""
        self.message_list.append(message)
        deferreds = []
        #if len(self.message_list) == 1 and not self.message_list[0].has_key('image_loc'):
        #    self.message_list[0]['data'] = ''
        #    return self.cb_class.queue_finished(self.message_list)
        #else:
        self.clients = HWIOS.ws_realm.pool.get_clients()
        for index, message in enumerate(self.message_list):
            deferreds.append(self.sem.run(self.push_to_transport, transport, message))
            deferreds[-1].addCallback(self.push_status,index)
            deferreds[-1].addErrback(self.push_error,index)
        if len(deferreds) > 0:
            dl = defer.DeferredList(deferreds)
            dl.addCallback(self.finish)

    def _push_status(self,result,queue_number):
        """Queue reported status"""
        if result:
            self.message_list[queue_number]['data'] = result
            self.data_retrieved +=float((len(result)/1024))
            self.images_retrieved +=1
            if self.data_retrieved < 1024:
                sys.stdout.write('\r%s images retrieved (%.4gkb)' % (self.images_retrieved,self.data_retrieved))
            else:
                sys.stdout.write('\r%s images retrieved (%.4gmb)' % (self.images_retrieved,self.data_retrieved/1024))
            sys.stdout.flush()
        else:
            self.message_list[queue_number]['data'] = ''
        
    def _push_error(self,result,queue_number):
        """Queue reported an error"""
        sys.stdout.write('Queue worker %s reported an error: %s\n' % (queue_number,result.getErrorMessage()))
        #self.message_list[queue_number]['data'] = '-1'

    def finish(self,results=False):
        """Queue is finished"""
        pass
        #self.cb_class.queue_finished(self.message_list)