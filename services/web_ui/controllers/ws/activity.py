# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.activity
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Websocket controller for user website activity 

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from hwios.core.application import HWIOS

from web_ui.models.activity import Activity, ACTIVITY_CSS
from web_ui.models.ws_auth import WSAuth
from web_ui.models.signal import Signal




class WS_Activity(object):


    def __init__(self, dispatcher):
        pass


    def get_activities(self, client):
        if client.profile.is_staff:            
            activities = Activity.objects.filter(action_moderators__range=(1,4))[:50]
        elif client.profile.is_authenticated:
            activities = Activity.objects.filter(action_users__range=(1,4))[:50]
        else:
            activities = Activity.objects.filter(action_all__range=(1,4))[:50]
            
        for activity in activities:
            action_css = ACTIVITY_CSS[activity.action_all]
            if client.profile.is_staff:
                action_css = ACTIVITY_CSS[activity.action_moderators]
            elif client.profile.is_authenticated:
                action_css = ACTIVITY_CSS[activity.action_users]
            setattr(activity,'action_css', action_css)
        tpl_activity = render_to_string("activity/view_activities.html", {"activities":activities,'profile':client.profile})
        return {'data':{'dom':{'activity':tpl_activity}}}
        