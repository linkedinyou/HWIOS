# -*- coding: utf-8 -*-
"""
    urls.py
    ~~~~~~~

    Defines all http and websocket routes

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django.conf.urls.defaults import *
from web_ui.controllers.http.feeds.blog import LatestArticlesFeed
import settings as settings

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('web_ui','web_ui.models','web_ui.models.no_fixture'),
}

#http patterns
urlpatterns = patterns('',
(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
(r'^misc/splash/$', 'web_ui.controllers.http.misc.splash'),
(r'^misc/bad_browser/$', 'web_ui.controllers.http.misc.bad_browser'),
(r'^data/profiles/login/$','web_ui.controllers.http.profiles.login_profile'),
(r'^data/profiles/logout/$','web_ui.controllers.http.profiles.logout_profile'),

(r'^data/opensim/avatars/luggage/upload/$','web_ui.controllers.http.opensim.upload_luggage'),
(r'^data/opensim/regions/scenes/upload/$', 'web_ui.controllers.http.opensim.upload_scenes'),
(r'^misc/elconnector/$', 'web_ui.controllers.http.misc.elconnector'),

#feeds
(r'^feeds/blog/$', LatestArticlesFeed()),
#all other urls return the bootstrapping view
(r'^', 'web_ui.controllers.http.misc.index'),
)

if settings.DEBUG:    
    urlpatterns += patterns((r'^debug/', include('hwios.debug.urls')))

'''
websocket patterns
urls that result in a page-view start with /views/
views are typical 'get/post' form combinations, where an url without params contains the form user-interface. The same url with params performs the form-action, 
and either returns a form error or returns to the main module after success. Main module returns are internal redirects in the view.

urls that point to data-updates, start with /data/
urls consist of a uri ending with an action defined in the last /option/ of the url, and are either crud(/create/read/update/delete/) or customized actions 
'''
ws_patterns = [
    #example module uri's
    (r'^/my_mod/$', 'web_ui.controllers.ws.my_mod', 'WS_MyMod', 'view_my_mod'),
    (r'^/my_mod/notify/$', 'web_ui.controllers.ws.my_mod', 'WS_MyMod', 'notify'),
    (r'^/my_mod/trip/$', 'web_ui.controllers.ws.my_mod', 'WS_MyMod', 'trip'),
    
    #activity uri's
    (r'^/data/activity/$','web_ui.controllers.ws.activity','WS_Activity','get_activities'),
    
    #misc uri's
    (r'^/views/misc/about/$', 'web_ui.controllers.ws.misc', 'WS_Misc', 'read_about'),    
    
    #pages uri's
    (r'^/pages/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'list_pages'),
    (r'^/pages/new/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'create_page'),
    (r'^/pages/(?P<uuid>[^/]+)/edit/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'edit_page'),    
    (r'^/pages/entities/new/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'create_entity'),
    (r'^/data/pages/delete/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'delete_pages'),
    (r'^/data/pages/scripts/(?P<script_id>[^/]+)/save/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'save_page'),
    (r'^/data/pages/scripts/(?P<script_id>[^/]+)/connect/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'connect_plasmoid_editor'),
    (r'^/data/pages/scripts/(?P<script_id>[^/]+)/disconnect/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'disconnect_plasmoid_editor'),
    (r'^/data/pages/scripts/(?P<script_id>[^/]+)/insert/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'request_plasmoid_insert'),
    (r'^/data/pages/scripts/(?P<script_id>[^/]+)/remove/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'request_plasmoid_delete'),
    (r'^/data/pages/scripts/(?P<script_id>[^/]+)/undo/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'request_plasmoid_undo'),
    (r'^/data/pages/scripts/(?P<script_id>[^/]+)/caret/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'update_remote_caret'),
    (r'^/data/pages/scripts/(?P<script_id>[^/]+)/play/$', 'web_ui.controllers.ws.pages', 'WS_Pages', 'play_plasmoid_script'),
    
    
    #pad uri's
    (r'^/pad/context/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'get_context'),
    (r'^/pad/(?P<pad_id>[^/]+)/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'sync_pad'),
    (r'^/data/pad/(?P<pad_id>[^/]+)/save/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'save_pad'),
    (r'^/data/pad/(?P<pad_id>[^/]+)/mouse/bc/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'bc_mouse_position'),
    (r'^/data/pad/(?P<pad_id>[^/]+)/mouse/leave/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'leave_mouse'),
    
    (r'^/data/pad/(?P<pad_id>[^/]+)/layers/(?P<layer_id>[^/]+)/draw/brush/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'draw_brush'),
    (r'^/data/pad/(?P<pad_id>[^/]+)/layers/(?P<layer_id>[^/]+)/draw/shape/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'draw_shape'),
    (r'^/data/pad/(?P<pad_id>[^/]+)/layers/(?P<layer_id>[^/]+)/draw/text/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'draw_text'),  
    (r'^/data/pad/(?P<pad_id>[^/]+)/layers/(?P<layer_id>[^/]+)/draw/fill/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'draw_fill'), 
    
    (r'^/data/pad/(?P<pad_id>[^/]+)/clear/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'clear_pad'),   
    (r'^/data/pad/(?P<pad_id>[^/]+)/layers/(?P<layer_name>[^/]+)/create/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'create_layer'),
    (r'^/data/pad/(?P<pad_id>[^/]+)/layers/(?P<layer_name>[^/]+)/delete/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'delete_layer'),
    (r'^/data/pad/(?P<pad_id>[^/]+)/layers/(?P<layer_id>[^/]+)/order/$', 'web_ui.controllers.ws.pad', 'WS_Pad', 'change_layer_order'),
    
    
    #messenger uri's
    (r'^/data/messenger/init/$', 'web_ui.controllers.ws.messenger', 'WS_Messenger', 'init_messenger'),
    (r'^/data/messenger/message/send/$', 'web_ui.controllers.ws.messenger', 'WS_Messenger', 'send_message'),
    
    #wiki uri's
    (r'^/wiki/context/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'get_context'),
    (r'^/wiki/(?P<slug>[^/]+)/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'view_wiki_article'),
    
    (r'^/wiki/(?P<slug>[^/]+)/edit/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'edit_wiki_article'),
    (r'^/wiki/(?P<slug>[^/]+)/edit/history/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'edit_history'),
    (r'^/data/wiki/(?P<slug>[^/]+)/edit/notify/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'notify_editors'),
    (r'^/data/wiki/(?P<slug>[^/]+)/save/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'save_page'),
    (r'^/data/wiki/(?P<slug>[^/]+)/delete/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'delete_page'),
    (r'^/data/wiki/(?P<slug>[^/]+)/insert/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'request_wiki_insert'),
    (r'^/data/wiki/(?P<slug>[^/]+)/remove/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'request_wiki_remove'),
    (r'^/data/wiki/(?P<slug>[^/]+)/undo/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'request_wiki_undo'),
    (r'^/data/wiki/(?P<slug>[^/]+)/caret/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'update_remote_caret'),
    
    #wiki plasmoid api
    (r'^/data/wiki/tree/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'plasmoid_get_wiki_tree'),


    #blog uri's
    (r'^/blog/$', 'web_ui.controllers.ws.blog', 'WS_Blog', 'view_blog'),
    (r'^/blog/context/$', 'web_ui.controllers.ws.blog', 'WS_Blog', 'get_context'),
    (r'^/blog/create/$', 'web_ui.controllers.ws.blog', 'WS_Blog', 'create_blog_article'),
    (r'^/blog/(?P<slug>[^/]+)/$', 'web_ui.controllers.ws.blog', 'WS_Blog', 'view_blog_article'),
    (r'^/blog/(?P<slug>[^/]+)/edit/$', 'web_ui.controllers.ws.blog', 'WS_Blog', 'edit_blog_article'),
    (r'^/data/blog/(?P<slug>[^/]+)/delete/$', 'web_ui.controllers.ws.blog', 'WS_Blog', 'delete_blog_article'),
    (r'^/data/blog/(?P<slug>[^/]+)/comments/create/$', 'web_ui.controllers.ws.blog', 'WS_Blog', 'create_article_comment'),
    (r'^/data/blog/(?P<slug>[^/]+)/comments/(?P<uuid>[^/]+)/delete/$', 'web_ui.controllers.ws.blog', 'WS_Blog', 'delete_article_comment'),
    #(r'^/data/blog/(?P<slug>[^/]+)/edit/notify/$', 'web_ui.controllers.ws.wiki', 'WS_Wiki', 'notify_editors'),
   
    
    #opensim uri's
    (r'^/opensim/settings/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'handle_settings'),
    (r'^/opensim/regions/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'view_regions'),
    (r'^/opensim/regions/create/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'create_region'),
    (r'^/opensim/regions/(?P<region_uuid>[^/]+)/edit/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'edit_region'),
    (r'^/opensim/regions/scenes/upload/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'upload_scenes'),
    (r'^/opensim/avatars/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'view_avatars'),
    (r'^/opensim/avatars/luggage/upload/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'upload_luggage'),    
    
    (r'^/data/opensim/maps/render/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'render_maps'),
    (r'^/data/opensim/regions/(?P<region_uuid>[^/]+)/backup/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'backup_region'),    
    (r'^/data/opensim/regions/delete/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'delete_regions'),    
    (r'^/data/opensim/regions/scenes/(?P<scene_name>[^/]+)/load/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'load_scene'),
    (r'^/data/opensim/regions/scenes/delete/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'delete_scenes'),
    (r'^/data/opensim/avatars/sync/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'sync_avatars'),
    (r'^/data/opensim/avatars/luggage/(?P<profile_uuid>[^/]+)/backup/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'backup_luggage'),
    (r'^/data/opensim/avatars/luggage/(?P<luggage_name>[^/]+)/load/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'load_luggage'),    
    (r'^/data/opensim/avatars/luggage/delete/$', 'web_ui.controllers.ws.opensim', 'WS_OpenSim', 'delete_luggage'),
    
    #map uri's
    (r'^/maps/$', 'web_ui.controllers.ws.maps', 'WS_Maps', 'load_maps'),
    (r'^/data/maps/cells/read/$', 'web_ui.controllers.ws.maps', 'WS_Maps', 'read_cell'),

    #profile uri's
    (r'^/profiles/context/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'get_context'),
    (r'^/profiles/manage/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'manage_profiles'),
    (r'^/profiles/my_profile/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'edit_my_profile'),
    (r'^/profiles/create/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'create_profile'),
    (r'^/profiles/(?P<username>[^/]+)/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'view_profile'),
    (r'^/profiles/(?P<username>[^/]+)/whois/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'whois_profile'),
    (r'^/profiles/(?P<username>[^/]+)/edit/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'edit_profile'),
    (r'^/profiles/activate/(?P<profile_uuid>[^/]+)/$','web_ui.controllers.ws.profiles', 'WS_Profiles', 'activate_profile'),
    
    (r'^/data/profiles/login/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'login_profile'),
    (r'^/data/profiles/register/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'register_profile'),
    (r'^/data/profiles/delete/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'delete_profiles'),     
    (r'^/data/profiles/(?P<username>[^/]+)/follow/$', 'web_ui.controllers.ws.profiles', 'WS_Profiles', 'follow_profile'),
    
    #teknon uri's   
    (r'^/teknon/$','web_ui.controllers.ws.teknon', 'WS_Teknon', 'view_pool'),
    (r'^/teknon/services/(?P<service_uuid>[^/]+)/sim_slave_ini/edit/$', 'web_ui.controllers.ws.teknon', 'WS_Teknon', 'edit_sim_slave_ini'),
    (r'^/teknon/services/(?P<service_uuid>[^/]+)/sim_slave_ini/save/$', 'web_ui.controllers.ws.teknon', 'WS_Teknon', 'save_sim_slave_ini'),
    
    (r'^/data/teknon/services/start/$','web_ui.controllers.ws.teknon', 'WS_Teknon', 'confirm_start_services'),
    (r'^/data/teknon/services/stop/$','web_ui.controllers.ws.teknon', 'WS_Teknon', 'confirm_stop_services'),
    (r'^/data/teknon/services/kill/$','web_ui.controllers.ws.teknon', 'WS_Teknon', 'confirm_kill_services'), 
    (r'^/data/teknon/services/switch/$', 'web_ui.controllers.ws.teknon', 'WS_Teknon', 'switch_services'),
    (r'^/data/teknon/services/watchdog/switch/$', 'web_ui.controllers.ws.teknon', 'WS_Teknon', 'switch_watchdog'),
    (r'^/data/teknon/services/subscribe_console/$', 'web_ui.controllers.ws.teknon', 'WS_Teknon', 'subscribe_console'),
    (r'^/data/teknon/services/unsubscribe_console/$', 'web_ui.controllers.ws.teknon', 'WS_Teknon', 'unsubscribe_console'),    
    (r'^/data/teknon/services/(?P<service_uuid>[^/]+)/send_command/$', 'web_ui.controllers.ws.teknon', 'WS_Teknon', 'send_service_command'),
    
    (r'^/data/teknon/services/(?P<service_uuid>[^/]+)/proxy_stdout/$', 'web_ui.controllers.ws.teknon', 'WS_Teknon', 'proxy_service_stdout'),
    (r'^/data/teknon/$', 'web_ui.controllers.ws.teknon', 'WS_Teknon', 'update_view'),
    (r'^/data/teknon/services/state/update/$', 'web_ui.controllers.ws.teknon', 'WS_Teknon', 'update_service_state'),
    
    #settings uri's
    (r'^/settings/$', 'web_ui.controllers.ws.settings', 'WS_Settings', 'load_settings'),
    (r'^/data/settings/save/$', 'web_ui.controllers.ws.settings', 'WS_Settings', 'save_settings'),      
    
]