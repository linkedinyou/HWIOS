# -*- coding: utf-8 -*-
"""
    services.web_ui.models.clients
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Defines the general Client object that keeps state between HTTP and Websocket mode

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from core.application import HWIOS
from web_ui.models.signal import Signal

class TrackerMiddleware:
    """Small middleware that can track urls also in HTTP-mode. Not really used AFAIK atm."""

    def process_request(self, request):
        """Process each request, add the url to the client's view history and signal that the view has changed.

        :param request: The django request object to handle

        """
        #this is a path being used within django, and not some call in twisted
        if 'views' in request.path:
            if request.user.is_authenticated():
                client = HWIOS.ws_realm.pool.get_client(request.user.profile.uuid)
                if client:
                    client.transport.view_history.append(request.path)
                    #filter on the previous page view. should look like /views/wiki/*slug*/edit/
                    HWIOS.ws_realm.pool.signals.send('view_changed', client = client, filters = [client.transport.view_history[-2],client.transport.view_history[-1]])
                
