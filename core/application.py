# -*- coding: utf-8 -*-
"""
    core.application
    ~~~~~~~~~~~~~~~~

    Defines the main namespace for the application: "HWIOS"

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""


from tools import Tools

class HWIOS(object):
    """The general HWIOS namespace to keep things available through the whole application"""
    services = {}
    tools = Tools()
    
    @classmethod
    def set_value(self,value):
        self.foo = value
    
    @classmethod
    def get_value(self):
        return self.foo


