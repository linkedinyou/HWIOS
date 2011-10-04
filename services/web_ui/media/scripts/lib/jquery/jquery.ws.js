/*
* jQuery Web Sockets Plugin v0.0.1
* http://code.google.com/p/jquery-websocket/
*
* This document is licensed as free software under the terms of the
* MIT License: http://www.opensource.org/licenses/mit-license.php
* 
* Copyright (c) 2010 by shootaroo (Shotaro Tsubouchi).
*
* 
* Customized for the HWIOS project 
*
/*# -*- coding: utf-8 -*-
"""
    lib.jquery.jquery.ws
    ~~~~~~~~~~~~~~~~~~~~

    Websocket router

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
*/

/*!
Math.uuid.js (v1.4)
http://www.broofa.com
mailto:robert@broofa.com

Copyright (c) 2010 Robert Kieffer
Dual licensed under the MIT and GPL licenses.
*/
var CHARS = '0123456789abcdefghijklmnopqrstuvwxyz'.split('');
Math.uuidFast = function() {
    var chars = CHARS, uuid = new Array(36), rnd=0, r;
    for (var i = 0; i < 36; i++) {
      if (i==8 || i==13 ||  i==18 || i==23) {
        uuid[i] = '-';
      } else if (i==14) {
        uuid[i] = '4';
      } else {
        if (rnd <= 0x02) rnd = 0x2000000 + (Math.random()*0x1000000)|0;
        r = rnd & 0xf;
        rnd = rnd >> 4;
        uuid[i] = chars[(i == 19) ? (r & 0x3) | 0x8 : r];
        }
    }
    return uuid.join('');
};


function decode_utf8( s ) {
return decodeURIComponent( escape( s ) );
}


(function($){
$.extend({
    websocketSettings: {
        open: function(){},
        close: function(){},
        message: function(){},
        error: function(){},
        options: {},
        methods: {},
        message_cb: function(){},
    },
    websocket: function(url, s) {
        if ("WebSocket" in window) {
            var ws = WebSocket ? new WebSocket( url ) : {
                send: function(m){ return false },
                close: function(){},
                open: function(){},
                error: function(){}};
            ws.remote_callback = {};
        }
        //mozilla uses prefix nowadays
        else if('MozWebSocket' in window){
            var ws = MozWebSocket ? new MozWebSocket( url ) : {
                send: function(m){ return false },
                close: function(){},
                open: function(){},
                error: function(){}};
            ws.remote_callback = {};
        }
        else {
            $(document).trigger('BAD_BROWSER',['NO_WEBSOCKET']);
            return false;
        }
        ws._settings = $.extend($.websocketSettings, s);
        ws.redirect = null;
        $(ws).bind('open', $.websocketSettings.open)
            .bind('close', $.websocketSettings.close)
            .bind('error', $.websocketSettings.error)
            .bind('message', function(e){
                var response = JSON.parse(e.originalEvent.data);
                //function: ['my_function',{param1: myparam, param2: myparam2},method_uuid]
                if (response instanceof Array && typeof(response[0]) == 'string') {
                    var match = false;
                    $.each($.websocketSettings.methods, function(pattern, registered_method) {
                        //match function against array of registered methods
                        var method_match = response[0].match(registered_method[0]);
                        var params = {}
                        //put all of our array keys which may include GET params into a plain object
                        if(method_match != null) {
                            match = true;
                            for (key in method_match) {
                                if (isNaN(key) && key !='index' && key !='input') {                                    
                                    params[key] = method_match[key];   
                                }
                            }
                            //if our params element is an array, stuff it in a params key
                            if (response[1] instanceof Array) {                               
                                params['params'] = response[1];
                            }
                            //dict to json object
                            else {
                                for(key in response[1]) {
                                    params[key] = response[1][key]
                                }     
                            }
                            if('status' in response[1]) {
                                $("#notify-container").notify("create",ws.tt[response[1].status.type], {i18n: response[1].status.i18n});
                                if('state' in response[1]['status']) {
                                    history.pushState(null, null, response[1].status.state);
                                }
                            }
    
                            registered_method[1](params);
                        }                        
                    });
                    //no method match, but a notification was found
                    if('status' in response[1] && match == false) {
                        $("#notify-container").notify("create",ws.tt[response[1].status.type], {i18n: response[1].status.i18n});
                    }  
                }
                //response data [{'param1':param1,'param2':param2},'origin url', method_uuid]
                else {
                    
                     //no access granted, handle gracefully
                    if(response[0] == false) {
                        console.log('Access to resource denied...');
                    }
                    else if(response[0] != null) {
                        //var origin = response.splice(1,1)[0];
                        //match origin with available callbacks
                        $.each(ws.remote_callback[response[1]], function(method_uuid, _callback) {           
                            if(method_uuid == response[2]) {
                                if('status' in response[0]) {
                                    if('i18n' in response[0].status) {
                                        $("#notify-container").notify("create",ws.tt[response[0].status.type], {i18n: response[0].status.i18n});
                                    }
                                    if('state' in response[0].status) {
                                        history.pushState(null, null, response[0].status.state);    
                                    }
                                }
                                _callback(response[0]);
                                delete(ws.remote_callback[response[1]][method_uuid]);
                                if(response[0]['data'] != undefined) {
                                    if('plasmoids' in response[0]['data']) {
                                        ws._settings['message_cb']('plasmoids',response[0]['data']['plasmoids']);
                                    }
                                }
                            }                    
                        });
                    }
                }
            });
            
        ws.remote = function(method,params,callback) {
            if(!ws.remote_callback.hasOwnProperty(method)){
            ws.remote_callback[method] = {};
            }
            var _uid = Math.uuidFast();
            ws.remote_callback[method][_uid] = callback;
            return ws.send(JSON.stringify([method,params, _uid]))
        }
        
        ws.method = function(pattern,callback) {
            var regexp = XRegExp(pattern);
            if(!(pattern in $.websocketSettings.methods)) {
                $.websocketSettings.methods[pattern] = [regexp,callback];
            }            
        }
        $(window).unload(function(){ ws.close(); ws = null });
        return ws;
    }
});
})(jQuery);