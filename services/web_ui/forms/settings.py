# -*- coding: utf-8 -*-
"""
    services.web_ui.forms.settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form definitions for the settings module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from web_ui.models.settings import Settings

class GeneralSettingsForm(forms.ModelForm):

    class Meta:
        model = Settings
        
    def __init__(self, *args, **kwargs):
        super(GeneralSettingsForm, self).__init__(*args, **kwargs)  
        self.fields['site_name'].widget.attrs['class'] = 'textfield-medium'
        self.fields['mail_from'].widget.attrs['class'] = 'textfield-medium'
        self.fields['mail_header'].widget.attrs['class'] = 'textfield-large'
        self.fields['mail_body'].widget.attrs['class'] = 'textarea-large'       
