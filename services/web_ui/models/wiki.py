# -*- coding: utf-8 -*-
"""
    services.web_ui.models.wiki
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The models for the wiki module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django.db import models
from web_ui.models.profiles import Profile


class WikiArticle(models.Model):
    """Hyki page model"""
    connection_name="default"
    
    slug = models.SlugField(editable=False, max_length=30)
    created_on = models.DateTimeField(editable=False, auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = "Articles"
        app_label = 'no_fixture'
        db_table = 'hwios_hyki_articles'
        
        
class WikiRevision(models.Model):
    """Hyki page revision model"""
    article = models.ForeignKey(WikiArticle,)
    patch = models.TextField()
    submit_profile = models.ForeignKey(Profile, blank=True, null=True)
    submit_comments = models.TextField(blank=True)
    submit_date = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = 'Revisions'
        app_label = 'no_fixture'
        db_table = 'hwios_hyki_revisions'
        ordering = ['-submit_date']