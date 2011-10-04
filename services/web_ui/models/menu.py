# -*- coding: utf-8 -*-
"""
    services.web_ui.models.menu
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The menu model and logics to render a recursive menu

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
from django.db import models
from django.utils.translation import ugettext as _
import re

class MenuTree(models.Model):

    parent_id = models.IntegerField(max_length=30)  
    auth_level = models.IntegerField()  
    icon_class = models.CharField(max_length=60)    
    title = models.CharField(max_length=30)    
    view = models.CharField(max_length=60, blank=True)
    order = models.IntegerField()  
    class Meta:
        verbose_name_plural = "Menus"
        db_table = 'hwios_menu'
        ordering = ['title']
        
        
class Menu(object):
    
    
    def __init__(self, user):
        self.user = user
        self.nodes = {}
        self.menu_structure = ''
        self.menu_regex = re.compile(r'\{(\w+)\}')
        
    
    def recursive_render(self, nodes, parent = 0):
        if parent not in nodes:
            return
        #submenu
        if parent != 0:
            self.menu_structure +='<ul class="menu-list">'
        for index, node in enumerate(nodes[parent]):
            if self.has_children(node):
                if parent == 0:
                    if '/' in node.view:
                        self.menu_structure +='<li><div class="menu-item" data-uri="%s">%s</div>' % (node.view, _(node.title))
                    else:
                        self.menu_structure +='<li><div class="menu-item" data-function="%s">%s</div>' % (node.view, _(node.title))
                else:
                    if '/' in node.view:
                        self.menu_structure +='<li><span class="ui-icon %s menu-icon ui-icon-empty"></span><div class="menu-item" data-uri="%s">%s</div><span class="sf-sub-indicator"></span>' % (node.icon_class, node.view, _(node.title))
                    else:
                        self.menu_structure +='<li><span class="ui-icon menu-icon ui-icon-empty"></span><div class="menu-item" data-function="%s">%s</div><span class="sf-sub-indicator"></span>' % (node.view, _(node.title))
                self.recursive_render(nodes, node.pk)
            else:
                if self.authenticate_node(node):
                    #Detect URL
                    self.menu_structure +='<li>'
                    if len(node.icon_class) > 0:
                        self.menu_structure +='<span class="ui-icon %s menu-icon"></span>' % node.icon_class
                    if '/' in node.view:
                        #simple placeholder function for user attributes
                        iterator = self.menu_regex.finditer(node.view)  
                        node.view = str(node.view)
                        for match in iterator:
                            replace_attr = str(match.group()[1:-1])
                            node.view = node.view.replace(match.group(), getattr(self.user, replace_attr))
                        print _(node.title)
                        self.menu_structure +='<div class="menu-item" data-uri="%s">%s</div></li>' % (node.view, _(node.title))
                    else:                        
                        self.menu_structure +='<div class="menu-item" data-function="%s">%s</div></li>' % (node.view, _(node.title))
                        print _(node.title)
        if parent != 0:
            self.menu_structure +='</ul></li>'   
        
    
    def has_children(self, node):
        if node.pk in self.nodes and len(self.nodes[node.pk]) > 0:
            #detect whether there are valid child nodes
            for node in self.nodes[node.pk]:
                result = self.authenticate_node(node)
                if result:
                    return True     
            return False
        else:
            return False


    def authenticate_node(self, node):
        if node.auth_level == 0:
            return True
        if node.auth_level == 1 and not self.user.is_authenticated():
            return True
        if node.auth_level == 2 and self.user.is_authenticated():
            return True
        if node.auth_level == 3 and self.user.is_staff:
            return True        
        return False
        

    def render(self):
        self.menu_structure = ''
        menu_items = MenuTree.objects.all()        
        for menu_item in menu_items:
            if menu_item.parent_id not in self.nodes:
                self.nodes[menu_item.parent_id] = []
            self.nodes[menu_item.parent_id].append(menu_item)        
        self.menu_structure ='<div id="main-menu"><ul class="sf-menu">'
        self.recursive_render(self.nodes)
        self.menu_structure +='</ul></div>'
        return self.menu_structure
        
