# -*- coding: utf-8 -*-
"""
    services.web_ui.models.plasmoids
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The plasmoid model and routing logics

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import uuid
from django.db import models
from django import forms
from django.forms import ModelForm
from datetime import datetime
import re


class PageAnchor(models.Model):
    """Page ORM-model description"""
    connection_name="default"
    uuid = models.CharField(max_length=36,  primary_key=True, default=lambda:str(uuid.uuid4()))
    slug = models.SlugField(editable=False, blank=True, max_length=30)
    target = models.CharField(max_length=128)
    access = models.IntegerField()
    cacheable = models.IntegerField(default=0)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Pages"
        db_table = 'hwios_page_anchors'


class PageEntity(models.Model):
    """Page entity ORM-model description"""
    connection_name="default"
    uuid = models.CharField(max_length=36,  primary_key=True, default=lambda:str(uuid.uuid4()))
    slug = models.SlugField(editable=False, blank=True, max_length=30)
    anchor = models.ForeignKey(PageAnchor)
    code = models.TextField()
    type = models.IntegerField()
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Entities"
        db_table = 'hwios_page_entities'
        
        
class PageRouter(object):
    """Plasmoid logics mainly for routing plasmoids to the proper view"""
    
    def __init__(self):
        self.get_routes()
    
    
    def route(self, view_history, profile):
        """Routes the client's current view through the plasmoids and
        return plasmoids that match the view for parsing to the client

        :param list view_history: The client's view history
        :param Profile profile: The profile object of the client
        :return: None or list of plasmoids
        """
        plasmoids = []
        for route in self.routes:
            match = False
            rp1 = route[0].match(view_history[-1])
            #match
            if rp1 != None:
                if len(view_history) >=2:
                    rp2 = route[0].match(view_history[-2])
                    if rp2 == None:
                        match = True
                else: match = True
            if match:
                if route[1].visible == 0:
                    plasmoids.append({
                        'uuid':route[1].uuid,
                        'slug':route[1].slug,
                        'script':route[1].script,
                    })
                elif route[1].visible == 1 and profile.is_authenticated:
                    plasmoids.append({
                        'uuid':route[1].uuid,
                        'slug':route[1].slug,
                        'script':route[1].script,
                    })
                elif route[1].visible == 2 and profile.is_staff:
                    plasmoids.append({
                        'uuid':route[1].uuid,
                        'slug':route[1].slug,
                        'script':route[1].script,
                    })
        if len(plasmoids) == 0:
            return None
        else:
            return plasmoids
            
            
    def get_routes(self):
        """(Re)Compiles routes from all plasmoids"""
        self.routes = []
        pages = PageAnchor.objects.all()
        for page in pages:
            self.routes.append([re.compile(page.target),page])