# -*- coding: utf-8 -*-
"""
    services.web_ui.forms.maps
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form definitions for the maps module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import uuid
from datetime import datetime

from django.db import models
from django import forms
from django.utils.translation import ugettext_lazy as _


class MapsForm(forms.Form):
    zoom_levels = forms.IntegerField(min_value = 3,  max_value=12)
    openstreetmap = forms.BooleanField()
    offset_lon = forms.FloatField(min_value = 0)
    offset_lat = forms.FloatField(min_value = 0)

