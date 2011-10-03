# -*- coding: utf-8 -*-
"""
    services.dsm.dsm_server
    ~~~~~~~~~~~~~~~~~~~~~~~

    The dsm teknon daemon server that keeps a pool of connected teknon clients

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import uuid
import sys
import re 
import ConfigParser

from zope.interface import implements
from django.contrib.auth import authenticate, login
from twisted.spread.pb import Avatar,IPerspective, PBServerFactory,Viewable
from twisted.internet import defer, stdio, protocol, reactor
from twisted.protocols import basic
from twisted.cred.portal import IRealm, Portal
from twisted.cred.checkers import ANONYMOUS, AllowAnonymousAccess,InMemoryUsernamePasswordDatabaseDontUse
from twisted.application import service, internet
from twisted.cred import error
from twisted.cred.credentials import IUsernameHashedPassword, IUsernamePassword
from twisted.cred.checkers import ICredentialsChecker
from twisted.spread.flavors import Referenceable, NoSuchMethod
from twisted.spread.pb import _JellyableAvatarMixin,_PortalRoot
from twisted.spread.flavors import Root, IPBRoot

from web_ui.models.profiles import Profile
from django.core.exceptions import ObjectDoesNotExist
from twisted.internet.defer import Deferred


class DSMPortalRoot:
    """Custom portal root that allows username/password authentication"""
    implements(IPBRoot)

    def __init__(self,portal):
        self.portal = portal

    def rootObject(self, broker):
        """Set the rootobject of the portal

        :param Broker broker: The twisted broker to use
        """
        return _DSMPortalWrapper(self.portal, broker)        
        
class _DSMPortalWrapper(Referenceable, _JellyableAvatarMixin):    
    """Custom portal wrapper that allows username/password authentication"""
    implements(IUsernamePassword)    
    def __init__(self, portal, broker):
        self.portal = portal
        self.broker = broker
        
    def remote_login(self, username, password, mind):
        """override default login mechanism

        :param str username: Username the client will send
        :param str password: Raw password the client will send
        :param Mind mind: The Twisted mind to use
        """
        self.username = username
        self.password = password
        d = self.portal.login(self, mind, IPerspective)
        d.addCallback(self._cbLogin)
        return d     
        
        
class DSMCredChecker(Referenceable, _JellyableAvatarMixin):
    """Django cred-checker for PB provides hwios django authentication"""
    implements(ICredentialsChecker)

    def __init__(self, hash= None, caseSensitive=False):
        self.credentialInterfaces = (IUsernameHashedPassword,IUsernamePassword,)        

    def requestAvatarId(self, c):
        """Client sent login-request. Handle it against django's authentication

        :param object c: the object representing the user login
        """
        password = str.strip(c.password)        
        deferred = Deferred()
        user = authenticate(username=c.username, password = password)
        if user != None:
            if user.is_staff:
                deferred.callback(c.username)
            else:
               deferred.errback(error.LoginDenied('Only staff users are allowed to attach Teknon clients!'))
        else:
           deferred.errback(error.LoginDenied('Invalid Credentials'))
        return deferred
        
    def __getstate__(self):
        return dict(vars(self)) 


class DSMRealm(object):
    """Takes care of logging the avatar into the realm"""
    implements(IRealm)
    def requestAvatar(self,avatarID,mind,*interfaces):
        """Some funky twisted way of handling the login"""
        if IPerspective  in interfaces:
            assert IPerspective in interfaces
            avatar = Client(avatarID)
            avatar.server = self.server
            avatar.attached(mind)
            return IPerspective, avatar, lambda a=avatar:a.detached(mind)
        else:
            raise NotImplementedError("Only pb.IPerspective interface is supported by this realm")
        
        
class Client(Avatar):
    """The teknon can call these remote functions"""
    def __init__(self,name):
        self.name = name
        self.services = []
        
        
    def attached(self,mind):
        """Client logged into the mind. Force join client-group

        :param Mind mind: The twisted mind to login to
        """
        self.remote = mind
        self.init_client_state()
        self.server.joinClientGroup('CLIENTS',self, True)
        
        
    def detached(self,mind):
        """Client logged out of the mind. Force depart client-group

        :param Mind mind: The twisted mind to logout from
        """
        self.server.departClientGroup('CLIENTS',self, True)
        self.remote = None
        
        
    def send(self, command):
        """Some dummy send function, Not really used actually.

        :param str command: Sends a command to the teknon client
        """
        self.remote.callRemote("print",command)
        
        
    def joined_group(self,name):
        """Notify of client joining a group. Not really used actually.

        :param str name: The group-name that's being joined
        """
        self.remote.callRemote('joined_group',name)
        
        
    def perspective_from_console(self,service_uuid,output):
        """Routes a teknon service stdout update through the websocket dispatcher

        :param str service_uuid: The service uuid that the console update is coming from
        :param str output: The stdout update from the teknon service
        """
        self.server.connector.dispatch('/data/teknon/services/%s/proxy_stdout/' % service_uuid,{'output':output})
        
        
    def perspective_update_client_state(self, client_state):
        """Routes a teknon service status update through the websocket dispatcher

        :param list client_state: A list of teknon services with their actual status
        """
        self.services = client_state['services']
        self.region_services = client_state['region_services']
        #proxy service_state to connector
        self.server.connector.dispatch('/data/teknon/services/state/update/',{'services':self.services})
        
        
    @defer.inlineCallbacks
    def init_client_state(self):
        """Setup the client's initial information at the serverside"""
        client_state = yield self.remote.callRemote('get_client_state')
        self.services = client_state['services']
        self.region_services = client_state['region_services']
        self.uuid = client_state['client_uuid']
        self.peer = self.remote.broker.transport.getPeer()
        self.server.connector.dispatch('/data/teknon/',{})
        #self.server.connector.notify({'status':{'code':'NEW_CLIENT'},'client':{'host':('%s:%s') % (self.peer.host,self.peer.port),'uuid':self.uuid,'name':self.name}})
        
        
    @defer.inlineCallbacks
    def switch_watchdog(self,service_uuid,status):
        """Switch the service watchdog to ON, OFF or TRIGGER

        :param str service_uuid: The uuid of the service to target
        :param str status: The watchdog status to give this servoce
        """
        response = yield self.remote.callRemote('switch_watchdog',service_uuid,status)
        defer.returnValue(response)
        
    
    @defer.inlineCallbacks
    def command_service(self, service_uuid, command):
        """Sends a command to a service running on this client

        :param str service_uuid: The uuid of the service to target
        :param str command: The command to pipe into the service
        """
        response = yield self.remote.callRemote('command_service',str(service_uuid),str(command))
        defer.returnValue(response)
        
        
    @defer.inlineCallbacks
    def get_sim_slave_ini(self,service_uuid):
        """Loads the simulator's ini file

        :param str service_uuid: The uuid of the service to target
        """

        response = yield self.remote.callRemote('get_sim_slave_ini',service_uuid)
        defer.returnValue(response)
        
        
    @defer.inlineCallbacks
    def save_slave_sim_ini(self,service_uuid, data):
        """Saves the simulator's ini file

        :param str service_uuid: The uuid of the service to target
        :param str data: The new simulator ini file
        """
        response = yield self.remote.callRemote('save_slave_sim_ini', service_uuid, data)
        defer.returnValue(response)
        
        
    @defer.inlineCallbacks
    def switch_service(self,service_uuid,to_state):
        """Switch a service ON, OFF or KILL

        :param str service_uuid: The uuid of the service to target
        :param str to_state: The state to set this service to
        """
        response = yield self.remote.callRemote('switch_service', service_uuid, to_state)
        defer.returnValue(response)
        
        
    @defer.inlineCallbacks
    def backup_region(self,service_uuid,region_uuid, name):
        """Saves an oar to the webdav share defined in Teknon client

        :param str service_uuid: The uuid of the service to target
        :param str region_uuid: The uuid of the region to target
        :param str name: The filename for this oar-file
        """
        response = yield self.remote.callRemote('backup_region',service_uuid, region_uuid, name)
        defer.returnValue(response)
        
        
    @defer.inlineCallbacks
    def load_scene(self,service_uuid,region_uuid, name):
        """Loads an oar from the webdav share defined in Teknon client

        :param str service_uuid: The uuid of the service to target
        :param str region_uuid: The uuid of the region to target
        :param str name: The filename of the oar-file to load
        """
        response = yield self.remote.callRemote('load_scene',service_uuid, region_uuid, name)
        defer.returnValue(response)        
        
        
    @defer.inlineCallbacks
    def load_luggage(self,service_uuid, avatar, inventory_path, archive_file):
        """Loads a luggage file from the webdav share defined in Teknon client

        :param str service_uuid: The uuid of the service to target
        :param str avatar: The avatar name to which to load the luggage into
        :param str inventory_path: The internal opensim inventory path to use
        :param str archive_file: The archive file to load from
        """
        response = yield self.remote.callRemote('load_luggage',service_uuid, avatar, inventory_path, archive_file)
        defer.returnValue(response)
        
        
    @defer.inlineCallbacks
    def backup_luggage(self,service_uuid, avatar, inventory_path, archive_file):
        """Saves an IAR luggage file to the webdav share defined in Teknon client

        :param str service_uuid: The uuid of the service to target
        :param str avatar: The avatar name to which to load the luggage into
        :param str inventory_path: The internal opensim inventory path to use
        :param str archive_file: The archive file to load from
        """
        response = yield self.remote.callRemote('backup_luggage',service_uuid, avatar, inventory_path, archive_file)
        defer.returnValue(response)
        
    
