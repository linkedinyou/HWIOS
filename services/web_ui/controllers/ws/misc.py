# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.misc
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The misc module websocket routing logics

    :copyright: Copyright 2009-2011 OS-Networks.
    :license: BSD, see LICENSE for details.
"""
import os,sys
import math
from django.core import serializers
from django.template.loader import render_to_string

from hwios.core.application import HWIOS
from web_ui.models.ws_auth import WSAuth
from web_ui.models.profiles import Profile


class WS_Misc(object):
    """
    Websocket controller class for the msic module
    """
    
    def __init__(self, dispatcher):
        pass
    
    
    def read_about(self, client):
        """
        Renders and returns the credits demo-page view

        :param Client client: The requesting client
        :return: dict - Html data response
        """
        main = render_to_string("misc/about.html", {})
        return {'data':{'dom':{'main':main}}}