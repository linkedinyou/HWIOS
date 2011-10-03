# -*- coding: utf-8 -*-
"""
    services.web_ui.forms.widgets.slider
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form definitions for the jquery slider 

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django import forms

class SliderInput(forms.TextInput):
    """     
    A slider widget to include in your form
    """ 
            
    def render(self, name, value, attrs):
        attributes = attrs
        attributes['type'] = 'hidden'
        
        res = super(SliderInput, self).render(name, value, attrs = attributes)
        res += '<div class="slider-wrapper">'
        res += '<div id="%s_slider" class="slider"></div>' % name
        res += '<div id="%s_slider_value" class="slider-value"></div>' % (name)
        res += '</div>'
        return res      
