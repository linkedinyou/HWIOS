# -*- coding: utf-8 -*-
"""
    services.web_ui.forms.blog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form definitions for the blogging module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _
from widgets.contenteditable import ContenteditableInput

class BlogArticleForm(forms.Form):
    text = forms.CharField(label='', widget=ContenteditableInput)
    title = forms.CharField(min_length=3, max_length=128, widget=forms.TextInput(attrs={'class':'textfield-huge'}))


class CreateArticleComment(forms.Form):
    text = forms.CharField(label='Comment', widget=forms.Textarea(attrs={'class':'blog-comment-editor'}), min_length=10)



