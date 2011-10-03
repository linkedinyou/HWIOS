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

require.def('modules/plasmoids',[],
            
function(){
    var editor;
    var plasmoid_uuid;
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
    
    
function initEditor(plasmoid_uuid, override_layout) {
    editor = $.jinfinote(application.ws, {
    ws_connect:'/plasmoids/'+plasmoid_uuid+'/edit/',
    ws_disconnect:'/data/plasmoids/'+plasmoid_uuid+'/disconnect/',
    ws_insert:'/data/plasmoids/'+plasmoid_uuid+'/insert/',
    ws_delete:'/data/plasmoids/'+plasmoid_uuid+'/remove/',
    ws_undo:'/data/plasmoids/'+plasmoid_uuid+'/undo/',
    ws_caret:'/data/plasmoids/'+plasmoid_uuid+'/caret/',
    cb_insert:'^/data/plasmoids/(?<plasmoid_uuid>[^/]+)/insert/$',      
    cb_delete:'^/data/plasmoids/(?<plasmoid_uuid>[^/]+)/remove/$',
    cb_undo:'^/data/plasmoids/(?<plasmoid_uuid>[^/]+)/undo/$',
    cb_caret:'^/data/plasmoids/(?<plasmoid_uuid>[^/]+)/caret/$',   
    mode:'javascript',
    init: 
        function(data) {
            if (typeof(override_layout) == 'undefined') {
                application.functions.ui.transition(data.dom.main, $('.main'));
            }
            else {
                application.functions.ui.transition(override_layout, $('.main'));
                $.each($('.main .errorlist'), function () {     
                $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                });   
            }
            
            canvas_preview = $('#plasmoid_'+plasmoid_uuid).get(0);
        $('.infinote-editor-textarea').text(data.page.state[1]);
        return {editor_element:'#plasmoid-editor'}
        }
    }); 
}
    
    
function bind_functions(){
    application.functions.plasmoids = {
        route: function(uri, push_history) {
            if(urls == undefined) {
                urls = [
                    [XRegExp('^/plasmoids/$'),this.view_plasmoids],
                    [XRegExp('^/plasmoids/new/$'), this.create_plasmoid],
                    [XRegExp('^/plasmoids/(?<uuid>[^/]+)/edit/$'), this.edit_plasmoid],
                ];
            }
            application.route_uri_to_mod_function(uri, urls, push_history);
        },
        
        view_plasmoids: function(kwargs, update) {
            if(update == undefined){
                application.ws.remote('/plasmoids/',{},function(response){
                    application.functions.ui.transition(response.data.dom.main, $('.main'));
                });
            }
            else {
                application.functions.ui.transition(kwargs.data.dom.main, $('.main'));                
            }
            
        },
        
        delete_plasmoids: function() {        
            application.ws.remote('/data/plasmoids/delete/',{},function(response){  
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function(){
                    $(this).dialog('close');
                }
                i18nButtons[gettext('Delete')] = function(){
                    var params = $(".datatable :checkbox:checked:visible").serializeObject();
                    application.ws.remote('/data/plasmoids/delete/',{params:params},function(response){
                        application.cb_selected = 0;
                        application.functions.ui.transition(response.data.dom.main, $('.main'));
                        $('.datatable').dataTable({"bJQueryUI": true,"bAutoWidth": false,"aoColumnDefs":[{"aTargets":[0],"bSearchable":false,"bSortable": false}]});
                        $tabs = $('#simulation_tabs').tabs();
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
        
        create_plasmoid: function() {
            application.ws.remote('/plasmoids/new/',{},function(response){
                //application.functions.ui.transition(response.data.dom.main, $('.main'));
                initEditor(response.data.plasmoid.uuid, response.data.dom.main);
            });
            
        },
        
        edit_plasmoid: function(kwargs) {
            initEditor(kwargs.uuid);            
        },
        
        cancel_edit_plasmoid: function() {
            listPlasmoids();            
        },
        
        save_plasmoid: function(kwargs) {
            var form_data = $("form:visible").serializeObject();
            form_data.content = editor._state.buffer.toString();
            application.ws.remote('/data/plasmoids/'+kwargs.uuid+'/save/',{form:form_data},function(response){
                switch(response.status.code) {
                    case "PLASMOID_EDIT_OK":
                        application.functions.plasmoids.view_plasmoids();
                    break;
                    case "PLASMOID_EDIT_NO_CHANGE":
                        application.functions.plasmoids.view_plasmoids();
                    break;
                    case "FORM_INVALID":
                        initEditor(kwargs.uuid, response.data.dom.main);
                    break;
                }
            });
        }
    }    
}

function bind_ws(){
    application.ws.method('^/data/plasmoids/(?<plasmoid_uuid>[^/]+)/online/update/$', function(params){
        editor.update_online(params.online);
    });

    application.ws.method('^/plasmoids/modified/$', function(kwargs){
        application.functions.plasmoids.view_plasmoids(kwargs, true);

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
}
    
return {
    init:function(uri, push_history){ 
        bind_functions();
        bind_ws();
        bind_events();
        application.functions.plasmoids.route(uri, push_history);        
        return 'plasmoids';
    },
    load:function(uri, push_history){
        bind_events();
        application.functions.plasmoids.route(uri, push_history);
    },
    clean_up: function() {
        unbind_events();
    }
}

});