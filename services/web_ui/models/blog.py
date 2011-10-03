# -*- coding: utf-8 -*-
"""
    services.web_ui.models.blog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The model description for the blogging module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import uuid

from django.db.models import CharField, DateTimeField, ForeignKey, Model, TextField
from web_ui.models.profiles import Profile
from autoslug import AutoSlugField


class BlogArticle(Model):
    """Model for the blog articles"""
    connection_name="default"
    
    uuid = CharField(max_length=36,  primary_key=True, default=lambda:str(uuid.uuid4()))
    title = CharField(max_length=36)
    pub_date = DateTimeField(auto_now_add=True)
    author = ForeignKey(Profile, blank=True, null=True)
    slug = AutoSlugField(populate_from=lambda instance: instance.title,
                        unique_with=['author__username', 'pub_date__month'],
                        slugify=lambda value: value.replace(' ','-'))
    text = TextField()
    
    
    class Meta:
        verbose_name_plural = "Articles"
        app_label = 'no_fixture'
        db_table = 'hwios_blog_articles'
        ordering = ['-pub_date']


class BlogArticleComment(Model):
    """Model for the blog article comments, linked to both author and article"""
    connection_name="default"

    uuid = CharField(max_length=36,  primary_key=True, default=lambda:str(uuid.uuid4()))
    pub_date = DateTimeField(auto_now_add=True)
    author = ForeignKey(Profile, blank=True, null=True)
    article = ForeignKey(BlogArticle, blank=True, null=True)
    text = TextField()


    class Meta:
        verbose_name_plural = "Comments"
        app_label = 'no_fixture'
        db_table = 'hwios_blog_comments'
        ordering = ['-pub_date']

