# -*- coding: utf-8 -*-
"""
    services.web_ui.models.clients
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Defines the general Client object that keeps state between HTTP and Websocket mode

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
from twisted.python import failure, log
from twisted.names.client import lookupPointer
from twisted.internet import defer

from django.contrib.gis.utils import GeoIP
from core.application import HWIOS
from web_ui import settings

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


    def get_ip(self, force_wanip = False):
        #either lan or wan ip
        _ip = self.transport.getPeer().host
        #accessed from LAN, make distinction between wan/lan
        if _ip.startswith('192.168.') or _ip.startswith('10.0.'):
            lan_ip = self.transport.getPeer().host
            wan_ip = settings.HWIOS_WANIP
        else:
            wan_ip = self.transport.getPeer().host       
        #we need a clean wan-ip here
        if force_wanip:
            if '192.168.' or '10.0.' in _ip:
                return settings.HWIOS_WANIP
            else:
                return self.transport.getPeer().host
        else:
            if '192.168.' or '10.0.' in _ip:                
                return '%s - %s' % (lan_ip, wan_ip)
            else:
                return wan_ip

            
    def _gotReverseLookupResult(self, (answers, authority, additional)):
        return answers[0].payload.name
        
        
    def _reverse_IPv4_lookup(self, ipString):
        """
        @param ipString: dotted-quad IP address.
        """
        parts = ipString.split('.')
        parts.reverse()
        host = '.'.join(parts) + '.in-addr.arpa'
        return lookupPointer(host).addCallback(self._gotReverseLookupResult)
        
        
    @defer.inlineCallbacks
    def get_hostname(self):
        result = yield self._reverse_IPv4_lookup(self.get_ip(force_wanip = True))
        defer.returnValue(result)


    def get_geoip(self):
        g = GeoIP()
        return g.city(self.get_ip(force_wanip = True))
        