# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.http.misc
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    General http controller managing the bootstrap and all general non-websocket http traffic

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import os, sys
import random

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser


from web_ui.models.elFinder import connector

from core.application import HWIOS
from core.tools import JSONResponse
from web_ui.models.settings import Settings
from web_ui.models.menu import Menu
from web_ui.models.client import Client
from web_ui.models.statics import *

import web_ui.settings


def index(request):
    """
    Bootstrap HTTP Call. Set client container and return settings
    """
    try:
        request.session['language'] = request.META['HTTP_ACCEPT_LANGUAGE'].split(',')[0]
    except KeyError:
        request.session['language'] = 'en_us'
    if web_ui.settings.DEBUG:
        script_path = '/media/scripts/'
        css_target = 'hwios_debug.css'
    else:
        script_path = '/media/scripts/deploy/'
        css_target = 'hwios_deploy.css'
    settings = Settings.objects.all()[0]     
    #user should be able to override this, based on it's session settings at some point
    theme = settings.default_template
    if isinstance(request.user, AnonymousUser):
        #i know this is ugly ok?
        request.user.id = random.randint(1000,9999)
        request.session['id'] = request.user.id
    client_init = {'settings':{
        'services':{},
        'user':{
            'id':request.user.id,
            'is_authenticated': request.user.is_authenticated()
        },
        'tt':ws_table
        }
    }
    client_init['settings']['services']['tms'] = HWIOS.services['tms'].get_client_settings()
    client_init['settings']['services']['web_ui'] = HWIOS.services['web_ui'].get_client_settings()
    client_init = HWIOS.tools.json_encode(client_init)
    menu = Menu(request.user).render()
    return render_to_response("misc/base.html",{
        'client_init':client_init,
        'theme': theme,
        'menu':menu,
        'script_path':script_path,
        'css_target': css_target},
        context_instance=RequestContext(request))
    

def splash(request):
    regions = Regions.get_regions()    
    return render_to_response("misc/splash.html",{
                            'settings': HWIOS.services['web_ui'].get_client_settings(),'show_status':None,
                            }, context_instance=RequestContext(request))


def bad_browser(request):
    if request.method == 'POST':
        dialog = render_to_string('misc/bad_browser.html', {'code': request.POST['code']}, context_instance=RequestContext(request))
        response = {
            'status':{
                'code':'BAD_BROWSER',
                'i18n':_('Oops! You are using an incompatible browser...'),
                'type': HWIOS.ws_realm._t['notify-warning']
                },
                'data':{'dom':{'dialog':dialog}
                }
        }
        return JSONResponse(response)


'''Author
=======
Dmitry Shapoval <dmitry@0fe.ru>

License:
========
django-elfinder is issued under a LGPL Version 3 license.
django-elfinder includes parts of elFinder, which is covered by the 3-clauses BSD license.
"""
'''
def elconnector(request):
    finder = connector({'URL':'/media/files/',
    'root':'/home/hwios/hwios/services/web_ui/media/files/',
    'tmbDir':'.tmb',
    'imgLib':'PIL'})

    if request.POST:
        if "cmd" in request.POST and request.POST["cmd"] == "upload":
            request.POST['upload[]'] = request.FILES.getlist('upload[]')

        finder.run(request.POST)
        return JSONResponse(finder.httpResponse)
    finder.run(request.GET)
    ret = HttpResponse(mimetype=finder.httpHeader["Content-type"])
    if finder.httpHeader["Content-type"] == "application/json":
        ret.content = HWIOS.tools.json_encode(finder.httpResponse)
    else:
        ret.content = finder.httpResponse
    for head in finder.httpHeader:
        if head != "Content-type":
            ret[head] =  finder.httpHeader[head]
    ret.status_code = finder.httpStatusCode
    return ret
'''*********************************************************************************'''  
