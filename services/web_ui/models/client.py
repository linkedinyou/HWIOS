# -*- coding: utf-8 -*-
"""
    services.web_ui.models.clients
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Defines the general Client object that keeps state between HTTP and Websocket mode

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
from twisted.python import failure, log

from hwios.core.application import HWIOS

class Client(object):
    """
    The Client objects describes a general user-entity that's available in both HTTP and Websocket mode
    """
    
    def __init__(self, profile, session, language):
        self.profile = profile
        self.session = session
        self.language = language
    
    
    def set_transport(self, transport):
        """Sets the Client's tcp transport reference

        :param transport transport: The websocket tcp transport
        """
        self.transport = transport 
        
    
    def remote(self, method_url, params = None):
        """Sends json-encoded method-data in HWM-format to this client.

        :param str method_url: The client-side method-url to route to
        :param params: Either a dict or a list to use as parameters for the client-side method

        """
        log.msg('%s WS/76/HRM' % (method_url),system='%s,OUT' % self.transport.getPeer().host)
        self.transport.write(HWIOS.tools.json_encode([method_url, params]))


    def set_uri(self, uri):
        """Sets the client's current tracked view

        :param str uri: The uri to set the view to
        
        """
        self.transport.view_history.append(uri)
        return uri