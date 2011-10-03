# -*- coding: utf-8 -*-
"""
    services.web_ui.forms.teknon
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form definitions for the Teknon module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django.db import models
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm
from datetime import datetime

SERVICE_TYPES = (
    (0, 'StandAlone Vanilla'),
    (1, 'StandAlone ModRex'),
    (2, 'ROBUST Service'),
    (3, 'User Service'),
    (4, 'Grid Service'),
    (5, 'ModRex Service'),
    (6, 'Vanilla Simulator'),
    (7, 'ModRex Simulator'),
    (8, 'Maps Service'),
    (9, 'Unknown'),
)

class BackendOnlineServiceIniForm(forms.Form):
    user_settings = forms.CharField(widget=forms.Textarea())
    restart_service = forms.BooleanField(initial=True)
    

class BackendOfflineServiceIniForm(forms.Form):
    user_settings = forms.CharField(widget=forms.Textarea())
