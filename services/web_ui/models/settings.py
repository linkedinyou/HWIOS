# -*- coding: utf-8 -*-
"""
    services.web_ui.models.settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The model description for the settings modules

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

ACTIVATION_TYPES = (
    (0, 'Instant'),
    (1, 'Mail user'),
    (2, 'Mail moderator'),
)

class Settings(models.Model):
    site_name = models.CharField(max_length=64, verbose_name=_("Site Name"))
    activation_type = models.SmallIntegerField(choices=ACTIVATION_TYPES, verbose_name=_("Activation Type"))
    registration_moderator_notify = models.BooleanField(verbose_name=_("Moderator Notify"))
    mail_from = models.CharField(max_length=64, verbose_name=_("Mail From"))
    mail_header = models.CharField(max_length=64, verbose_name=_("Mail Header"))
    mail_body = models.TextField(verbose_name=_("Mail Body"))
    class Meta:
        db_table = 'hwios_settings'
        app_label = 'models'
    def __unicode__(self):
        return 'settings'
        