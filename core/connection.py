# -*- coding: utf-8 -*-
"""
    core.connection
    ~~~~~~~~~~~~~~~

    SSL Contextfactory, in case we want to start a twisted service with SSL support

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from OpenSSL import SSL

class ServerContextFactory:
    """The SSL Server Context Factory here specifies the ssl certificates to use as well"""
    def getContext(self):
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file('core/ssl/server.crt')
        ctx.use_privatekey_file('core/ssl/server.key')
        return ctx