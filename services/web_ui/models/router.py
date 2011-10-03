# -*- coding: utf-8 -*-
"""
    services.web_ui.models.router
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Database router modifications

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import sys

class HWIOSRouter(object):

    def db_for_read(self, model, **hints):
        if hasattr(model,'connection_name'):
            return model.connection_name
        else:
             return "default"

    def db_for_write(self, model, **hints):
        if hasattr(model,'connection_name'):
            return model.connection_name
        else:
            return "default"

    def allow_syncdb(self, db, model):  
        if hasattr(model,'connection_name'):
            return model.connection_name
        else:
            return "default"
            
    def allow_relation(self,obj1, obj2, **hints):
        return True