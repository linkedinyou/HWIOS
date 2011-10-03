# -*- coding: utf-8 -*-
"""
    services.web_ui.models.profiles
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The model description for the blogging module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import uuid, random, hashlib

from django.db import models 
from django.contrib.auth.models import User

import web_ui.settings as settings

web_ui = __import__('web_ui.auth.%s' % settings.AUTHENTICATION_CONFIG)
auth_load = getattr(web_ui.auth,settings.AUTHENTICATION_CONFIG)


class Profile(User):
    '''
    HWIOS profile model object

    Extends django's default user object with custom fields and functionality like
    modified authentication.

    '''
    uuid = models.CharField(editable = False,  max_length=36)
    organisation = models.CharField(max_length=36)
    timezone = models.CharField(max_length=50, default='Europe/Amsterdam')
    photo = models.TextField()
    karma = models.IntegerField(default=1)
    ip = models.IPAddressField(blank=True)
    salt = models.CharField(max_length=36)
    about = models.TextField()
    
    objects = getattr(auth_load,'XAuthManager')()
    
    class Meta:
        db_table = 'auth_user_profiles'
        app_label = 'no_fixture'
        verbose_name = 'profile'


    def set_password(self, raw_password):
        pwsalt ='%016x' % random.getrandbits(128)
        pwhash = hashlib.md5('%s:%s' % (hashlib.md5(raw_password).hexdigest(),pwsalt)).hexdigest()
        self.password = pwhash
        self.salt = pwsalt
