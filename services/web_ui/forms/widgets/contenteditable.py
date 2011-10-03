# -*- coding: utf-8 -*-
"""
    services.web_ui.forms.widgets.contenteditable
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Widget for the contenteditable element

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django import forms

class ContenteditableInput(forms.TextInput):
    """
    A contenteditable widget to include in your form
    """

    def render(self, name, value, attrs):
        attributes = attrs
        attributes['type'] = 'hidden'

        res = super(ContenteditableInput, self).render(name, value, attrs = attributes)
        res += '<div id="%s" class="contenteditable"></div>' % name
        return res    