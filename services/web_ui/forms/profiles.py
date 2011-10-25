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
    username = forms.CharField(label=_('Username'), max_length=32)
    first_name = forms.CharField(label=_('First name'), min_length = 2, max_length=16,required=False)
    last_name = forms.CharField(label=_('Last name'),min_length = 2, max_length=16,required=False)
    email = forms.EmailField(label=_('Email'))
    organisation = forms.CharField(min_length = 2, max_length=36,label=_('Organisation'), required=False)
    password = forms.CharField(label=_('Password'), min_length = 4, max_length=16, widget=forms.PasswordInput(render_value=False)) 
    is_active = forms.BooleanField(label=_('Is active'), required=False, initial=1)
    is_staff = forms.BooleanField(label=_('Is staff'), required=False)
    is_superuser = forms.BooleanField(label =_('Is superuser'), required=False)
    def clean(self):
        cleaned_data = self.cleaned_data
        if 'username' in cleaned_data:
            username = cleaned_data['username'].lower().replace(' ', '_')
            try:
                Profile.objects.get(username=username)
            except Profile.DoesNotExist:
                return cleaned_data
            self._errors["username"] = self.error_class(['The profile username "%s" is not available anymore.' % username])
            del cleaned_data
        return None

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            Profile.objects.get(email=email)
        except Profile.DoesNotExist:
            return email
        raise forms.ValidationError('The emailaddress "%s" is already taken.' % email)
    
    
class EditProfileForm(forms.Form):
    username = forms.CharField(label=_('Username'), max_length=32)
    first_name = forms.CharField(label=_('First name'), max_length=32, required=False)
    last_name = forms.CharField(label=_('Last name'), max_length=32, required=False)
    email = forms.EmailField(label=_('Email'))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput,required=False)
    is_active = forms.BooleanField(label=_('Is active'), required=False, initial=1)
    is_staff = forms.BooleanField(label=_('Is staff'), required=False)
    is_superuser = forms.BooleanField(label=_('Is superuser'), required=False)
    
    
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
        if 'username' in cleaned_data:
            username = self.cleaned_data['username'].lower().replace(' ', '_')
            try:
                Profile.objects.get(username=username)
            except Profile.DoesNotExist:
                return cleaned_data
            self._errors["username"] = self.error_class(['The profile name "%s " is not available anymore.' % username])            
            del cleaned_data["username"]
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            Profile.objects.get(email=email)
        except Profile.DoesNotExist:
            return email
        raise forms.ValidationError('The emailaddress "%s" is already taken.' % email)
        

class LoginForm(forms.Form):
    username = forms.CharField(min_length = 2, max_length=36,label=_('Username'))
    password = forms.CharField(min_length = 4, max_length=16, widget=forms.PasswordInput(render_value=False), label=_('Password')) 
    
    
class ActivateForm(forms.Form):
    password = forms.CharField(min_length = 4, max_length=16, widget=forms.PasswordInput(render_value=False), label=_('Password')) 
