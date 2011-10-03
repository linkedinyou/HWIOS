# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.blog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The websocket controller for the blog module
 
    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""


from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.core import serializers
from django.forms import model_to_dict
from django.utils.translation import ugettext as _
from django.db import models

from hwios.core.application import HWIOS

from web_ui.models.ws_auth import WSAuth
from web_ui.models.blog import BlogArticle, BlogArticleComment
from web_ui.forms.blog import BlogArticleForm, CreateArticleComment

from web_ui.models.signal import Signal
from web_ui.models.notifications import *
from web_ui.models.activity import *

class WS_Blog(object):
    """
    Websocket controller class for the blog module
    """

    def __init__(self, dispatcher):
        pass
        #dispatcher.signals.subscribe('ws_disconnect', self.leave_hyki_article)
        #dispatcher.signals.subscribe('view_changed', self.leave_hyki_article, filters = [(r'/hyki/(?P<slug>[^/]+)/',True),(r'/hyki/(?P<slug>[^/]+)/edit/',False)])


    def get_context(self, client):
        context = render_to_string("blog/context_menu.html", {'profile':client.profile})
        return {'data':{'dom':{'context':context}}}
    

    def view_blog(self, client):
        """Renders the blog articles view

        :param Client client: The requesting client
        :return: dict - html-layout data response
        """
        return self._get_blog(client)[0]

        
    def view_blog_article(self, client, slug):
        """Renders the blog article view

        :param Client client: The requesting client
        :param str slug: The article slug reference
        :return: dict - html-layout data response
        """
        return self._get_blog_article(client, slug)[0]
    

    @WSAuth.is_staff
    def create_blog_article(self, client, params = None):
        """Handles creation of a new blog article, and notification to other watching clients

        :param Client client: The requesting client
        :param dict params: Contains the form parameters
        :return: dict - Status and html-layout data response
        """
        if params == None:
            form = BlogArticleForm()
            main = render_to_string("blog/create_article.html", {'profile': client.profile,'form':form})
            return {'data':{'dom':{'main':main}}}
        else:
            form = BlogArticleForm(params)
            if form.is_valid():
                article = BlogArticle()
                article.title = form.cleaned_data['title']
                article.text = form.cleaned_data['text']
                article.author = client.profile
                article.save()
                client_response, tpl_params = self._get_blog(client)
                client_response.update({
                    'status':{
                        'code':'BLOG_ARTICLE_CREATED',
                        'i18n': '%s: %s' % (client.profile.username, _('Article created succesfully...')),
                        'type': HWIOS.ws_realm._t['notify-info'],
                    }
                })
                notify_others(client, client_response,'/blog/modified/', '^/blog/$', tpl_params)
                publish_activity(client.profile, _('Blog article created'),'/blog/%s/' % article.slug,[0,1,4,0,0])
                client_response['status']['state'] = '/blog/'
                return client_response
            else:
                main = render_to_string("blog/create_article.html", {'profile': client.profile,'form':form})
                client_response =  {
                    'status':{
                        'code':'FORM_INVALID',
                        'i18n':_('Invalid form!'),
                        'type': HWIOS.ws_realm._t['notify-info']
                    },
                    'data':{'dom':{'main':main}}
                }
                return client_response


    @WSAuth.is_staff
    def edit_blog_article(self, client, slug, params = None):
        """Shows edit-view when there are no parameters, otherwise try to save the related article

        :param Client client: The requesting client
        :param str slug: The article slug reference
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and html-layout data response
        """
        if params == None:            
            article = BlogArticle.objects.get(slug = slug)
            form = BlogArticleForm(initial={'title':article.title,'text':article.text})
            main = render_to_string("blog/edit_article.html", {"article":article,'profile': client.profile,'form':form})
            return {'data':{'dom':{'main':main}}}
        else:
            form = BlogArticleForm(params)
            if form.is_valid():
                article = BlogArticle.objects.get(slug = slug)
                article.title = form.cleaned_data['title']
                article.text = form.cleaned_data['text']
                article.author = client.profile
                article.save()
                client_response, tpl_params = self._get_blog(client)
                client_response.update({
                    'status': {
                        'code':'BLOG_ARTICLE_SAVED',
                        'i18n':'%s: %s' % (client.profile.username,_('Article updated succesfully...')),
                        'type': HWIOS.ws_realm._t['notify-info'],
                    }
                })
                #notify others viewing the main blog
                notify_others(client, client_response,'/blog/modified/', '^/blog/$', tpl_params)
                #notify othere viewing this article
                _response, _tpl_params = self._get_blog_article(client, slug)
                _response.update(client_response)
                notify_others(client, _response,'/blog/%s/modified/' % slug, '^/blog/%s/$' % slug, _tpl_params)
                client_response['status']['state'] = client.set_uri('/blog/')
                publish_activity(client.profile, _('Blog article edited'),'/blog/%s/' % slug,[0,0,4,0,0])
                return client_response
            else:                
                article = BlogArticle.objects.get(slug = slug)
                main = render_to_string("blog/edit_article.html", {"article":article,'profile': client.profile,'form':form})
                client_response =  {
                    'status':{
                        'code':'FORM_INVALID',
                        'i18n':_('Invalid form!'),
                        'type': HWIOS.ws_realm._t['notify-info']
                    },
                    'data':{'dom':{'main':main}}
                }
                return client_response


    @WSAuth.is_staff
    def delete_blog_article(self, client, slug, params = None):
        """Returns delete-confirmation layout when there are no parameters, otherwise try to delete the related article and
        render the general article view. 

        :param Client client: The requesting client
        :param str slug: The article slug reference
        :param dict params: Optional; contains the form parameters
        :return: dict - Status and html-layout data response
        """
        if params == None:
            try:
                article = BlogArticle.objects.filter(slug = slug)[0]
            except BlogArticle.DoesNotExist:
                return False
            dialog = render_to_string("blog/confirm_delete_article.html", {"article":article})
            response = {'data':{'dom':{'dialog':dialog}}}
            return response
        else:
            BlogArticle.objects.filter(slug = slug).delete()
            client_response, tpl_params = self._get_blog(client)
            client_response.update({
                'status': {
                    'code':'BLOG_ARTICLE_DELETED',
                    'i18n':'%s: %s' % (client.profile.username,_('Article %(slug)s removed succesfully...') % {'slug':str(slug)}),
                    'type': HWIOS.ws_realm._t['notify-info'],
                    'state': '/blog/'
                }
            })
            #notify others viewing the main blog
            notify_others(client, client_response,'/blog/modified/', '^/blog/$', tpl_params)
            #notify others viewing the same deleted blog article. Moves their url to new state
            notify_others(client, client_response,'/blog/modified/', '^/blog/%s/$' % slug, tpl_params, '/blog/')
            publish_activity(client.profile, _('Blog article deleted'),'/blog/',[0,3,4,0,0])
            return client_response


    @WSAuth.is_authenticated
    def create_article_comment(self, client, slug, params):
        """Takes care of all related actions that are involved in saving a new article

        Saves the ORM-entry, notifies other users of the event as well as generating an action-entry

        :param Client client: The requesting client
        :param str slug: The article slug reference
        :param dict params: Contains the form parameters
        :return: dict - Status and html-layout data response
        """
        form = CreateArticleComment(params)
        article = BlogArticle.objects.get(slug = slug)
        comments = article.blogarticlecomment_set.all()
        if form.is_valid():
            comment = BlogArticleComment()
            comment.text = form.cleaned_data['text']
            comment.article = article
            comment.author = client.profile
            comment.save()
            #prepare updated page for client and others
            client_response, tpl_params = self._get_blog_article(client, slug)
            client_response.update({
                'status':{
                    'code':'BLOG_COMMENT_SAVED',
                    'i18n':'%s: %s' % (client.profile.username, _('Comment saved succesfully...')),
                    'type': HWIOS.ws_realm._t['notify-info']
                }
            })
            #notify others viewing the same blog article
            notify_others(client, client_response, '/blog/%s/modified/', '^/blog/%s/$' % slug, tpl_params)
            #notify others viewing the main blog
            _response, _tpl_params = self._get_blog(client)
            _response.update({
                'status':{
                    'code':'BLOG_COMMENT_SAVED',
                    'i18n':'%s: %s' % (client.profile.username, _('Comment saved succesfully...')),
                    'type': HWIOS.ws_realm._t['notify-info'],
                }
            })
            notify_others(client, _response,'/blog/modified/', '^/blog/$', _tpl_params)
            publish_activity(client.profile, _('Blog comment created'),'/blog/%s/' % slug,[1,3,4,0,0])
            return client_response
        else:
            article = BlogArticle.objects.get(slug = slug)
            comments = article.blogarticlecomment_set.all()
            main = render_to_string("blog/read_article.html", {'article':article, 'comments':comments, 'profile': client.profile, 'form':form})
            response = {
                'status':{
                    'code':'FORM_INVALID',
                    'i18n':_('Invalid form!'),
                    'type': HWIOS.ws_realm._t['notify-info']
                },
                'data':{'dom':{'main':main}}
            }
            return response
            
            
    @WSAuth.is_staff
    def delete_article_comment(self, client, slug, uuid, params = None):
        """Takes care of all related actions that are involved in deleting an article

        Deletes the ORM-entry, notifies other users of the event as well as generating an action-entry

        :param Client client: The requesting client
        :param str slug: The article slug reference
        :param str uuid: The article comment uuid to delete
        :param dict params: Optional; acts like a switch to either return a confirmation view or hand it over to the actual deletion part
        :return: dict - Status and html-layout data response
        """
        if params == None:
            try:
                comment = BlogArticleComment.objects.get(pk = uuid)
            except BlogArticle.DoesNotExist:
                return False
            dialog = render_to_string("blog/confirm_delete_comment.html", {"comment":comment})
            return {'data':{'dom':{'dialog':dialog}}}
        else:
            BlogArticleComment.objects.get(pk = uuid).delete()
            client_response, tpl_params = self._get_blog_article(client, slug)
            client_response.update({
                'status': {
                    'code':'BLOG_COMMENT_DELETED',
                    'i18n':'%s: %s' % (client.profile.username, _('Comment removed succesfully...')),
                    'type': HWIOS.ws_realm._t['notify-info']
                }
            })
            #notify others viewing the same blog article
            notify_others(client, client_response, '/blog/%s/modified/', '^/blog/%s/$' % slug, tpl_params)
            #notify others viewing the main blog
            _response, _tpl_params = self._get_blog(client)
            _response.update(client_response)
            notify_others(client, _response,'/blog/modified/', '^/blog/$', _tpl_params)
            publish_activity(client.profile, _('Blog comment deleted'),'/blog/%s/' % slug,[1,3,4,0,0])
            return client_response


    def _get_blog(self, client):
        """
        Small helper function that returns template and html-layout references of all articles with their comments-count,
        that work well with the notify-others action
        """
        articles = BlogArticle.objects.extra(select={
            'comments': 'SELECT COUNT(*) FROM hwios_blog_comments WHERE hwios_blog_comments.article_id = hwios_blog_articles.uuid'
            },).all()
        tpl_params = {"articles":articles,'form':BlogArticleForm()}
        return [
            {'data':{'dom':{'main':render_to_string("blog/read_blog.html", dict(tpl_params.items() +dict({'profile':client.profile}).items()))}}},
            {'main':{'tpl':'blog/read_blog.html','params':tpl_params}}
        ]


    def _get_blog_article(self, client, slug):
        """
        Small helper function that returns template and html-layout references of an article with their comments,
        that work well with the notify-others action
        """
        article = BlogArticle.objects.get(slug = slug)
        comments = article.blogarticlecomment_set.all()
        form = CreateArticleComment()
        tpl_params= {'article':article,'comments': comments, 'form':form,'form': form}
        return [
            {'data':{'dom':{'main':render_to_string("blog/read_article.html", dict(tpl_params.items()+dict({'profile':client.profile}).items()))}}},
            {'main':{'tpl':'blog/read_article.html','params':tpl_params}}
        ]
        
    