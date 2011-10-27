/*# -*- coding: utf-8 -*-
"""
    scripts.modules.wiki
    ~~~~~~~~~~~~~~~~~~~~

    Wiki module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
*/
require.def('modules/wiki',[

],
function(){

    var wiki_context;
    var markdown_worker = new Worker('/media/scripts/lib/tools/markdown_worker.js');
    var editor;
    var delayed_update;
    var editor_cache;
    var patch_text = null;
    var _patch_text = null;
    var current_rev = 0;
    var page_revisions;
    var sync_callback;
    var urls;
    
    //setup editor
    function initEditor(id, override_layout, add_text) {
        editor = $.jinfinote(application.ws, {
            ws_connect:'/wiki/'+id+'/edit/',
            ws_disconnect:'/wiki/'+id+'/disconnect/',
            ws_insert:'/data/wiki/'+id+'/insert/',
            ws_delete:'/data/wiki/'+id+'/remove/',
            ws_undo:'/data/wiki/'+id+'/undo/',
            ws_caret:'/data/wiki/'+id+'/caret/',
            cb_insert:'^/data/wiki/(?<id>[^/]+)/insert/$',
            cb_delete:'^/data/wiki/(?<id>[^/]+)/remove/$',
            cb_undo:'^/data/wiki/(?<id>[^/]+)/undo/$',
            cb_caret:'^/data/wiki/(?<id>[^/]+)/caret/$',
            mode:'markdown',
            init: 
                function(data) {
                    layout = data.dom.main;
                    page = data.article;
                    if (typeof(override_layout) == 'undefined') {
                        application.functions.ui.transition(data.dom.main, $('.main'));
                    }
                    else {
                        application.functions.ui.transition(override_layout.data.dom.main, $('.main'), override_layout.status.code);
                        $.each($('.main .errorlist'), function () {     
                        $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                        });   
                    }
                    if(data.ce.revisions < 2) {
                        $('#wiki-edit-history').addClass('ui-state-disabled');
                    }
                    apply_markdown($('#wiki-markdown'),data.ce.state[1]);
                    if(add_text !==undefined){
                        return {editor_element:'#wiki-editor',add_text: add_text}
                    }
                    else {
                        return {editor_element:'#wiki-editor'}
                    }
                }
            });

    }
    
    function initListener(id) {
        editor = $.jinfinote(application.ws,{
            ws_connect:'/wiki/'+id+'/',
            ws_disconnect:'/data/wiki/'+id+'/disconnect/',
            ws_insert:'/data/wiki/'+id+'/insert/',
            ws_delete:'/data/wiki/'+id+'/remove/',
            ws_undo:'/data/wiki/'+id+'/undo/',
            ws_caret:'/data/wiki/'+id+'/caret/',
            cb_insert:'^/data/wiki/(?<id>[^/]+)/insert/$',
            cb_delete:'^/data/wiki/(?<id>[^/]+)/remove/$',
            cb_undo:'^/data/wiki/(?<id>[^/]+)/undo/$',
            cb_caret:'^/data/wiki/(?<id>[^/]+)/caret/$',
            editor:'listen',
            init: 
                function(data) {
                    application.functions.ui.transition(data.dom.main, $('.main'),'');
                    //skip when article doesn't exist, and no editor is available
                    if(data.ce !== undefined) {
                        apply_markdown($('#wiki-markdown'),data.ce.state[1]);
                    }                    
                    return {editor_element:'#wiki-editor'}
                },
            
        });
    }  

    /**
        @param {String} target_element The element that is used to parse the wiki-text in
        @param {String} wiki_text The wiki text that's about to be parsed
    */
    function apply_markdown(target_element, wiki_text) {
        markdown_worker.postMessage(wiki_text);
    }

    markdown_worker.onmessage = function(event) {
        $('#wiki-markdown').html(event.data);
    };    
    

function bind_functions() {
    
    application.functions.wiki = {
        route: function(uri, push_history) {
            if(urls == undefined) {
                urls = [
                    [XRegExp('^/wiki/(?<id>[^/]+)/$'),this.view_article],
                    [XRegExp('^/wiki/(?<id>[^/]+)/edit/$'),this.edit_article],
                    [XRegExp('^/wiki/(?<id>[^/]+)/edit/history/$'),this.edit_article_history]
                ];
            }
            application.route_uri_to_mod_function(uri, urls, push_history);
        },
        
        view_article: function(kwargs) {
            $(document).trigger('WIKI_ARTICLE_LINK_FOLLOWED',{id: kwargs.id});
            initListener(kwargs.id);
        },
        
        edit_article: function(kwargs) {
            if(kwargs.id == undefined){
                kwargs.id = $('#btn-frontend-wiki-edit').data('url');
            }
            initEditor(kwargs.id);
        },

        edit_fullscreen: function(kwargs) {
            var _parent = $('.edit-wiki-article');
            //already in fullscreen mode
            console.log('blaa');
            if($(_parent).hasClass('wiki-fullscreen')){
                $(_parent).removeClass('wiki-fullscreen');
                $('#wiki-fullscreen-button').removeClass('fullscreen-button-fullscreen');
                $('.sidebar').removeClass('sidebar-fullscreen');
            }
            else {
                $(_parent).addClass('wiki-fullscreen');
                $('#wiki-fullscreen-button').addClass('fullscreen-button-fullscreen');
                //force the sidebar to be hidden, so it doesnt mess up the container height
                $('.sidebar').addClass('sidebar-fullscreen');
            }
            //somehow messes up codemirror line positioning
            //$('.edit-wiki-page').get(0).webkitRequestFullScreen();
            editor.editor.refresh();
        },
        
        cancel_edit_article: function(kwargs) {
            var form_data = $("form:visible").serializeObject();        
            initListener(kwargs.id);
        },
        
        edit_article_history: function(kwargs) {
            editor_cache = $('.main > .hwios-widget:first').html();
            var dmp = new diff_match_patch();            
                sync_callback = function(revisions) {
                    current_rev = $('#undo_slider').slider('option','value');
                    $('#id_submit_comments').val(revisions[current_rev-1].submit_comments);
                    revisions = revisions.slice(0, current_rev);
                    patches = new Array();
                    $.each(revisions, function(key, revision) {
                        patches.push(dmp.patch_fromText(revision.patch));
                    });
                    _patch_text = '';
                    $.each(patches, function(key, patch) {         
                        _patch_text = dmp.patch_apply(patch, _patch_text)[0];
                    });
                    apply_markdown($('#wiki-markdown'),_patch_text);
                }
                
                application.ws.remote('/wiki/'+kwargs.id+'/edit/history/',{},function(response){
                    page_revisions = response.ce.revisions;
                    application.functions.ui.transition(response.data.dom.main, $('.main'));
                    $.data($('#wiki-restore-button')[0],'revision',response.ce.revisions.length);
                        var _history_slider = $('#undo_slider').slider({ animate:true,min:1, max: response.ce.revisions.length,value: response.ce.revisions.length,
                            change: function(event, ui) {
                                var _value = $('#undo_slider').slider('option','value');
                                $('#undo_slider_value').html('@ '+_value);                                
                                $('#id_content').attr ('disabled', false);
                            },
                            slide: function(event, ui) {
                                var _value = $('#undo_slider').slider('option','value');                        
                                $('#undo_slider_value').html('<div class="change_to_text">@ '+_value+'</div>');
                                $('#id_content').attr('disabled', true);
                                //timed update. sync requests are computational heavy. Only perform when the user keeps the slider in place for a while
                                    if (typeof(delayed_update) == 'number') {
                                    clearTimeout(delayed_update);
                                    }
                                delayed_update = setTimeout(sync_callback(page_revisions),100);
                            },
                            stop: function(event, ui) {
                                var _value = $('#undo_slider').slider('option','value');
                                $.data($('#wiki-restore-button')[0],'revision',_value);
                                $('#undo_slider_value').html('<div class="change_to_text">@ '+_value+'</div>');
                                if (typeof(delayed_update) == 'number') {
                                clearTimeout(delayed_update);
                                }
                                sync_callback(page_revisions);
                            }
                        });
                    if(page_revisions.length > 0) {
                        sync_callback(page_revisions);
                        $('#undo_slider_value').text('@ '+$('#undo_slider').slider('option','value'));
                    }
                });
        },
        
        cancel_edit_article_history: function(kwargs) {
            $('.main').html(editor_cache).hide();
            initEditor(kwargs.id);
        },
        
        restore_article_history: function(kwargs) {
            application.ws.remote('/data/wiki/'+kwargs.id+'/edit/notify/',{revision:kwargs.revision},function(response){
                patch_text = _patch_text;
                initEditor(kwargs.id, undefined, patch_text);
            });
        },
        
        save_edit_article: function(kwargs) {
            var form_data = $("form:visible").serializeObject();
            form_data.content = editor._state.buffer.toString();
            application.ws.remote('/data/wiki/'+kwargs.id+'/save/',{params:form_data},function(response){
                switch(response.status.code) {
                    case "WIKI_EDIT_OK":
                        initListener(kwargs.id);
                        $(document).trigger('WIKI_ARTICLE_SAVED',{id:kwargs.id});
                    break;
                    case "WIKI_EDIT_NO_CHANGE":
                        initListener(kwargs.id);
                    break;
                    case "FORM_INVALID":
                        initEditor(kwargs.id, response);
                    break;
                }
            });
        },
        
        save_new_article: function(kwargs) {
            application.ws.remote('/data/wiki/'+kwargs.id+'/save/',{params:{id:kwargs.id,submit_comments:'Page created',content:''}},function(response){
                initEditor(kwargs.id);
                $(document).trigger('WIKI_ARTICLE_CREATED',{id:kwargs.id});
            });
        },
        
        delete_article: function(kwargs) {
            application.ws.remote('/data/wiki/'+kwargs.id+'/delete/',{}, function(response) {
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function(){
                    $(this).dialog('close');
                };
                i18nButtons[gettext('Delete')] = function(){
                    application.ws.remote('/data/wiki/'+kwargs.id+'/delete/',{params:{id:kwargs.id}},function(response){
                        switch(response.status.code) {
                            case "WIKI_DELETE_OK":
                                $('.main').html(response.data.dom.main).hide().fadeIn();
                                $(document).trigger('WIKI_ARTICLE_DELETED',{id:kwargs.id});
                            break;
                        }
                    });
                    $(this).dialog('close');
                }
                var _dialog = $(response.data.dom.dialog).dialog({
                    resizable: false,width:300, modal: true, zIndex:1000000,
                    title:'<span class="ui-icon ui-icon-alert"></span><span>'+gettext("Warning")+'!</span>',
                    buttons: i18nButtons
                });
            });
        },
    }
}

function bind_events() {
    //follow link to new wiki article when clicked
    $(".main").delegate("#wiki-markdown a", "click", function(event){
        event.preventDefault();
        url = $(event.target).attr('href');
        application.functions.wiki.route(url, true);
    }); 
    
    //we need a way to capture remote textarea update events
    $(document).bind('infinote_update', function(e) {
        apply_markdown($('#wiki-markdown'), editor._state.buffer.toString());
    });
}
    
    
function bind_ws() {
    
    application.ws.method('^/data/wiki/(?<id>[^/]+)/online/update/$', function(params){
        editor.update_online(params.online);
    });
    
    application.ws.method('^/data/wiki/(?<id>[^/]+)/edit/notify/$',function(request){

    });
    
    //remote function to trigger page update after 
    application.ws.method('^/wiki/(?<id>[^/]+)/$',function(request){
        var _url_resolve = window.location.pathname.split('/');
        var current_id = _url_resolve[2];
        var current_action = _url_resolve[3];
        if(current_id == request.id){
            //make sure to only update if the current article is the same, and the user is in observer mode
            if(current_action == ''){
                initListener(request.id);
            }
        }
        $(document).trigger('WIKI_ARTICLE_CREATED',{id:request.id});
    });    
    
    //when a user saves the same page, Notify all other clients.
    application.ws.method('/data/wiki/(?<id>[^/]+)/saved/',function(request){
        //means this client still has a history view in front of him/her
        if ($('#undo_slider').length > 0) {
            page_revisions.push(request.data.revision);
            $('#undo_slider').slider('option','max',[page_revisions.length]);
            $('#undo_slider').slider('option','value',[page_revisions.length]);
            sync_callback(page_revisions);
        }
        //enable history button in the editing session view, if it was still disabled and view is there
        if ($('#btn-frontend-wiki-edit-history').length > 0) {
            $('#btn-frontend-wiki-edit-history').removeClass('ui-state-disabled');
        }
    });     
    
    //Websocket listener for when a user removes a page, and server notifies other clients about this event
    application.ws.method('/data/wiki/(?<id>[^/]+)/deleted/',function(request){
        var _url_resolve = window.location.pathname.split('/');
        var current_id = _url_resolve[2];
        var current_action = _url_resolve[3];
        $(document).trigger('WIKI_ARTICLE_CREATED',{id:request.id});
        if(current_id == request.id){
            initListener(request.id);
        }
    }); 
}

function unbind_events() {

    $(".main").undelegate("#wiki-markdown a", "click");
}
   
    return {
        init: function(uri, push_history) {
            wiki_context = $.context({anchor:'.main',delegate:'#wiki-context',uri:'/wiki/context/',id:'ctx-wiki'});
            application.cache.load.context.wiki = true;
            bind_functions();
            bind_ws();
            bind_events(); 
            application.functions.wiki.route(uri, push_history);
            return 'wiki';
        },
        load: function(uri, push_history) {
            if(typeof application.cache.load.context.wiki == 'undefined') {
                application.cache.load.context.wiki = true;
                wiki_context.reload();
            }
            bind_events(); 
            application.functions.wiki.route(uri, push_history);
            $(document).trigger('WIKI_ARTICLE_LINK_FOLLOWED',{id:'Main'});
        },
        clean_up: function(){
            $('div[class*="page-widget-sidebar"]').remove();
            unbind_events();
        }
    }     
});
