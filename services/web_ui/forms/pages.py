# -*- coding: utf-8 -*-
"""
    services.web_ui.forms.plasmoids
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form definitions for the plasmoids module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class EditPageForm(forms.Form):
    slug = forms.CharField(label=_('Title'), min_length = 2, max_length = 32,widget=forms.TextInput(attrs={'class':'textfield-small'}))
    visible = forms.ChoiceField(label=_('Access Level'), choices=[(0,'All'),(1,'Users'),(2,'Moderators')])
    target = forms.CharField(label=_('URL Target'), min_length = 2, max_length = 128,widget=forms.TextInput(attrs={'class':'textfield-medium'}))
    auto_preview = forms.BooleanField(label=_('Auto Preview'),required = False)

class EditScriptForm(forms.Form):
    slug = forms.CharField(label=_('Title'), min_length = 2, max_length = 32,widget=forms.TextInput(attrs={'class':'textfield-small'})) 
    visible = forms.ChoiceField(label=_('Access Level'), choices=[(0,'All'),(1,'Users'),(2,'Moderators')])
    target = forms.CharField(label=_('URL Target'), min_length = 2, max_length = 128,widget=forms.TextInput(attrs={'class':'textfield-medium'})) 
    auto_preview = forms.BooleanField(label=_('Auto Preview'),required = False)


    
    