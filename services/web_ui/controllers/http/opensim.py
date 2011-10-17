# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.http.opensim
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    HTTP controller for opensim upload related methods. Still need to be ported to binary websockets hybi-10...

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import os
import time

from django.contrib.auth.decorators import user_passes_test
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist
from django.template import RequestContext
from django.utils.translation import ugettext as _

from core.application import HWIOS
from core.tools import JSONResponse

import web_ui.settings as settings
from web_ui.models.profiles import Profile
from web_ui.models.opensim import Regions, Scenes
from web_ui.controllers.ws.opensim import OSUserAccounts
from web_ui.models.opensim import Simulators, Luggage

@user_passes_test(lambda u: u.is_staff)
def upload_scenes(request):
    if request.method == "POST":
        file_size = request.META['HTTP_X_FILE_SIZE']
        file_name = request.META['HTTP_X_FILE_NAME']
        location = HWIOS.services['web_ui'].config.location
        content = request.raw_post_data
        f = open(os.path.join(location,'dav_store','oar',file_name), 'w')
        f.write(content)
        scenes = Scenes.get_scenes()
        regions = Regions.get_regions()
        main = render_to_string("opensim/read_regions.html", {'regions': regions,'scenes':scenes}, context_instance=RequestContext(request))
        return JSONResponse({
            'status':{
                'code':'FILE_UPLOADED',
                'i18n':_('File(s) succesfully uploaded'),
                'type': HWIOS.ws_realm._t['notify-warning']
            },
            'data':{'dom':{'main':main}}
        })


@user_passes_test(lambda u: u.is_staff)
def upload_luggage(request):
    if request.method == "POST":
        file_size = request.META['HTTP_X_FILE_SIZE']
        file_name = request.META['HTTP_X_FILE_NAME']
        location = HWIOS.services['web_ui'].config.location
        content = request.raw_post_data
        f = open(os.path.join(location,'dav_store','iar',file_name), 'w')
        f.write(content)
        luggage = Luggage.get_luggage()
        online_simulators = Simulators.get_simulators(online=True)
        response = {
            'status':{
                'code':'FILE_UPLOADED',
                'i18n':'File(s) succesfully uploaded',
                'type': HWIOS.ws_realm._t['notify-info']
                }
        }
        luggage = Luggage.get_luggage()
        online_simulators = Simulators.get_simulators(online=True)
        profiles = OSUserAccounts.objects.using('grid').all()
        main = render_to_string("opensim/read_avatars.html", {'profiles':profiles,'luggage':luggage,'online_simulators':len(online_simulators)})
        response.update({'data':{'dom':{'main':main}}})
        return JSONResponse(response)    
