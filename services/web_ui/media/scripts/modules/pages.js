/*
* Copyright (c) Contributors, http://hwios.org/
* See CONTRIBUTORS for a full list of copyright holders.
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*   * Redistributions of source code must retain the above copyright
*     notice, this list of conditions and the following disclaimer.
*   * Redistributions in binary form must reproduce the above copyright
*     notice, this list of conditions and the following disclaimer in the
*     documentation and/or other materials provided with the distribution.
*   * Neither the name of the HWIOS Project nor the
*     names of its contributors may be used to endorse or promote products
*     derived from this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE DEVELOPERS ``AS IS'' AND ANY
* EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE CONTRIBUTORS BE LIABLE FOR ANY
* DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
* (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
* LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
* SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.'''
*/

require.def('modules/pages',[],
            
function(){
    var editor;
    var plasmoid_uuid;
    var tabs;
    var selected_tab;
    var canvas_preview;
    var processing;
    var urls;
    
    
function get_cb_names() {
    var names = '<ul>';
        $.each($('.datatable :checkbox:checked:visible'), function(n, val) {
            var name = $(this).parent().next().text();
            if(name != '') {
            names = names + "<li>" + name +"</li>";
            }
            else {
            names = names + "<li>Unnamed - "+$(this).parent().next().next().text()+"</li>";    
            }
        });
    names += '</ul>'; 
    return names;
}
    
    
function init_helpers() {
    $('#slider-shutdown-time').slider({ animate:true,min:1, max: 60,value: 5,
        change: function(event, ui) {
        $('#id_shutdown_time').val($('#slider-shutdown-time').slider('option','value'));
        $('#slider-shutdown-time-indicator').text(gettext('Reboot')+' ('+$('#slider-shutdown-time').slider('option','value')+' sec.)');
        }
    });
    $('#id_shutdown_time').val($('#slider-shutdown-time').slider('option','value'));
    $('#slider-shutdown-time-indicator').text(gettext('Reboot')+' ('+$('#slider-shutdown-time').slider('option','value')+' sec.)');
}
    
    
function initEditor(uuid, response, ws_connect) {
    editor = $.jinfinote(application.ws, {
    ws_connect:ws_connect,
    ws_disconnect:'/data/pages/entities/'+uuid+'/disconnect/',
    ws_insert:'/data/pages/entities/'+uuid+'/insert/',
    ws_delete:'/data/pages/entities/'+uuid+'/remove/',
    ws_undo:'/data/pages/entities/'+uuid+'/undo/',
    ws_caret:'/data/pages/entities/'+uuid+'/caret/',
    cb_insert:'^/data/pages/entities/(?<uuid>[^/]+)/insert/$',      
    cb_delete:'^/data/pages/entities/(?<uuid>[^/]+)/remove/$',
    cb_undo:'^/data/pages/entities/(?<uuid>[^/]+)/undo/$',
    cb_caret:'^/data/pages/entities/(?<uuid>[^/]+)/caret/$',   
    mode:'javascript',
    init: 
        function(data) {
            if (response === undefined) {
                application.functions.ui.transition(data.dom.main, $('.main'));
            }
            else {
                application.functions.ui.transition(response.data.dom.main, $('.main'),response.status.code);
                $.each($('.main .errorlist'), function () {     
                $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                });   
            }            
            switch($('#id_type').val()){
                case '0': $(this)[0].mode = 'htmlmixed';
                break;
                case '1': $(this)[0].mode = 'css';
                break;
                case '2': $(this)[0].mode = 'javascript';
                break;
            }   
            canvas_preview = $('#entity-'+uuid).get(0);
        return {editor_element:'#entity-editor'}
        }
    }); 
}

function apply_tabs(){
    tabs = $('#pages-tabs').tabs({
        select: function(event, ui) {
            selected_tab = ui.index;
        },
    });
    if(tabs !== undefined) {
        tabs.tabs('option', 'selected',selected_tab);
    }
}
    
    
function bind_functions(){
    application.functions.pages = {
        route: function(uri, push_history) {
            if(urls == undefined) {
                urls = [
                    [XRegExp('^/pages/$'),this.view_pages],
                    [XRegExp('^/pages/anchors/new/$'), this.create_anchor],            
                    [XRegExp('^/pages/anchors/(?<uuid>[^/]+)/edit/$'), this.edit_anchor],
                    [XRegExp('^/pages/entities/(?<uuid>[^/]+)/new/$'), this.create_entity],
                    [XRegExp('^/pages/entities/(?<uuid>[^/]+)/edit/$'), this.edit_entity],
                ];
            }
            application.route_uri_to_mod_function(uri, urls, push_history);
        },
        
        view_pages: function(kwargs, update) {
            if(update === undefined){
                application.ws.remote('/pages/',{},function(response){
                    application.functions.ui.transition(response.data.dom.main, $('.main'));
                    apply_tabs();
                });
            }
            else {
                console.log('update');
                application.functions.ui.transition(kwargs.data.dom.main, $('.main'));
                apply_tabs();
            }
        },

        create_anchor: function() {
            application.ws.remote('/pages/anchors/new/',{},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
            });

        },
        save_create_anchor: function(kwargs) {
            var form = $("form:visible").serializeObject();
            application.ws.remote('/pages/anchors/new/',{form:form},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'), response.status.code);
                tabs = $('#pages-tabs').tabs();
            });
        },

        edit_anchor: function(kwargs) {
            application.ws.remote('/pages/anchors/'+kwargs.uuid+'/edit/',{},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
            });
        },
        save_edit_anchor: function(kwargs) {
            var form = $("form:visible").serializeObject();
            application.ws.remote('/pages/anchors/'+kwargs.uuid+'/edit/',{form:form},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'), response.status.code);
                tabs = $('#pages-tabs').tabs();
            });
        },
        
        delete_anchors: function() {
            application.ws.remote('/data/pages/anchors/delete/',{},function(response){
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function(){
                    $(this).dialog('close');
                }
                i18nButtons[gettext('Delete')] = function(){
                    var params = $(".datatable :checkbox:checked:visible").serializeObject();
                    application.ws.remote('/data/pages/anchors/delete/',{params:params},function(response){
                        application.functions.ui.transition(response.data.dom.main, $('.main'));                        
                        $tabs = $('#pages-tabs').tabs();
                    });
                    $(this).dialog('close'); 
                }
                
                $deletePlasmoid = $(response.data.dom.dialog).dialog({
                resizable: false,width:300, modal: true,
                title: '<span class="ui-icon ui-icon-arrow-4-diag"></span><span>'+gettext('Please confirm')+'...</span>',
                    open: function(event, ui) {
                    $('.confirm-list').html(get_cb_names());     
                    },
                    buttons: i18nButtons
                });
            });        
        },

        create_entity: function(kwargs) {            
            initEditor(kwargs.uuid,undefined,'/pages/entities/'+kwargs.uuid+'/create/');            
        },
        save_create_entity: function(kwargs) {
            var form_data = $("form:visible").serializeObject();
            form_data.content = editor._state.buffer.toString();
            application.ws.remote('/pages/entities/'+kwargs.uuid+'/create/',{form:form_data},function(response){
                switch(response.status.code) {
                    case "ENTITY_CREATE_OK":
                        application.functions.pages.view_pages(response, true);
                    break;
                    case "FORM_INVALID":
                        console.log('invalid form!');
                        initEditor(kwargs.uuid, response);
                    break;
                }
            });
        },

        edit_entity: function(kwargs) {
            initEditor(kwargs.uuid,undefined,'/pages/entities/'+kwargs.uuid+'/edit/');
        },
        save_edit_entity: function(kwargs) {
            console.log(kwargs);
            var form_data = $("form:visible").serializeObject();
            form_data.content = editor._state.buffer.toString();
            application.ws.remote('/pages/entities/'+kwargs.uuid+'/edit/',{form:form_data},function(response){
                switch(response.status.code) {
                    case "ENTITY_EDIT_OK":
                        application.functions.pages.view_pages(response, true);
                    break;
                    case "ENTITY_EDIT_NO_CHANGE":
                        application.functions.pages.view_pages(response, true);
                    break;
                    case "FORM_INVALID":
                        console.log('invalid form!');
                        initEditor(kwargs.uuid, response);
                    break;
                }
            });
        },
        
        delete_entities: function() {
            application.ws.remote('/data/pages/entities/delete/',{},function(response){
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function(){
                    $(this).dialog('close');
                }
                i18nButtons[gettext('Delete')] = function(){
                    var params = $(".datatable :checkbox:checked:visible").serializeObject();
                    application.ws.remote('/data/pages/entities/delete/',{params:params},function(response){
                        application.functions.pages.view_pages(response, true);
                    });
                    $(this).dialog('close');
                }

                $deletePlasmoid = $(response.data.dom.dialog).dialog({
                resizable: false,width:300, modal: true,
                title: '<span class="ui-icon ui-icon-arrow-4-diag"></span><span>'+gettext('Please confirm')+'...</span>',
                    open: function(event, ui) {
                    $('.confirm-list').html(get_cb_names());
                    },
                    buttons: i18nButtons
                });
            });
        },               

    }    
}

