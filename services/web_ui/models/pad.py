# -*- coding: utf-8 -*-
"""
    services.web_ui.models.pad
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    General Pad model

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import uuid
from django.db import models 


class Pad(models.Model):
    """ORM Model for pad drawings"""
    uuid = models.CharField(max_length=36,  primary_key=True, default=lambda:str(uuid.uuid4()))
    slug = models.SlugField(editable=False, max_length=30)
    last_modified = models.DateTimeField(auto_now=True)
    data = models.TextField(blank=True)
    class Meta:
        verbose_name_plural = 'Pads'
        db_table = 'hwios_pads'
        app_label = 'no_fixture'
