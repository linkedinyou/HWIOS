# -*- coding: utf-8 -*-
"""
    core.tools
    ~~~~~~~~~~

    Defines some handy functions that are used throughout hwios, making it easier to swap out components.

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

from django.http import HttpResponse

#favor ujson as main decoder, since it's faster than other implementations like simplejson
class sjson_serialize(object):


    def encode(self, some_dict):
        return json.dumps(some_dict)


    def decode(self, some_dict):
        return json.loads(some_dict)


class ujson_serialize(object):


    def encode(self, some_dict):
        return json.encode(some_dict)


    def decode(self, some_dict):
        return json.decode(some_dict)
      

try:
    import ujson as json
    serializer = ujson_serialize()
except ImportError:
    import simplejson as json
    serializer = sjson_serialize()



class Tools(object):
    """The Tool class is added to the HWIOS namespace for easy inclusion in other parts"""
    
    #import simplejson as json
    #json_decoder = json.JSONDecoder()
    #json_encoder = json.JSONEncoder(encoding='utf-8')
    
    def json_decode(self, some_dict):
        """Decodes some dict
        :param dict some_dict: Decodes some dict (as utf-8)
        """
        return serializer.decode(some_dict)

        
    def json_encode(self, some_dict):
        """Encodes some dict
        :param dict some_dict: Encodes some dict (as utf-8)
        """
        return serializer.encode(some_dict)
        #return self.json_encoder.encode(some_dict)
        
    def is_long(self, s):
        """Check if a variable is a long.

        :param int s: The int to test
        :return: long or False
        """
        try: 
            long(s)
            return long(s)
        except ValueError:
            return False


class JSONResponse(HttpResponse):
    def __init__(self, content= ''):
        super(JSONResponse, self).__init__(Tools().json_encode(content), mimetype='application/json', status=None, content_type=None)
