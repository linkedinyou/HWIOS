# -*- coding: utf-8 -*-
"""
    services.web_ui.forms.wiki
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form definitions for the wiki module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _
from web_ui.forms.widgets.slider import SliderInput

class EditArticleForm(forms.Form):
    submit_comments = forms.CharField(label=_('Comments'), min_length = 6, max_length = 64,widget=forms.TextInput(attrs={'class':'textfield-huge'})) 


class EditArticleHistoryForm(forms.Form):
    submit_comments = forms.CharField(label=_('Comments'), widget=forms.TextInput(attrs={'class':'textfield-huge','readonly':True})) 
    undo = forms.IntegerField(label=_('Revision History'), required = False, widget=SliderInput()) 
    
        
class FrontendSearchForm(forms.Form):
    text = forms.CharField(label=_("Enter search term"))
    search_content = forms.BooleanField(label=_("Search content"), required=False)