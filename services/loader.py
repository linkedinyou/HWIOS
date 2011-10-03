# -*- coding: utf-8 -*-
"""
    services.loader
    ~~~~~~~~~~~~~~~

    Automated loader of all services in this directory. Keep the convention used by other services...

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import os,sys
HWIOS_ROOT = os.environ['HWIOS_ROOT']
from ConfigParser import ConfigParser

from hwios.core.application import HWIOS

class ServiceLoader(object):
    """Automated service loader for HWIOS"""
    
    def __init__(self, hwios_config):
        service_reference = self.find_services()
        for service in service_reference:
            _temp = __import__(service['module'], globals(), locals(), [service['class']], -1)
            service_config = ConfigParser()
            service_config.location = os.path.join(HWIOS_ROOT,'services',service['dir'])
            service_config.read(os.path.join(service_config.location,'service.ini'))
            
            HWIOS.services[service['dir']] = getattr(_temp,service['class'])(service_config,hwios_config)
            twisted_server = HWIOS.services[service['dir']].get_service()
            twisted_server.setServiceParent(HWIOS.service_collection)


    def find_services(self):
        """Search for services in the service path, and setup their classname, based on some basic conventions

        :return: list - A list of information about services
        """
        services = []
        for f in os.listdir(os.path.join(HWIOS_ROOT,'services/')):
            if os.path.isdir(os.path.join('services',f)):
                module = '%s.service' % f
                class_name = '%sService' % f.capitalize()
                services.append({'module':module,'class':class_name,'dir':f})
        return services

