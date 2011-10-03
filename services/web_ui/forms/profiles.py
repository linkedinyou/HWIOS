# -*- coding: utf-8 -*-
"""
    services.web_ui.forms.profiles
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form definitions for the profiles module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""


import uuid
import hashlib

from django.db import models
from django import forms
from web_ui.models.profiles import Profile
from django.utils.translation import ugettext_lazy as _


class NewProfileForm(forms.Form):
    first_name = forms.CharField(min_length = 2, max_length=16,label=_('First name'))
    last_name = forms.CharField(min_length = 2, max_length=16,label=_('Last name'))
    email = forms.EmailField(label=_('Email'))
    organisation = forms.CharField(min_length = 2, max_length=36,label=_('Organisation'))
    password = forms.CharField(min_length = 4, max_length=16, widget=forms.PasswordInput(render_value=False),label=_('Password')) 
    is_active = forms.BooleanField(required=False, initial=1,label=_('Is active'))
    is_staff = forms.BooleanField(required=False, label=_('Is staff'))
    is_superuser = forms.BooleanField(required=False,label =_('Is superuser'))
    def clean(self):
        cleaned_data = self.cleaned_data
        if 'first_name' and 'last_name' in cleaned_data:
            first_name = cleaned_data['first_name'].lower().replace(' ', '_')
            last_name = cleaned_data['last_name'].lower().replace(' ', '_')
            try:
                Profile.objects.get(first_name=first_name,last_name=last_name)
            except Profile.DoesNotExist:
                return cleaned_data
            self._errors["first_name"] = self.error_class(['The profile name "%s %s" is not available anymore.' % (first_name,last_name)])
            self._errors["last_name"] = self.error_class(['The profile name "%s %s" is not available anymore.' % (first_name,last_name)])
            del cleaned_data
        return None

    def clean_email(self):
        n = self.cleaned_data['email']
        try:
            Profile.objects.get(email=n)
        except Profile.DoesNotExist:
            return n
        raise forms.ValidationError('The emailaddress "%s" is already taken.' % n)
    
    
class EditProfileForm(forms.Form):
    first_name = forms.CharField(max_length=32,label=_('First name'))
    last_name = forms.CharField(max_length=32, label=_('Last name'))
    email = forms.EmailField(label=_('Email'))
    password = forms.CharField(widget=forms.PasswordInput,required=False, label=_('Password'))
    is_active = forms.BooleanField(required=False, initial=1,label=_('Is active'))
    is_staff = forms.BooleanField(required=False,label=_('Is staff'))
    is_superuser = forms.BooleanField(required=False,label=_('Is superuser'))
    
    
class EditMyProfileForm(forms.Form):
    email = forms.EmailField(label=_('Email'))
    password = forms.CharField(widget=forms.PasswordInput,required=False, label=_('Change Password'))
    about = forms.CharField(label=_('About me'), widget=forms.Textarea)


class RegisterProfileForm(forms.Form):        
    username = forms.CharField(min_length = 2, max_length=36,label=_('Username'))
    email = forms.EmailField(label=_('Email'))
    password = forms.CharField(min_length = 4, max_length=16, widget=forms.PasswordInput(render_value=False),label=_('Password')) 

    def clean(self):
        cleaned_data = self.cleaned_data
        if 'first_name' and 'last_name' in cleaned_data:
            first_name = self.cleaned_data['first_name'].lower().replace(' ', '_')
            last_name = self.cleaned_data['last_name'].lower().replace(' ', '_')
            try:
                Profile.objects.get(first_name=first_name,last_name=last_name)
            except Profile.DoesNotExist:
                return cleaned_data
            self._errors["first_name"] = self.error_class(['The profile name "%s %s" is not available anymore.' % (first_name,last_name)])
            self._errors["last_name"] = self.error_class(['The profile name "%s %s" is not available anymore.' % (first_name,last_name)])
            del cleaned_data["first_name"]
            del cleaned_data["last_name"]
        return cleaned_data

    def clean_email(self):
        n = self.cleaned_data['email']
        try:
            Profile.objects.get(email=n)
        except Profile.DoesNotExist:
            return n
        raise forms.ValidationError('The emailaddress "%s" is already taken.' % n)
        

class LoginForm(forms.Form):
    username = forms.CharField(min_length = 2, max_length=36,label=_('Username'))
    password = forms.CharField(min_length = 4, max_length=16, widget=forms.PasswordInput(render_value=False), label=_('Password')) 
    
    
class ActivateForm(forms.Form):
    password = forms.CharField(min_length = 4, max_length=16, widget=forms.PasswordInput(render_value=False), label=_('Password')) 
