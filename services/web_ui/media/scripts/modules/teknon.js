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

require.def('modules/teknon',[
'lib/jquery/jquery.atools'
],
function(backend_ui){
    var c_dialog = {};
    var offset_history = new Array();  
    var urls;
    var tabs;
    
    function get_cb_names(names) {        
        var items = '<ul>';
        if(names == undefined) {
            $.each($(':checkbox:checked:visible'), function(n, val) {
            items = items + "<li>" + $(this).parent().next().text() +"</li>";
            });
        }
        else {
            $.each(names, function(idx, value) {
            items = items + "<li>" + value +"</li>";
            });
        }
        items += '</ul>'; 
        return items;
    }    
    
    
function bind_ws() { 

    application.ws.method('^/data/teknon/services/state/update/$',function(params){
        $(document).trigger('SERVICE_CHANGED_STATE',[params.services]);
        if(typeof $('#teknon-services').val() !== 'undefined') {
            $.each(params.services, function(i, service) {
            var watchdog_status = $('#watchdog-status-'+service.uuid)[0];
            var service_status = $('#service-status-'+service.uuid)[0];
            var console_status = $('#console-status-'+service.uuid)[0];
                if(service.watchdog == 'OFF') {
                $(watchdog_status).removeClass('watchdog-on');
                $(watchdog_status).addClass('watchdog-off');
                $.data(watchdog_status, 'state', 'ON');
                }
                else {
                $(watchdog_status).removeClass('watchdog-off');
                $(watchdog_status).addClass('watchdog-on');
                $.data(watchdog_status, 'state', 'OFF');
                }
                if (service.status == 'OFF') {
                //$('button[value=someValue]')
                $(service_status).removeClass('service-on');
                $(service_status).addClass('service-off');
                $(watchdog_status).addClass('action-icon-disabled');
                $(console_status).addClass('action-icon-disabled');
                $.data(service_status, 'function', 'teknon.start_services');
                }
                else {
                $(service_status).removeClass('service-off');
                $(service_status).addClass('service-on');
                $(watchdog_status).removeClass('action-icon-disabled');
                $(console_status).removeClass('action-icon-disabled');
                $.data(service_status, 'function', 'teknon.stop_services');
                }
            });
        }
    });

    application.ws.method('^/data/teknon/$',function(params){
        application.functions.ui.transition(params.data.dom.main, $('.main'));        
        $('#teknon-tabs').tabs();
    });
        
    application.ws.method('^/data/teknon/services/(?<service_uuid>[^/]+)/console/update/$',function(params){
        filter_html = $('<div/>').text(params.output).html();
        filter_lb = filter_html.replace(/\t/g,'&#09;').replace(/\r\n/g,'<br/>').replace(/\r/g,'<br/>').replace(/\n/g,'<br/>')+'<br/>';
        
        $('#console-lines-'+params.service_uuid).append(filter_lb+'<br/>');
        $('.console-box').scrollTop($('.console-box > #console-lines-'+params.service_uuid).outerHeight()+10000000);
    });
}
    
function bind_functions() {    
    application.functions.teknon = {
        route: function(uri, push_history) {
            if(urls == undefined) {
                urls = [
                    [XRegExp('^/teknon/$'),application.functions.teknon.view_services],
                ];
            }
            application.route_uri_to_mod_function(uri, urls, push_history);
        },
        
        view_services: function(kwargs) {        
            application.ws.remote('/teknon/',{},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));                
                $('#teknon-tabs').tabs();
            });
        },
        
        switch_watchdog: function(kwargs) {
            application.ws.remote('/data/teknon/services/watchdog/switch/',{services:[kwargs.uuid],status:kwargs.state},function(response){
            });
        },
        /**
        * Console UI handler
        * param: service UUID
        */
        open_console: function(kwargs) {
            var offset = 0;
                //existing dialog
                if (typeof c_dialog[kwargs.uuid] != 'undefined') {
                    //if existing dialog is not open, check gaps or add to the end of the offset list
                    if (!c_dialog[kwargs.uuid].dialog('isOpen')) {              
                        if (offset_history.length > 0) {
                        offset_history.sort(function(a,b){return a - b});
                        offset = offset_history.shift();
                        }
                        else {
                            offset = 0;
                            $.each(c_dialog, function(i, dialog) {
                                if (dialog.dialog('isOpen')) {
                                offset +=35;
                                }
                            });
                        }
                    }
                    //existing dialog is already open. Keep current position
                    else {offset = c_dialog[kwargs.uuid].dialog( "option" , 'position')[0];}
                }
                else {
                    $.each(c_dialog, function(i, dialog) {
                        if (dialog.dialog('isOpen')) {
                        offset +=33;
                        }
                    });
                }
            if (typeof c_dialog[kwargs.uuid] == 'undefined') {
                c_dialog[kwargs.uuid] = $('<div class="console-container"><div id="console-box'+kwargs.uuid+'" class="console-box"><div id="console-lines-'+
                kwargs.uuid+'" class="console-lines"></div></div><input type="text" id="console-input-'+kwargs.uuid+'" class="console-input"></input></div>').dialog({
                    dialogClass: 'console-dialog-container', autoOpen: false, resizable: false,
                    title: '<span class="ui-icon ui-icon-image"></span><span>Console '+kwargs.name+'</span>',height:446,width:802,position:[offset,offset],zIndex:10000,
                    open:function(event, ui) {
                        c_dialog[kwargs.uuid].c_hist = new Array();
                        $('#console-input-'+kwargs.uuid).removeAttr("disabled");
                        $('.console-box').removeClass('console-box-disabled');
                        c_dialog[kwargs.uuid].c_hist_index = 0;
                        application.ws.remote('/data/teknon/services/subscribe_console/',{services:[kwargs.uuid]},function(response){
                            $('#console-lines-'+kwargs.uuid).append('<div class="console-notification">Console \''+response.data.service.name+'@'+response.data.client+'\' '+gettext('connected')+'...</div>');
                            $('.console-box').scrollTop($('.console-box > #console-lines-'+kwargs.uuid).outerHeight()+10000000);
                            $('#console-input-'+kwargs.uuid).focus();
                            $(document).bind('SERVICE_CHANGED_STATE', function(e,services) {
                                $.each(services, function(i, service) {
                                    if(service.uuid == kwargs.uuid) {
                                        if (service.status == "OFF") {
                                        $('#console-input-'+kwargs.uuid).attr("disabled","disabled");
                                        $('.console-box').addClass('console-box-disabled');
                                        }
                                        else if (service.status == "ON") {
                                        $('#console-input-'+kwargs.uuid).removeAttr("disabled");
                                        $('.console-box').removeClass('console-box-disabled');
                                        }
                                    }
                                });
                            });
                            $('#console-input-'+kwargs.uuid).keyup(function(e){
                                switch (e.which) {
                                    case 13:
                                    var command = $('#console-input-'+kwargs.uuid).val();
                                        if(command !='') {
                                            if (command == 'clear') {$('#console-lines-'+kwargs.uuid).html('');}
                                            else {
                                            application.ws.remote('/data/teknon/services/'+kwargs.uuid+'/send_command/',{'command':command},function(response){});
                                            }
                                        c_dialog[kwargs.uuid].c_hist.push(command);
                                        }
                                    $('#console-input-'+kwargs.uuid).val('');
                                    c_dialog[kwargs.uuid].c_hist_index = 0;
                                    break;
                                    case 38:
                                        if (c_dialog[kwargs.uuid].c_hist_index >= c_dialog[kwargs.uuid].c_hist.length) {c_dialog[kwargs.uuid].c_hist_index = 0;}
                                        if (typeof c_dialog[kwargs.uuid].c_hist[(c_dialog[kwargs.uuid].c_hist.length) - c_dialog[kwargs.uuid].c_hist_index -1] !== 'undefined') {
                                        $('#console-input-'+kwargs.uuid).val(c_dialog[kwargs.uuid].c_hist[(c_dialog[kwargs.uuid].c_hist.length-1) - c_dialog[kwargs.uuid].c_hist_index]);                               
                                        }
                                        c_dialog[kwargs.uuid].c_hist_index+=1;
                                        var textobj = $('#console-input-'+kwargs.uuid).getSelection();
                                        $('#console-input-'+kwargs.uuid).setCaretPos(textobj.end+1);
                                    break;
                                    case 40:
                                        if (c_dialog[kwargs.uuid].c_hist_index <= 0) {c_dialog[kwargs.uuid].c_hist_index=c_dialog[kwargs.uuid].c_hist.length;}
                                        if (typeof c_dialog[kwargs.uuid].c_hist[(c_dialog[kwargs.uuid].c_hist.length) - c_dialog[kwargs.uuid].c_hist_index] !== 'undefined') {
                                        $('#console-input-'+kwargs.uuid).val(c_dialog[kwargs.uuid].c_hist[(c_dialog[kwargs.uuid].c_hist.length) - c_dialog[kwargs.uuid].c_hist_index]);
                                        }
                                        c_dialog[kwargs.uuid].c_hist_index-=1;
                                    break;
                                }
                            });
                        });
                    },
                    close:function(event, ui) {
                        offset_history.push(c_dialog[kwargs.uuid].dialog('option','position')[0]);
                        application.ws.remote('/data/teknon/services/unsubscribe_console/',{services:[kwargs.uuid]},function(response){
                        $(document).unbind('SERVICE_CHANGED_STATE');
                        $('#console-lines-'+kwargs.uuid).append('<div class="console-notification">Console \''+response.data.service.name+'@'+response.data.client+'\' '+gettext('disconnected')+'...</div>');
                        }); 
                    },
                });
            c_dialog[kwargs.uuid].dialog('open');
            }
            else {
                if (!c_dialog[kwargs.uuid].dialog('isOpen')) {  
                c_dialog[kwargs.uuid].dialog( "option" , 'position' , [offset,offset] );
                c_dialog[kwargs.uuid].dialog('open');
                }
                else {
                c_dialog[kwargs.uuid].dialog( "moveToTop" );
                }
            }
        },

        edit_sim_slave_ini: function(service) {
            var service_name = service.split('_')[0];
            var service_uuid = service.split('_')[1];
            application.ws.remote('/teknon/services/sim_slave_ini/edit/',{},function(response){
                $('.main').html(response.data.dom.main);
                $('textarea').markItUp(mySettings);
                $('.main').hide();
                $('.main').fadeIn("slow");
            });
        },
    
        cancel_edit_sim_slave_ini: function() {
            this.view_services();        
        },
        
        save_edit_sim_slave_ini: function(service) {
            var service_name = service.split('_')[0];
            var service_uuid = service.split('_')[1];
            var form_data = $('form').serializeObject();
                application.ws.remote('/teknon/services/'+kwargs.uuid+'/sim_slave_ini/save/',{data:form_data},function(response){
                $('.main').html(response.data.dom.main).hide().fadeIn();                
                $('#teknon-tabs').tabs();
                });
        },
        
        start_services: function(kwargs) {
            var _services = {};         
            var _names;
            if(!('uuid' in kwargs)) {
                _services = $(":checkbox:checked:visible").serializeObject();
                _names = get_cb_names();
            }
            else {
                _services[kwargs.uuid] = 'on'; 
                _names = get_cb_names([kwargs.name]);
            }
            application.ws.remote('/data/teknon/services/start/',{},function(response){
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function() {$(this).dialog('close');}
                i18nButtons[gettext('Start')] = function() {
                    var services = $(":checkbox:checked:visible").serializeObject();
                    application.ws.remote('/data/teknon/services/switch/',{services:_services,to_state:'on'},function(response){
                    });
                    $(this).dialog('close');  
                }
                var _dialog = $(response.data.dom.dialog).dialog({
                resizable: false,width:300, modal: true,title: '<span class="ui-icon ui-icon-gear"></span><span>'+gettext('Please confirm')+'...</span>',
                    open: function(event, ui) {$('.confirm-list').html(_names);}, 
                    buttons: i18nButtons,zIndex:1000000
                });
            });
        },
        
        stop_services: function(kwargs) {
            var _services = {};   
            var _names;
            if(!('uuid' in kwargs)) {
                _services = $(":checkbox:checked:visible").serializeObject();
                _names = get_cb_names();
            }
            else {
                _services[kwargs.uuid] = 'on'; 
                _names = get_cb_names([kwargs.name]);
            }
            application.ws.remote('/data/teknon/services/stop/',{},function(response){
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function() {$(this).dialog('close');}
                i18nButtons[gettext('Stop')] = function() {
                    var services = $(":checkbox:checked:visible").serializeObject();
                    application.ws.remote('/data/teknon/services/switch/',{services:_services,to_state:'off'},function(response){

                    });
                    $(this).dialog('close');
                }
                var _dialog = $(response.data.dom.dialog).dialog({
                resizable: false,width:300, modal: true,title: '<span class="ui-icon ui-icon-gear"></span><span>'+gettext('Please confirm')+'...</span>',
                    open: function(event, ui) {$('.confirm-list').html(_names);},
                    buttons: i18nButtons,zIndex:1000000
                });
            });
        },    

        kill_services: function(kwargs) {
            var _services = {};  
            var _names;
            if(!('uuid' in kwargs)) {
                _services = $(":checkbox:checked:visible").serializeObject();
                _names = get_cb_names();
            }
            else {
                _services[kwargs.uuid] = 'on'; 
                _names = get_cb_names([kwargs.name]);
            }
            if(!('uuid' in kwargs)) {_services = $(":checkbox:checked:visible").serializeObject();}
            else {_services[kwargs.uuid] = 'on';}
            application.ws.remote('/data/teknon/services/kill/',{},function(response){
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function() {$(this).dialog('close');}
                i18nButtons[gettext('Kill')] = function() {
                    var services = $(":checkbox:checked:visible").serializeObject();
                    application.ws.remote('/data/teknon/services/switch/',{services:_services,to_state:'kill'},function(response){

                    });
                    $(this).dialog('close');  
                }
                var _dialog = $(response.data.dom.dialog).dialog({
                resizable: false,width:300, modal: true,title: '<span class="ui-icon ui-icon-gear"></span><span>'+gettext('Please confirm')+'...</span>',
                    open: function(event, ui) {$('.confirm-list').html(_names);},
                    buttons: i18nButtons,zIndex:1000000
                });
            });
        }
    }
} 

function bind_events(){
    
    
}

function unbind_events(){
    $(document).unbind('SERVICE_CHANGED_STATE');
}
    
return {        
    init: function(uri, push_history) {
        bind_functions();
        bind_ws();
        bind_events();   
        application.functions.teknon.route(uri, push_history);
        return 'teknon';
    },
    load: function(uri, push_history) {
        bind_events();
        application.functions.teknon.route(uri, push_history);
    },
    clean_up: function() {
        unbind_events();
    }
}
});