function bind_ws(){
    application.ws.method('^/data/pages/entities/(?<uuid>[^/]+)/online/update/$', function(params){
        editor.update_online(params.online);
    });

    application.ws.method('^/pages/entities/modified/$', function(kwargs){
        application.functions.pages.view_pages(kwargs, true);
    });
}
    
    
function bind_events() {
    function try_run_plasmoid(){
        try {
            eval(editor._state.buffer.toString());
        }
        catch (error){
            console.log(error);
        }
    }

    $('#id_type').die().live('change', function(){
        var _val = $(this).val();
        switch($(this).val()){
            case '0': editor.change_mode('htmlmixed');
            break;
            case '1': editor.change_mode('css');
            break;
            case '2': editor.change_mode('javascript');
            break;
        }
    });
    
    //FIXME: Buggy preview mode doesn't work properly without processing.js yet
    $('#id_auto_preview').live("click",function() {
        if($(this).attr('checked') == 'checked') {
            if ($('#id_type').val() == 1) {
                try_run_plasmoid();
                    $(document).unbind('infinote_update').bind('infinote_update', function(e) {
                        delete application.plasmoids[$('#uuid').val()];
                        $('.plasmoid-preview').empty();
                        try_run_plasmoid();
                    });
                }
            }
        else {
            $(document).unbind('infinote_update');
            delete application.plasmoids[$('#uuid').val()];
            $('.plasmoid-preview').empty();
        }
    });

    $(document).bind('infinote_synced', function(e, log_length, state_buffer, text_element) {
        if(editor !== undefined){

        }
    });
}

    
function unbind_events() {
    $(document).unbind('infinote_update');
    $('#id_auto_preview').die();
    $('#id_type').die();
}
    
return {
    init:function(uri, push_history){ 
        bind_functions();
        bind_ws();
        bind_events();
        application.functions.pages.route(uri, push_history);
        return 'pages';
    },
    load:function(uri, push_history){
        bind_events();
        application.functions.pages.route(uri, push_history);
    },
    clean_up: function() {
        unbind_events();
    }
}

});