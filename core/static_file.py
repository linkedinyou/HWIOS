# -*- coding: utf-8 -*-
"""
    core.static_file
    ~~~~~~~~~~~~~~~~

    Modified static-file resource to support gzip compression

    Twisted HTTP and websocket logics

    :copyright: 2001-2010 Twisted Matrix Laboratories.
    :license: MIT, see http://twistedmatrix.com/trac/browser/trunk/LICENSE
"""

import os
import struct
import zlib

from twisted.web import http
from twisted.web import static,server

class GzipRequest(object):
    """Wrapper for a request that applies a gzip content encoding"""

    def __init__(self, request, compressLevel=6):
        self.request = request
        self.request.setHeader('Content-Encoding', 'gzip')
        # Borrowed from twisted.web2 gzip filter
        self.compress = zlib.compressobj(compressLevel, zlib.DEFLATED,-zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL,0)


    def __getattr__(self, attr):
        if 'request' in self.__dict__:
            return getattr(self.request, attr)
        else:
            raise AttributeError, attr
        

    def __setattr__(self, attr, value):
        if 'request' in self.__dict__:
            return setattr(self.request, attr, value)
        else:
            self.__dict__[attr] = value
            

    def write(self, data):
        if not self.request.startedWriting:
            #print 'GzipRequest: Initializing'
            self.crc = zlib.crc32('')
            self.size = self.csize = 0
            # XXX: Zap any length for now since we don't know final size
            if 'content-length' in self.request.headers:
                del self.request.headers['content-length']
            # Borrow header information from twisted.web2 gzip filter
            self.request.write('\037\213\010\000' '\0\0\0\0' '\002\377')

        self.crc = zlib.crc32(data, self.crc)
        self.size += len(data)
        cdata = self.compress.compress(data)
        self.csize += len(cdata)
        #print 'GzipRequest: Writing %d bytes, %d total (%d compressed, %d total)' % (len(data),self.size,len(cdata),self.csize)
        if cdata:
            self.request.write(cdata)
        elif self.request.producer:
            # Simulate another pull even though it hasn't really made it
            # out to the consumer yet.
            self.request.producer.resumeProducing()


    def finish(self):
        remain = self.compress.flush()
        self.csize += len(remain)
        #print 'GzipRequest: Finishing (size %d, compressed %d)' % (self.size, self.csize)
        if remain:
            self.request.write(remain)
        self.request.write(struct.pack('<LL',
                                       self.crc & 0xFFFFFFFFL,
                                       self.size & 0xFFFFFFFFL))
        self.request.finish()


class StaticFile(static.File):
    """Modified static file resource with gzip support"""
    
    def __init__(self,*args,**kwargs):
        self.compression_types = ('text/css','application/x-javascript','application/x-font-ttf')
        static.File.__init__(self,*args,**kwargs)
        
        
    def getTypeAndEncoding(self,filename, types, encodings, defaultType):
        p, ext = os.path.splitext(filename)
        ext = ext.lower()
        if encodings.has_key(ext):
            enc = encodings[ext]
            ext = os.path.splitext(p)[1].lower()
        else:
            enc = None
        type = types.get(ext, defaultType)
        return type, enc
        

    def render_GET(self, request):
        if self.type is None:
            self.type, self.encoding = self.getTypeAndEncoding(self.basename(),self.contentTypes,self.contentEncodings,self.defaultType)
        if not self.exists(): return self.childNotFound.render(request)
        if self.isdir(): return self.redirect(request)
        accept_encoding = request.getHeader('accept-encoding')
        if accept_encoding != None:
            encodings = accept_encoding.split(',')
        else:
            encodings = ['gzip']
        if 'gzip' in encodings and self.type in self.compression_types:
            request = GzipRequest(request)
        request.setHeader('accept-ranges', 'bytes')
        try: fileForReading = self.openForReading()
        except IOError, e:
            import errno
            if e[0] == errno.EACCES:
                return resource.ForbiddenResource().render(request)
            else: raise
        request.setHeader('content-type', self.type)
        if request.setLastModified(self.getmtime()) is http.CACHED:
            #request.responseHeaders.removeHeader('content-type')
            return ''
        producer = self.makeProducer(request, fileForReading)
        if request.method == 'HEAD':
            return ''
        producer.start()
        return server.NOT_DONE_YET
    render_HEAD = render_GET