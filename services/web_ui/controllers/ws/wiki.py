# -*- coding: utf-8 -*-
"""
    services.web_ui.controllers.ws.wiki
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The websocket controller for the wiki module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from core.application import HWIOS
from lib.diff_match_patch import diff_match_patch

from web_ui.models.ws_auth import WSAuth
from web_ui.models.wiki import WikiArticle, WikiRevision
from web_ui.forms.wiki import EditArticleForm, EditArticleHistoryForm
from web_ui.models.infinote import InfinotePool
from web_ui.models.activity import *

from web_ui.models.signal import Signal
from markdown.inlinepatterns import LINK_RE


class WS_Wiki(object):
    """
    Websocket handler for the wiki module. Mainly involves infinote operations.
    """     
    
    def __init__(self, dispatcher):
        self.infinote_pool = InfinotePool(self)
        self.diff_mp = diff_match_patch()
        self._update_wiki_graph()
        dispatcher.signals.subscribe('ws_disconnect', self.leave_wiki_article)
        dispatcher.signals.subscribe('view_changed', self.leave_wiki_article, filters = [(r'/wiki/(?P<slug>[^/]+)/',True),(r'/wiki/(?P<slug>[^/]+)/edit/$',False)])
        

    def get_context(self, client):
        context = render_to_string("wiki/context_menu.html", {'profile':client.profile})
        return {'data':{'dom':{'context':context}}}


    def view_wiki_article(self, client, slug):
        """Infinote client wants to join the subscription log based on the content-id(cid). In this case within the wiki, the
        client requests the cid from the page-slug, subscribes to the channel and starts sending operation requests out, 
        with the cid included. When the client disconnects(other page view or websocket closes), the client gets 
        unsubscribed from the log.

        :param Client client: The requesting client
        :param str slug: The wiki slug reference
        :return: dict - wiki article state information or html-layout data response
        """
        try:
            article = WikiArticle.objects.get(slug=slug)
            article_text = self._get_revision_text(article)
            revisions = len(WikiRevision.objects.filter(article = article))
            client.role = 'view'
            subscriber = self.infinote_pool.subscribe(client, slug, article_text, 'wiki', self._signal_presence, 'view')
            main = render_to_string("wiki/read_article.html", {"profile":client.profile,'article':article})
            return {
                'data':{
                    'dom':{'main':main},
                    'article':{
                        'title':article.slug,
                        'state':subscriber['state'],
                        'log':subscriber['log'],
                        'revisions':revisions
                    }, 
                    'online':subscriber['online'],
                    'uid':client.profile.pk
                }
            }
        except ObjectDoesNotExist:
            main = render_to_string("wiki/create_article.html", {"profile":client.profile,"article":{'slug':slug}})
            return {'data':{'dom':{'main':main},'article':{'title':slug, 'state':False}}}
            

    @WSAuth.is_authenticated
    def edit_wiki_article(self, client, slug):
        """Joins an infinote subscription pool and returns document state information to sync client-side infinote editor with,
        or return a new-article template view
        
        :param Client client: The requesting client
        :param str slug: The wiki slug reference
        :return: dict - wiki article state information or html-layout data response
        """
        try:
            article = WikiArticle.objects.get(slug=slug)
            article_text = self._get_revision_text(article)
            revisions = len(WikiRevision.objects.filter(article = article))
            client.role = 'edit'
            subscriber = self.infinote_pool.subscribe(client, slug, article_text, 'wiki', self._signal_presence,'edit')
            form = EditArticleForm(initial={'id':article.pk, 'slug':slug})
            main = render_to_string('wiki/edit_article.html',  {'form': form,"article":article})
            if len(client.transport.view_history) > 1:
                if '/wiki/%s/edit/' % slug not in client.transport.view_history[-2]:
                    publish_activity(client.profile, _('Wiki article editing'),'/wiki/%s/edit/' % slug,[0,2,2,0,0])
            else:
                publish_activity(client.profile, _('Wiki article editing'),'/wiki/%s/edit/' % slug,[0,2,2,0,0])
            return {
                'data':{
                    'dom':{'main':main},
                    'article':{
                        'title':article.slug,
                        'state':subscriber['state'],
                        'log':subscriber['log'],
                        'revisions':revisions
                    }, 
                    'online':subscriber['online'],
                    'uid':client.profile.pk,
                }
            }
        except ObjectDoesNotExist:
            main = render_to_string("wiki/create_article.html", {"profile":client.profile,"article":{'slug':slug}})
            return {'data':{'dom':{'main':main},'article':{'title':slug, 'state':False}}}


    def _signal_presence(self, client, online, app_pool, item_id):
        """Callback function when someone subscribes or unsubscribes to the infinote pool"""
        client.remote('/data/%s/%s/online/update/' % (app_pool, item_id),{'online':online})


    def _signal_operation(self, client, app_pool, item_id, operation_type, params):
        """Client callback function for an infinote operation"""
        client.remote('/data/%s/%s/%s/' % (app_pool, item_id, operation_type), params)


    def _signal_caret(self, client, app_pool, item_id, params):
        """Client callback function for a caret operation"""
        client.remote('/data/%s/%s/caret/' % (app_pool, item_id), {'id': params['id'],'cursor':params['cursor']})
        

    def leave_wiki_article(self, client):
        """Remove client page subscription after client left the wiki page or disconnected. This is tracked
        by signal observers defined in the controller constructor.
        
        :param Client client: The requesting client
        """
        self.infinote_pool.unsubscribe(client, 'wiki', self._signal_presence)
                

    @WSAuth.is_authenticated
    def request_wiki_insert(self, client, slug, params):
        """Infinote client insert operation request on the subscription log
        
        :param Client client: The requesting client
        :param str slug: The wiki slug reference
        :param dict params: Contains the operation parameters
        :return: dict - status data response
        """
        self.infinote_pool.request_insert(client,'wiki', slug, params, self._signal_operation)
        return {'status':{'code':'OP_OK'}}
            

    @WSAuth.is_authenticated
    def request_wiki_remove(self, client, slug, params):
        """Infinote client delete operation request on the subscription log

        :param Client client: The requesting client
        :param str slug: The wiki slug reference
        :param dict params: Contains the operation parameters
        :return: dict - status data response
        """
        self.infinote_pool.request_delete(client,'wiki', slug, params, self._signal_operation)
        return {'status':{'code':'OP_OK'}}
        
                
    @WSAuth.is_authenticated       
    def request_wiki_undo(self, client, slug, params):
        """Infinote client undo operation request on the subscription log

        :param Client client: The requesting client
        :param str slug: The wiki slug reference
        :param dict params: Contains the operation parameters
        :return: dict - status data response
        """
        self.infinote_pool.request_undo(client,'wiki', slug, params, self._signal_operation)
        return {'status':{'code':'OP_OK'}}
        
           
    def update_remote_caret(self, client, slug, params):
        """Infinote client caret move broadcast

        :param Client client: The requesting client
        :param str slug: The wiki slug reference
        :param dict params: Contains the operation parameters
        """
        self.infinote_pool.update_caret(client,'wiki', slug, params, self._signal_caret)
        
                
    @WSAuth.is_authenticated
    def edit_history(self, client, slug):
        """Render the wiki page history view and return an overview of all page revisions for time-warp slider

        :param Client client: The requesting client
        :param str slug: The wiki slug reference
        :return: dict - Revision data and html-layout data response
        """
        article = WikiArticle.objects.get(slug = slug)
        revisions = WikiRevision.objects.filter(article = article)
        rev_data = []
        for revision in revisions:
            rev_data.append({'submit_comments':revision.submit_comments,'submit_date':str(revision.submit_date),'patch':revision.patch,
            'submit_profile':'%s %s' % (revision.submit_profile.first_name,revision.submit_profile.last_name)})
        rev_data.reverse()
        form = EditArticleHistoryForm(initial={'undo':len(revisions)})
        main = render_to_string("wiki/edit_history.html", {'article':article,'form':form})
        return {
            'data':{
                'dom':{'main':main}
            },
            'article':{
                'slug':article.slug,
                'revisions':rev_data
            }
        } 
        

    @WSAuth.is_authenticated
    def save_page(self, client, slug, params):
        """Saves an infinote document's state to the database and notifies participants of the action

        :param Client client: The requesting client
        :param str slug: The wiki slug reference
        :return: dict - Revision data and html-layout data response
        """
        _content = params['content']
        del params['content']
        form = EditArticleForm(params)
        
        if form.is_valid():
            
            try:
                article = WikiArticle.objects.get(slug = slug)
            except WikiArticle.DoesNotExist:
                article = WikiArticle()
                article.slug = slug
                article.save()                
                self._update_wiki_graph()
                publish_activity(client.profile, _('Wiki article created'),'/wiki/%s/' % slug,[0,1,1,0,0])
                for _client in HWIOS.ws_realm.pool.get_clients():
                    #this client is watching our attempt to create a new article. Send it a request to resubscribe to the article                    
                    if client != _client and '/wiki/' in _client.transport.view_history[-1]:
                        _client.remote('/wiki/%s/' % slug,{
                            'status':{
                                'code':'WIKI_PAGE_CREATED',
                                'i18n':_('%(first_name)s %(last_name)s just created article %(slug)s!') % {'first_name':client.profile.first_name,'last_name': client.profile.last_name,'slug':slug},
                                'type': HWIOS.ws_realm._t['notify-info']
                            }
                        })
                return self.edit_wiki_article(client,slug)
            article.last_modified = datetime.now()            
            #construct a revision
            previous_text = self._get_revision_text(article)
            patch = self.diff_mp.patch_make(previous_text, _content)
            #if the patch applied, save a revision
            if len(patch) > 0:
                revision = WikiRevision()
                revision.article = article
                revision.patch = self.diff_mp.patch_toText(patch)
                revision.submit_profile = client.profile
                revision.submit_comments = form.cleaned_data["submit_comments"]
                revision.save()
                revisions = WikiRevision.objects.filter(article = article)
                #evaluate queryset
                revision_count = len(revisions)
                last_revision = revisions[0]
                '''send our latest rev with the notification to other users, just in case we have someone fooling around in history'''
                rev_data = {'submit_comments':last_revision.submit_comments,'submit_date':str(last_revision.submit_date),'patch':last_revision.patch,
                'submit_profile':'%s %s' % (last_revision.submit_profile.first_name,last_revision.submit_profile.last_name)}
                article.content = _content                
                article.save()
                publish_activity(client.profile, _('Wiki article saved'),'/wiki/%s/' % slug,[0,1,1,0,0])
                response = {
                    'status':{
                        'code':'WIKI_EDIT_OK',
                        'i18n':_('Wiki article %(slug)s stored...') % {'slug':slug},
                        'type': HWIOS.ws_realm._t['notify-info'],
                        'state': '/wiki/%s/' % slug,
                    }
                }
                self._update_wiki_graph()
                main = render_to_string('wiki/read_article.html',{"profile":client.profile, "page":article})
                response.update({'data':{'dom':{'main':main},'page':{'title':article.slug, 'slug':slug}}})
            else:
                response = {
                    'status':{
                        'code':'WIKI_EDIT_NO_CHANGE',
                        'i18n':_('No changes found in wiki article. Page was not stored...'),
                        'type': HWIOS.ws_realm._t['notify-warning'],
                        'state': '/wiki/%s/' % slug,
                    }
                }
                main = render_to_string('wiki/read_article.html',{"profile":client.profile, "page":article})
                response.update({'data':{'dom':{'main':main},'page':{'title':article.slug, 'slug':slug}}})
                return response
            #Inform all users that are editing this article. Update history views with the latest revision
            for target_client in HWIOS.ws_realm.pool.subscription['wiki'][slug]['clients']:
                if client != target_client and target_client.role == 'edit':
                    target_client.remote("/data/wiki/%s/saved/" % slug,{
                        'status':{
                            'code':'WIKI_PAGE_SAVED',
                            'type': HWIOS.ws_realm._t['notify-info'],
                            'i18n':_('Wiki article was stored by %(first_name)s %(last_name)s as revision %(revision)s: %(comments)s') % {'first_name':client.profile.first_name, 'last_name':client.profile.last_name,'revision':revision_count,'comments':last_revision.submit_comments}
                        },
                        'data':{'revision':rev_data}
                    })  
            return response
        else:
            try:
                article = WikiArticle.objects.get(slug=slug)
                main = render_to_string('wiki/edit_article.html',  {'form': form,"page":article})
            except WikiArticle.DoesNotExist:
                main = render_to_string("wiki/create_article.html", {"slug":slug,"form":form})
            response = {
                'status':{
                    'code':'FORM_INVALID',
                    'i18n':_('Invalid Form!'),
                    'type': HWIOS.ws_realm._t['notify-warning']
                },
                'data':{'dom':{'main':main}}
            }
            return response  
        
     
    @WSAuth.is_authenticated
    def delete_page(self, client, slug, params = None):
        """Deletes an infinote document from the infinote pool and database, and notifies participants of the action

        :param Client client: The requesting client
        :param str slug: The wiki slug reference
        :return: dict - Status and html-layout data response
        """
        if params == None:
            try:
                article = WikiArticle.objects.get(slug=slug)
            except WikiArticle.DoesNotExist:
                return False
            dialog = render_to_string("wiki/delete_article_confirm.html", {"page":article})
            return {
                'data':{
                    'dom':{'dialog':dialog}
                }
            }
        try:
            article = WikiArticle.objects.get(slug=slug)
        except WikiArticle.DoesNotExist:
            return {
                'status':{
                    'code':'WIKI_INVALID_PAGE',
                    'i18n':_('Invalid article'),
                    'type': HWIOS.ws_realm._t['notify-error']
                }
            }
        main = render_to_string("wiki/create_article.html", {"profile":client.profile,"page":{'slug':slug}})
        for _client in HWIOS.ws_realm.pool.get_clients():
            if client != _client and '/wiki/' in _client.transport.view_history[-1]:
                _client.remote('/data/wiki/%s/deleted/' % slug,{
                    'status':{
                        'code':'WIKI_PAGE_DELETED',
                        'i18n':_('%(first_name)s %(last_name)s removed the current article...') % {'first_name':client.profile.first_name,'last_name':client.profile.last_name},
                        'type': HWIOS.ws_realm._t['notify-info']
                    },
                    'data':{
                        'dom':{'main':main},
                        'page':{'title':slug, 'content':False,'slug':slug}
                    }
                })              
        del HWIOS.ws_realm.pool.subscription['wiki'][slug]
        article.delete()
        publish_activity(client.profile, _('Wiki article deleted'),'/wiki/%s/' % slug,[0,1,4,0,0])
        self._update_wiki_graph()
        return {
            'status':{
                'code':'WIKI_DELETE_OK',
                'i18n':_('Wiki article deleted successfully...'),
                'type': HWIOS.ws_realm._t['notify-info']
            },
            'data':{
                'dom':{'main':main}
            }
        }        
        
        
    @WSAuth.is_authenticated
    def notify_editors(self, client, slug, revision):
        """After a client replaced the document state with a revision, it sends a request to notify participants

        :param Client client: The requesting client
        :param str slug: The wiki slug reference
        :param int revision: The revision that has been restored        
        :return: dict - Empty response to trigger re-init editor on the client-side
        """
        article = WikiArticle.objects.get(slug=slug)
        _rev = WikiRevision.objects.filter(article = article)
        _revision = _rev[len(_rev) - revision]
        for _client in HWIOS.ws_realm.pool.subscription['wiki'][slug]['clients']:
            if _client.profile.uuid != client.profile.uuid:
                _client.remote('/data/wiki/'+slug+'/edit/notify/',{
                    'status':{
                        'code':'WIKI_HISTORY_RESTORE_OK',
                        'i18n':_('Client %(first_name)s %(last_name)s restored article text to revision %(revision)s: \'%(comments)s\'') % {'first_name':client.profile.first_name, 'last_name':client.profile.last_name, 'revision':revision, 'comments':_revision.submit_comments},
                        'type': HWIOS.ws_realm._t['notify-info']
                        }})        
        publish_activity(client.profile, _('Wiki revision restored'),'/wiki/%s/' % slug,[0,1,3,0,0])
        return {}
        
            
    def _get_revision_text(self, article, revision = None):
        """Retrieve the page's current persistent revision text from the stored patches"""
        revisions = WikiRevision.objects.filter(article = article)
        patches = []
        for revision in revisions:
            patches.append(self.diff_mp.patch_fromText(revision.patch))
        patches.reverse()
        text = ''
        for patch in patches:            
            text = self.diff_mp.patch_apply(patch, text)[0]
        return text          
        
                        
    def _get_editing_clients(self, slug):
        """Get a list of editing clients, suitable for display"""
        editing_clients = []
        for _client in HWIOS.ws_realm.pool.subscription['wiki'][slug]['clients']:
            if _client.role == 'edit':  
                 editing_clients.append('%s %s' % (_client.profile.first_name, _client.profile.last_name))
        return editing_clients
        
        
    def plasmoid_get_wiki_tree(self, client):
        """Get a graph representation of the wiki structure,
        with links as edges and articles as nodes

        :param Client client: The requesting client
        :return: dict - TheJIT-compatible graph structure
        """
        response = {'data':{'tree':self.graph_info}}
        return response         
        
    
    def _update_wiki_graph(self):
        """write a python-graph of wiki articles(nodes) and their links(edges) to other articles"""
        import re
        from pygraph.classes.graph import graph
        pattern = re.compile(LINK_RE)
        articles = WikiArticle.objects.all()
        gr = graph()
        if len(articles) > 0:
            for article in articles:
                if article.id not in gr.nodes():
                    self._create_node(gr, article)
                article_text = self._get_revision_text(article)
                results = pattern.findall(article_text)
                for link in results:
                    _source = link[7].split('/')[1]
                    _link = link[7].split('/')[2]
                    if _source == 'wiki':
                        #adjacency article links
                        for _article in articles:
                            #match link with article
                            if _article.slug == _link:
                                #doesnt point to itself
                                if _article != article:
                                    #target node doesn't exist yet
                                    if _article.id not in gr.nodes():
                                        self._create_node(gr, _article)
                                        gr.add_edge((article.id, _article.id))
                                    else:
                                        if not gr.has_edge((_article.id,article.id)):
                                            gr.add_edge((article.id, _article.id))
            self.graph_info = self._format_graph_to_thejit_tree(gr)
        else:
            self.graph_info = False


    def _create_node(self, graph, article):
        """Create pygraph node"""
        graph.add_node(article.id)
        graph.add_node_attribute(article.id,{
            'name':article.slug,
            'data':{}
        })


    def _format_graph_to_thejit_graph(self,graph):
        """Convert pygraph graph to theJIT compatible graph"""
        thejit_graph = []
        for node in graph.nodes():
            jit_node = graph.node_attr[node][0]
            jit_node['id'] = node
            jit_node['adjacencies'] = graph.node_neighbors[node]
            thejit_graph.append(jit_node)
        return thejit_graph


    def _format_graph_to_thejit_tree(self, graph):
        """Convert pygraph graph to theJIT compatible tree. This will fail if you have a
        'disconnected' graph"""
        thejit_graph = self._make_node(graph, graph.nodes()[0], [])
        return thejit_graph


    def _make_node(self, graph, node, all_nodes):
        """Create a jit node from pygraph nodes. Check if there any 'data' attrs inside `graph`
        we can use"""
        jit_node = {}
        jit_node['id'] = node
        jit_node['name'] = graph.node_attr[node][0]['name']
        jit_children = []
        for child in graph.node_neighbors[node]:
            if child in all_nodes:
                # Avoid infinite recursion!
                continue
            jit_children.append(self._make_node(graph, child, all_nodes + [child]))
        jit_node['children'] = jit_children
        return jit_node      
