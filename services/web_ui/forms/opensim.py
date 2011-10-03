# -*- coding: utf-8 -*-
"""
    services.web_ui.forms.opensim
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form definitions for the opensim module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import random
from django import forms
from django.utils.translation import ugettext_lazy as _
from core.application import HWIOS
from web_ui.models.settings import Settings
from web_ui.models.profiles import Profile
from web_ui.models.opensim import Regions


class RegionForm(forms.Form):
    name = forms.CharField(max_length=32, min_length=2, initial = lambda: "region%s" % random.randint(1, 99999),label=_('Name'),widget=forms.TextInput(attrs={'class':'textfield-small'}))
    owner = forms.ModelChoiceField(initial='admin', queryset = Profile.objects.all(),label=_('Owner'))
    service = forms.ChoiceField(label=_('Simulator'))
    sim_location_x = forms.IntegerField(label=_('X Location'), min_value = 0, max_value = 262144,widget=forms.TextInput(attrs={'class':'textfield-smallest'}), help_text=_('Click on the map'))
    sim_location_y = forms.IntegerField(label=_('Y Location'),min_value = 0, max_value = 262144,widget=forms.TextInput(attrs={'class':'textfield-smallest'}), help_text=_('Click on the map'))

    
    def __init__(self,*args,**kwargs):
        super(RegionForm,self).__init__(*args,**kwargs)
        self.fields['service'].choices = Regions().get_region_services(format='tuple')
        
        
class BackupRegionForm(forms.Form):
    name = forms.CharField(max_length=32, min_length=2, label=_('Name'), widget=forms.TextInput(attrs={'class':'textfield-medium'}))
    region_uuid = forms.CharField(widget=forms.HiddenInput)
    service_uuid = forms.CharField(widget=forms.HiddenInput)
    

class LoadSceneForm(forms.Form):
    region_uuid = forms.ChoiceField(label=_('Target region'))
    scene_name = forms.CharField(widget=forms.HiddenInput, max_length=32)
    
    def __init__(self,*args,**kwargs):
        choices = kwargs['choices']
        del kwargs['choices']
        super(LoadSceneForm,self).__init__(*args,**kwargs)
        self.fields['region_uuid'].choices = choices
        
        
class UploadSceneForm(forms.Form):
    scene = forms.FileField(label='')   
    
    
class UploadLuggageForm(forms.Form):
    luggage = forms.FileField(label='')


class LoadLuggageForm(forms.Form):
    simulator_uuid = forms.ChoiceField(label=_('Designated simulator'))
    luggage_name = forms.CharField(widget=forms.HiddenInput, max_length=64,label=_('Luggage name'))
    avatar = forms.ModelChoiceField(queryset=Profile.objects.all(),label=_('Target avatar'))
    password = forms.CharField(widget=forms.PasswordInput, max_length=32,label=_('Avatar password'))
    inventory_dir = forms.CharField(max_length=32,label=_('Inventory directory'),initial='/')
    
    def clean_password(self):
        password = self.cleaned_data['password']
        profile = self.cleaned_data['avatar']
        if not Profile.objects.check_os_password(password, profile.uuid):
            raise forms.ValidationError('Invalid password!')
        else:
            return password
            
    def __init__(self,*args,**kwargs):
        if 'choices' in kwargs:
            choices = kwargs['choices']
            del kwargs['choices']
            super(LoadLuggageForm,self).__init__(*args,**kwargs)
            self.fields['simulator_uuid'].choices = choices
        else:
            super(LoadLuggageForm,self).__init__(*args,**kwargs)
            
            
class BackupLuggageForm(forms.Form):
    simulator_uuid = forms.ChoiceField(label=_('Designated simulator'))
    luggage_name = forms.CharField(max_length=32, min_length=2, widget=forms.TextInput(attrs={'class':'textfield-large'}),label=_('Luggage name'))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'textfield-small'}), max_length=32,label=_('Avatar password'))
    inventory_dir = forms.CharField(max_length=32,label=_('Inventory directory'),initial='/', widget=forms.TextInput(attrs={'class':'textfield-large'}))

    def clean_password(self):
        password = self.cleaned_data['password']
        if not Profile.objects.check_os_password(password, self.profile.uuid):
            raise forms.ValidationError('Invalid password!')
        else:
            return password
            
    def __init__(self,*args,**kwargs):
        if 'profile' in kwargs:
            self.profile = kwargs['profile']
            del kwargs['profile']
        if 'choices' in kwargs:
            choices = kwargs['choices']         
            del kwargs['choices']
            super(BackupLuggageForm,self).__init__(*args,**kwargs)
            self.fields['simulator_uuid'].choices = choices
        else:
            super(BackupLuggageForm,self).__init__(*args,**kwargs)


class SimulatorSettingsForm(forms.Form):
    master_ini = forms.CharField(widget=forms.Textarea(attrs={'class':'textarea-large'}),label=_('master ini'))


class MapSettingsForm(forms.Form):
    osm = forms.BooleanField(required=False,label=_('OpenStreetMap'),help_text=_('Place regions on earth'))
    center_x = forms.IntegerField(required=False, min_value = 0,label=_('Center Position (X)'),help_text=_('Defines the x-position to focus the map on after opening'),widget=forms.TextInput(attrs={'class':'smallest-field'}))
    center_y = forms.IntegerField(required=False, min_value = 0,label=_('Center Position (Y)'),help_text=_('Defines the y-position to focus the map on after opening'),widget=forms.TextInput(attrs={'class':'smallest-field'}))
    center_z = forms.IntegerField(min_value =0, max_value=18,label=_('Center Position (Z)'),help_text=_('Defines the zoom-level that\'s being used by the map after opening'),widget=forms.TextInput(attrs={'class':'smallest-field'}))
