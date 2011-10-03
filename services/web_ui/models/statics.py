# -*- coding: utf-8 -*-
"""
    services.web_ui.models.statics
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Register custom javascript translation strings here, so they end up in the translation file

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django.utils.translation import ugettext_lazy as _

ws_table = {
'notify-error': 0,
'notify-warning': 1,
'notify-info': 2    
}

_('Register')
_('Logout')
_('Maps')
_('Profiles')
_('Profile Management')
_('Region Management')
_('Avatar Management')
_('Settings')