# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.http.profiles
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    HTTP controller for profile related methods(login/logout)

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import os
import random

from django.contrib.auth.decorators import user_passes_test
from django.template import RequestContext
from django.template.loader import render_to_string
from django.template import Context, Template
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login, logout
from django.core import mail
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from hwios.core.application import HWIOS
from hwios.core.tools import JSONResponse

from web_ui.models.settings import Settings
from web_ui.models.profiles import Profile

from web_ui.models.menu import Menu
from web_ui.forms.profiles import LoginForm
from web_ui.models.activity import *


def login_profile(request):    
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            profile = authenticate(username= username, password = password, options = {'profile':Profile})
            #something is wrong with our webclient module
            if type(profile).__name__ == 'HttpResponseServerError': return profile
            elif profile != None:
                if profile.is_active == 1:
                    login(request, profile)
                    _client_user = {
                        'id':profile.pk,
                        'name':profile.username,
                    }
                    navbar = render_to_string('misc/navigation.html', {'menu': Menu(request.user).render()}, context_instance=RequestContext(request))
                    response = {
                        'status':{
                            'code':'CRED_OK',
                            'i18n':_('Succesfully logged in!'),
                            'type': HWIOS.ws_realm._t['notify-info']
                        },
                        'data':{'user': _client_user,'dom':{'navbar':navbar}}}
                    publish_activity(profile, _('Profile login'),'/profiles/%s/' % (profile.username),[0,1,1,0,0])
                else:
                    dialog = render_to_string('profiles/login.html', {'form': form}, context_instance=RequestContext(request))
                    response = {
                        'status':{
                            'code':'CRED_INACTIVE',
                            'i18n':_('Your account has not been activated yet...'),
                            'type': HWIOS.ws_realm._t['notify-warning']
                        },
                        'data':{'dom':{'dialog':dialog}}
                    }
                return JSONResponse(response)
            else:
                dialog = render_to_string('profiles/login.html', {'form': form}, context_instance=RequestContext(request))
                response = {
                    'status':{
                        'code':'CRED_FAILED',
                        'i18n':_('Invalid user/password entered...'),
                        'type': HWIOS.ws_realm._t['notify-warning']
                    },
                    'data':{'dom':{'dialog':dialog}}
                }
                return JSONResponse(response)
        else:
            dialog = render_to_string('profiles/login.html', {'form': form}, context_instance=RequestContext(request))
            response = {
                'status':{
                    'code':'FORM_INVALID',
                    'i18n':_('Invalid form input!'),
                    'type': HWIOS.ws_realm._t['notify-warning']
                },
                'data':{'dom':{'dialog':dialog}}
            }
            return JSONResponse(response)
            
            
def logout_profile(request):
    profile = request.user.profile
    publish_activity(profile, _('Profile logout'),'/profiles/%s/' % (profile.username),[0,1,1,0,0])
    logout(request)
    menu = Menu(request.user).render()
    navbar = render_to_string('misc/navigation.html', {'menu': menu}, context_instance=RequestContext(request))
    request.session['language'] = request.META['HTTP_ACCEPT_LANGUAGE'].split(',')[0]
    request.session['id'] = random.randint(1000,9999)
    response = {
        'status':{
            'code':'LOGOUT_OK',
            'i18n':_('You just logged out. Thank you for visiting...'),
            'type': HWIOS.ws_realm._t['notify-info'],
            'state': '/blog/'
        },
        'data':{
            'dom':{'navbar':navbar},
            'user':{'id':request.session['id']}
        }
    }
    return JSONResponse(response)
    

#helper function
def _load_personal(request):
    profiles = Profile.objects.all()
    luggage = Luggage.get_luggage()
    online_simulators = Simulators.get_simulators(online=True)
    main = render_to_string("profiles/read_profiles.html", {'profiles':Profile.objects.all(),'luggage':luggage,'online_simulators':len(online_simulators)}, context_instance=RequestContext(request))
    return {'data':{'dom':{'main':main}}}   