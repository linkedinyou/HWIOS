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
from web_ui.models.pages import PageAnchor


class CreateAnchorForm(forms.Form):
    slug = forms.CharField(label=_('Title'), min_length = 2, max_length = 32,widget=forms.TextInput(attrs={'class':'textfield-small'}))
    access = forms.ChoiceField(label=_('Access Level'), choices=[(0,'All'),(1,'Users'),(2,'Moderators')])
    target = forms.CharField(label=_('URL Target'), min_length = 2, max_length = 128,widget=forms.TextInput(attrs={'class':'textfield-medium'}))
    cacheable = forms.BooleanField(required=False)

    
class EditAnchorForm(forms.Form):
    slug = forms.CharField(label=_('Title'), min_length = 2, max_length = 32,widget=forms.TextInput(attrs={'class':'textfield-small'}))
    access = forms.ChoiceField(label=_('Access Level'), choices=[(0,'All'),(1,'Users'),(2,'Moderators')])
    target = forms.CharField(label=_('URL Target'), min_length = 2, max_length = 128,widget=forms.TextInput(attrs={'class':'textfield-medium'}))
    cacheable = forms.BooleanField(required=False)
    auto_preview = forms.BooleanField(label=_('Auto Preview'),required = False)


class EntityForm(forms.Form):
    slug = forms.CharField(label=_('Title'), min_length = 2, max_length = 32,widget=forms.TextInput(attrs={'class':'textfield-small'}))
    anchor = forms.ModelChoiceField(queryset=PageAnchor.objects.all(), empty_label=_('Please Choose...'))
    type = forms.ChoiceField(label=_('Entity Type'), choices=[(0,'HTML'),(1,'CSS'),(2,'JS')])
    
class EditEntityForm(forms.Form):
    slug = forms.CharField(label=_('Title'), min_length = 2, max_length = 32,widget=forms.TextInput(attrs={'class':'textfield-small'}))
    anchor = forms.ModelChoiceField(queryset=PageAnchor.objects.all(), empty_label=_('Please Choose...'))
    type = forms.ChoiceField(label=_('Entity Type'), choices=[(0,'HTML'),(1,'CSS'),(2,'JS')])



    
    