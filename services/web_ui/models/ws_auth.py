# -*- coding: utf-8 -*-
"""
    services.web_ui.models.ws_auth
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Simple django authentication decorator

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from web_ui.models.profiles import Profile

class WSAuth(object):
    """The decorator class for authentication"""
    
    @classmethod
    def is_authenticated(cls,fn):
        """Check if the view's client is authenticated or not"""
        def new(self, client,*args,**kwargs):
            if client.profile.is_authenticated == True:
                return fn(self, client,*args,**kwargs)
            else: 
                return None
        new.__doc__ = fn.__doc__
        return new
        
    @classmethod
    def is_staff(cls,fn):
        """Check if the view's client is staff or not"""
        def new(self, client,*args,**kwargs):
            if client.profile.is_staff:
                return fn(self, client,*args,**kwargs)
            else: return None
        new.__doc__ = fn.__doc__
        return new