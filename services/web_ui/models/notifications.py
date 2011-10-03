# -*- coding: utf-8 -*-
"""
    services.web_ui.models.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    View notification takes care of rendering and delivering templates to watching clients

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import re
from copy import deepcopy

from hwios.core.application import HWIOS
from django.template.loader import render_to_string

compiled_notify_patterns = {}

def _refresh_templates(message, template_info, profile):
    """Renders and returns a template"""
    try:
        dom = message['data']['dom']
        for key in dom:
            if key in template_info:
                _tpl_info = template_info[key]['params'].copy()
                _tpl_info.update({'profile': profile})
                message['data']['dom'][key] = render_to_string(template_info[key]['tpl'], _tpl_info)
                return message
    except KeyError:
        return False


def notify_others(source_client, _message, uri_route, client_match_uri = None, _template_info = None, uri_state = None):
    """Re-renders a source-client's view for other clients, that are watching the same view
    
    :param Client source_client: The client which is responsible for the change
    :param dict _message: Data that's being sent to the clients along with the template
    :param str uri_route: The client-side url to route this view to
    :param str client_match_uri: Regular expression filter to use for matching the current client's view
    :param dict _template_info: Directions to use to render the appropriate template
    :param str uri_state: Optional; Sometimes the view-state is supposed to change after notification. Specify new state here...
    
    """
    #check if compiled regexp pattern exists yet. if not, add to list
    if client_match_uri not in compiled_notify_patterns:
        compiled_notify_patterns[client_match_uri] = re.compile(client_match_uri)    
    _clients = HWIOS.ws_realm.pool.get_clients()
    if len(_clients) > 0:
        message = deepcopy(_message)
        template_info = deepcopy(_template_info)
        for _client in _clients:
            #process all, but our notification source client
            if _client != source_client:
                if client_match_uri != None:
                        rp = compiled_notify_patterns[client_match_uri].match(_client.transport.view_history[-1])
                        if rp != None:
                            if template_info != None:
                                message = _refresh_templates(message, template_info, _client.profile)
                            _client.remote(uri_route, message)
                            if uri_state != None:
                                _client.transport.view_history.append(uri_state)
                else:
                    if template_info != None:
                        message = _refresh_templates(message, template_info, _client.profile)
                    _client.remote(uri, message)
                

def notify_all(message, uri, same_page = False):
    """Dummy function which doens't have any functionality yet"""
    for _client in HWIOS.ws_realm.pool.get_clients():
        _client.remote(uri, message)