class ClientGroup(Viewable):
    """Each client-group has the following commands available"""
    def __init__(self,service_uuid, allowMattress):
        self.name = service_uuid
        self.allowMattress = allowMattress
        self.clients = []
        
    def addClient(self,client):
        """Adds a new client to this group

        :param Client client: The client to add
        """
        self.clients.append(client)
        client.joined_group(self.name)
        
    def rmClient(self,client):
        """Removes a client from this group

        :param Client client: The client to remove
        """
        self.clients.remove(client)
        
    def _view_send(self,from_client,command):
        """Deprecated function used for testing teknon messaging"""
        if not self.allowMattress and message.find("mattress") != -1:
            raise ValueError, "Don't say that word"
        for client in self.clients:
            client.send("<%s> says: %s" % (from_client.name, command))


class DSMServer:
    """
    The DSM server main clas used to setup the general logics behind the service
    """
    console_buffer = []
    
    
    def __init__(self,connector = None):
        self.connector = connector
        self.selected_client = None
        self.selected_service = None
        self.clientgroups = {}                     
        self.clientgroups['CLIENTS'] = ClientGroup('CLIENTS', True)
        self.connector.register_server(self)
        
    
    def joinClientGroup(self,name,client,allowMattress):
        """Processes a teknon client that just logged in

        :param str name: the group name to join
        :param Client client: The client that joins the group
        :param bool allowMattress: Some twisted curse-filter?
        """
        if name not in self.clientgroups:
            self.clientgroups[name] = ClientGroup(name, allowMattress)
        self.clientgroups[name].addClient(client)
        self.connector.update_pb_pool(self.clientgroups['CLIENTS'].clients)
        return self.clientgroups[name]
        
        
    def departClientGroup(self,group_name, client, allowMattress):
        """Processes a teknon client that just logged out or broke the connection

        :param str group_name: the group name to leave
        :param Client client: The client that joins the group
        :param bool allowMattress: Some twisted curse-filter?
        """
        self.clientgroups[group_name].rmClient(client)
        self.connector.update_pb_pool(self.clientgroups['CLIENTS'].clients)
        self.connector.dispatch('/data/teknon/',{})
        return self.clientgroups[group_name]
        
        
    def get_clients(self):
        """Get all the teknon clients that are connected
        
        :return: dict - A collection of all teknon clients currently logged in
        """
        return self.clientgroups['CLIENTS'].clients
        

    def search_service(self,service_uuid):
        """Search for a service in the teknon pool

        :param str service_uuid: The uuid of the teknon service to look for
        :return: dict - A collection of all teknon clients and services currently logged in
        """
        for client in self.clientgroups['CLIENTS'].clients:
            for service in client.services:
                if service_uuid in service['uuid']:
                    return {'client':client,'service':service}
        return False
        
        
    def search_client(self,service_uuid = None):
        """Search for a client in the teknon pool

        :param str service_uuid: The uuid of the teknon service to look for
        :return: Client or bool - The client that was found or False
        """
        if service_uuid != None:
            for client in self.clientgroups['CLIENTS'].clients:
                for service in client.services:
                    if service_uuid in service['uuid']:
                        return client
            return False
        
    
    @defer.inlineCallbacks
    def radmin_proxy(self,service_uuid,command,params):
        """Proxies an xmlrpc command to teknon which calls the xmlrpc method locally to the simulator

        :param str service_uuid: The uuid of the teknon service to target
        :param str command: The command to send to the simulator
        :param dict params: The parameters that need to be sent with the command to execute the xmlrpc method
        :return: dict - The result of the xmlrpc call to the simulator
        """
        found = self.search_service(service_uuid)
        if found:
            result = yield found['client'].remote.callRemote('radmin_proxy',service_uuid,command,params)
            defer.returnValue(result)           
