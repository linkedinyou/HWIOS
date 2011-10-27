/*# -*- coding: utf-8 -*-
"""
    scripts.app
    ~~~~~~~~~~~

    Main application file

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
*/
require.packaged = true;
var application = {functions:{},modules:{},plasmoids:{}}

define('app',[
'lib/tools/maps',
'modules/ui',
'lib/codemirror2/codemirror',
'lib/tools/xregexp',
'lib/tools/math',
'lib/jquery/jquery.serialobj',
'lib/jquery/jquery.class',
'lib/jquery/jquery.ws',
'lib/jquery/jquery.context',
'lib/tools/diff_match_patch',
'order!lib/codemirror2/mode/xml/xml',
'order!lib/codemirror2/mode/javascript/javascript',
'order!lib/codemirror2/mode/css/css',
'order!lib/codemirror2/mode/htmlmixed/htmlmixed',
'order!lib/codemirror2/mode/markdown/markdown',
'order!lib/jinfinote/jinfinote',
'order!lib/jquery/jquery.jinfinote',
],
function(maps){
    application.maps = maps;
    application.dom_buffer = {};
    //for now hardcode the list of accessible modules, so we can savely ignore around non-routable urls
    //pages is not routed at all, because we dont want a page prefix do we? :p
    application.modules = {
        blog:false,
        teknon:false,
        profiles:false,
        messenger:false,
        wiki:false,
        slide:false,
        ui:false,
        opensim:false,
        pages:false,
        settings:false,
        my_mod:false,
        activity:false,
        pad:false
    }
       
       
    _modules = [];
    var offline_trigger;
    var ssl = false;
    var ready = false;
    

    application.uri_back = function(steps){
        steps === undefined ? steps = 1: steps = steps;
        window.history.back(steps);
    }
    
    application.route_uri_to_mod = function(uri, push_history) {
        var mod_name;
        var _split = uri.split('/');
        //http://myhost without parameters should route to a default application

        //data function like /data/mymod/foo/bar/ 
        if(uri.indexOf('data') != -1) {
            mod_name = _split[2];            
        }
        else if(_split.length == 2) {
            uri = '/blog/';
            mod_name = 'blog';
        }
        //regular url-function /mymod/foo/bar/
        else {
            mod_name = _split[1];
        }
        //check previous module
        application.params.cb_selected = 0;
        if(mod_name in application.modules){
            if(application.mod_execute != mod_name && application.mod_execute !== undefined) {
                application.modules[application.mod_execute].clean_up();
            }
            //already loaded
            if(mod_name in application.modules && application.modules[mod_name] != false) {
                application.modules[mod_name].load(uri, push_history);
                application.mod_execute = mod_name;
            }
            else {
                require(['modules/'+mod_name], function(module) {
                    var mod_name = module.init(uri, push_history);
                    application.modules[mod_name] = module;
                    application.mod_execute = mod_name;
                });
            }
            return mod_name;
        }
        else {
            //anchor-only channel
            application.ws.remote(uri,{},function(response){
                $.each(response.data.anchors, function(idx,anchor) {
                    console.log('Loading anchor "'+anchor.slug+'"...');
                    application.load_anchor(anchor);
                });
                history.pushState({}, null, uri);
                application.functions.ui.mark_menu();
            });
        }
    }
    
    //Module tries to find it's way from it's own submitted routes
    application.route_uri_to_mod_function = function(uri, routes, push_history){        
        //handle possible anchor hash in the url (most notable in tabs)
        if(uri.indexOf('#') != -1) {uri = uri.split('#')[0];}
        $.each(routes,function(idx, route){
            var method_match = uri.match(route[0]);
            var params = {};
            if(method_match != null) {
                for (key in method_match) {
                    if (isNaN(key) && key !='index' && key !='input') {    
                        params[key] = method_match[key];
                    }
                }
                //call matching function
                route[1](params);
                //push state if desired
                if(push_history){
                    if(location.pathname != uri) {
                        if('pushState' in history){
                        history.pushState(params, null, uri);
                        application.functions.ui.mark_menu();
                        }
                    }
                }
            return false;
            }
        });
    }
    
    //Button router, accepts data-function(module.function), data-uri and uri_holder(flag post-processing)
    application.route_button = function(button){
        var params = button.data();
        //We have some special template cases, marked with a data-flag
        if('uri' in params) {
            if(params.uri.indexOf('data') == -1){
                application.route_uri_to_mod(params.uri, true);
            }
            else {
                application.route_uri_to_mod(params.uri, false);
            }
        }
        else if('function' in params) {
            try {var function_ref = params['function'].split('.');}
            catch(err) {
                console.warn('data-function format should be "module.function". Input was "'+params['function']+'"');
                return;
            }
            if (typeof application.functions[function_ref[0]][function_ref[1]] === 'function') {
                application.functions[function_ref[0]][function_ref[1]](params);
            }
            else {                
                console.warn('"'+params['function']+'" doesn\'t route to an existing module function. Available module functions are:');
                console.log(application.functions);
            }
        }  
        else if('uripart' in params) {
            if(!('uriflag' in params)) {
            console.warn('uri-holder needs a data-flag!');
            return;
            }
            //In some cases the cid can't be known at forehand in the template. Handle some of those cases with flags
            switch(params.uriflag) {
                case 'cb-cid':
                    var uri_holder = button.data('uripart');
                    //Suppose UUID or other Resource indicator stored in checkbox ID
                    var cb = $(".datatable :checkbox:checked:visible")[0];
                    var id = $(cb).attr('id');
                    //var uri = uri_holder.replace("^\{(\w*?)\}$",uuid);
                    params.uri = uri_holder.replaceKeys({id:id});
                break;
                case 'random-cid':
                    var uri_holder = button.data('uripart');
                    var id = Math.uuid();
                    params.uri = uri_holder.replaceKeys({id:id});
                break;
                case 'id':
                    var uri_holder = button.data('uripart');
                    params.uri = uri_holder.replaceKeys({id:button.data('id')});                    
                break;
            }
            application.route_uri_to_mod(params.uri, true);
            button.removeData('uri');
        }
        else {
            //console.warn('Button has no valid routing options!');
        }
    }
    
   
    application.load_anchor = function(anchor) {
        //anchor is html, css or javascript
        //store html/css first in a buffer. user is responsible for placement
        //using the entity uuid as a reference
        $.each(anchor.entities, function(idx, entity){
            if(entity.type == 0 || 1) {
                application.dom_buffer[entity.uuid] = entity.code;
            }
        });        
        $.each(anchor.entities, function(idx, entity){
            if(entity.type == 2) {
                try {eval(entity.code);}
                catch(error){console.log(error);}
            }
        });
    }

    application.prepare_form = function(form) {
        var form_data = $(form).serializeObject();
        //sync with non-form elements that contain values, like an rte
        $.each(form_data, function(idx, value){
            var _selector = $(form).find('#'+idx);
            if(_selector.length > 0){
                $('#id_'+idx).val(_selector.html());
            }        
        });
        form_data = $(form).serializeObject();
        return form_data;
        //rich elements have the same id as hidden input fields
    }

    application.merge_objects = function(object1, object2) {
        for(var i in object2) {
            if(!object1.hasOwnProperty(i)) {
            object1[i] = object2[i];
            }
        }
        return object1;
    }
    
    //Language specific object 
    application.il8n = {notify:{0:'Error',1:'Warning',2:'Info'}}
    
    function optimize_tt(tt) {
        var _optimized = {};
        $.each(tt, function(value, idx){
            _optimized[idx] = value;
        });
        return _optimized;
    }


    function load_modules(modules) {
        //this is a bit hackish. ui, activity and messenger hardcoded atm
        require(modules, function(module, module1, module2) {
            var mod = module.init();
            module1.init();
            module2.init();
            $(document).trigger('WS_ONLINE');
            //Double redundant code(check open websocket)
                if(application.redirect != null){
                    application.route_uri_to_mod(application.redirect, true);
                    application.redirect = null;
                }
                else {
                    var default_location = window.location.pathname + document.location.hash;
                    if(default_location == '/') {
                        default_location = '/blog/';
                }
            application.route_uri_to_mod(default_location, true);
            }
        });
        return true;
    }
    
    
    function init_websocket() {
        $(document).bind('BAD_BROWSER',function(e, err_code){
            if(err_code == 'NO_WEBSOCKET'){
                $.post("/misc/bad_browser/",{code:err_code}, function(response){
                    $('body').html('<div id="bad-browser"></div>');
                    var i18nButtons = {};
                    i18nButtons[gettext('Get a real browser')] = function(){
                    window.open ("http://build.chromium.org/f/chromium/snapshots/","mywindow");
                    }
                    $login = $(response.data.dom.dialog).dialog({
                    dialogClass: 'badbrowser-dialog',autoOpen: true,position:"center", width:450,
                    title: '<span class="ui-icon ui-icon-cancel"></span><span>'+gettext('Bad Browser!')+'</span>',
                    resizable: false,draggable: true,modal: true, buttons: i18nButtons, zIndex:1000000,
                    close: function(){                        
                        window.open ("/","_self");
                    },
                    });

                },"json");
            }
        });
        var ws_uri = application.settings.services.web_ui.uri;
        var ssl = application.settings.services.web_ui.ssl;
        if (ssl){var ws_url = 'wss://'+ws_uri+'/ws'} else {var ws_url = 'ws://'+ws_uri+'/ws'}
        application.ws = $.websocket(ws_url, {
                open: function() {                    
                    application.cache.load.context = {};
                    $('.activity-loading').remove();
                    this.tt = optimize_tt(application.settings.tt);
                    if(application.modloader === undefined){
                        application.modloader = load_modules(_modules);
                    }
                    else {
                        $(document).trigger('WS_ONLINE');
                        if(application.redirect != null){
                            application.route_uri_to_mod(application.redirect, true);
                            application.redirect = null;
                        }
                        else {
                            var default_location = window.location.pathname + document.location.hash;
                            if(default_location == '/') {
                                default_location = '/blog/';
                            }
                            application.route_uri_to_mod(default_location, true);
                        }
                    }
                    $('div[class*="hwios-plasmoid"]').remove();
                    console.log('Websocket open...');
                },
                close: function() {
                    application.cache.load.context = {};
                    console.log('Websocket closed...');
                    if(offline_trigger == false) {
                    $(document).trigger('WS_OFFLINE');
                    offline_trigger = true;
                    }
                setTimeout(function(){init_websocket()}, 500);
                },
                message_cb: function(type, data){
                    if(type == 'anchors') {
                        $.each(data, function(idx,anchor) {
                            console.log('Loading anchor "'+anchor.slug+'"...');
                            application.load_anchor(anchor);
                        });  
                    }
                },
        });
    }
    
    return {             
        init:function(client_init, modules) {
            String.prototype.replaceKeys = function(rs) { 
                return this.replace(/\{(\w+)\}/, function(_, k) { 
                    if (rs.hasOwnProperty(k)) { 
                        return rs[k];                         
                    } else { 
                        return k;                        
                    } 
                });                
            };
            
            _modules = modules;
            application.settings = client_init.settings;
            application.cache = {load:{context:{}}};
            application.params = {};
            init_websocket();          
        },

    }    
});