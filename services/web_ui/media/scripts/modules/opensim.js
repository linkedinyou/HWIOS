/*# -*- coding: utf-8 -*-
"""
    scripts.modules.opensim
    ~~~~~~~~~~~~~~~~~~~~~~~

    Opensim module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
*/
define('modules/opensim',[
'lib/jquery/jquery.xhr_upload',
],
function(xhr){
    var urls;
    var selected_tab;
    var tabs;
    
    
function get_cb_names() {
    var names = '<ul>';
        $.each($(':checkbox:checked:visible'), function(n, val) {
        names = names + "<li>"  + $(this).parent().next().text() +"</li>";
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

    
function bind_functions() {    
    application.functions.opensim = {
        route: function(uri, push_history) {
            if(urls == undefined) {
                urls = [
                    [XRegExp('^/opensim/settings/$'), this.view_settings],
                    [XRegExp('^/opensim/avatars/$'), this.view_avatars],            
                    [XRegExp('^/opensim/maps/$'), this.view_maps],
                    [XRegExp('^/opensim/regions/$'), this.view_regions],
                    [XRegExp('^/opensim/regions/create/$'), this.create_region],
                    [XRegExp('^/opensim/regions/(?<uuid>[^/]+)/edit/$'), this.edit_region],
                    [XRegExp('^/opensim/regions/scenes/upload/$'), this.upload_scenes],
                    [XRegExp('^/opensim/avatars/luggage/upload/$'), this.upload_luggage],                
                ];
            }
            application.route_uri_to_mod_function(uri, urls, push_history);
        },
        
        view_regions: function(kwargs, update) {
            if(update == undefined){
                application.ws.remote('/opensim/regions/',{},function(response){
                    application.functions.ui.transition(response.data.dom.main, $('.main'));                    
                    tabs = $('#region-tabs').tabs();
                    tabs.tabs('option', 'selected',selected_tab);
                });
            }
            else {
                application.functions.ui.transition(kwargs.data.dom.main, $('.main'));                
                tabs = $('#region-tabs').tabs();
                tabs.tabs('option', 'selected',selected_tab);
            }
        },        
        
        view_avatars: function(kwargs, update) {
            if(update == undefined){
                application.ws.remote('/opensim/avatars/',{},function(response){
                    application.functions.ui.transition(response.data.dom.main, $('.main'));                    
                    tabs = $('#avatar-tabs').tabs();
                    tabs.tabs('option', 'selected',selected_tab);
                });
            }
            else {
                application.functions.ui.transition(kwargs.data.dom.main, $('.main'));                
                tabs = $('#avatar-tabs').tabs();
                tabs.tabs('option', 'selected',selected_tab);
            }
        },
        
        view_settings: function(kwargs, update){
            if(update == undefined){
                application.ws.remote('/opensim/settings/',{},function(response){
                    application.functions.ui.transition(response.data.dom.main, $('.main'));
                    tabs = $('#settings_tabs').tabs({show:
                        function(event, ui) {
                            if(ui.index == 1) {
                                application.maps.connect();
                            }
                        }
                    });
                });
            }
            else {
                application.functions.ui.transition(kwargs.data.dom.main, $('.main'));
                    tabs = $('#settings_tabs').tabs({show:
                        function(event, ui) {
                            if(ui.index == 1) {
                                application.maps.connect();
                            }
                        }
                    });
            }
        },
        
        view_maps: function(){
            application.ws.remote('/maps/',{},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                application.maps.connect();
            });          
        },

        sync_avatars: function() {
            application.ws.remote('/data/opensim/avatars/sync/',{},function(response){
            application.functions.ui.transition(response.data.dom.main, $('.main'));
            tabs = $('#avatar-tabs').tabs();
            $('.main').fadeIn();
            });
        },
        
        upload_luggage: function() {
            if(tabs != undefined) {selected_tab = tabs.tabs('option', 'selected');}
            application.ws.remote('/opensim/avatars/luggage/upload/',{},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                $('#id_scene').xhr_upload({
                    url:'/data/opensim/avatars/luggage/upload/',
                    submit:'#upload-start-button',
                    cancel:'#upload-cancel-button',
                    formats:['.iar'],
                    select_box:'#upload-selected',
                    progress:'#upload-status',
                });
            });
        },
        
        start_upload_luggage: function() {
            $('#id_scene').xhr_upload('send',function(response){
                if(typeof $('#upload-start-button').val() !== 'undefined') {
                    application.functions.ui.transition(response.data.dom.main, $('.main'));                    
                    tabs = $('#avatar-tabs').tabs();
                    tabs.tabs('option', 'selected',selected_tab);
                }
                $("#notify-container").notify("create",application.ws.tt[response.status.type], {i18n: response.status.i18n});
            });
        },
        
        delete_luggage: function(luggage) {
            selected_tab = tabs.tabs('option', 'selected');
            application.ws.remote('/data/opensim/avatars/luggage/delete/',{},function(response){
                $deleteLuggage = $(response.data.dom.dialog).dialog({
                resizable: false,width:300, modal: true,title: gettext("Please confirm")+"...",zIndex:1000000,
                    open: function(event, ui) {
                    $('.confirm-list').html(get_cb_names());     
                    },
                    buttons: {
                        Cancel: function() {
                            $(this).dialog('close');
                        },
                        Delete: function() {
                            var form_data = $(":checkbox:checked:visible").serializeObject();
                            application.ws.remote('/data/opensim/avatars/luggage/delete/',{params: form_data},function(response){
                                application.cb_selected = 0;
                                application.functions.ui.transition(response.data.dom.main, $('.main'));
                                $deleteLuggage.dialog('destroy');                                
                                tabs = $('#avatar-tabs').tabs();
                                tabs.tabs('option', 'selected',selected_tab);
                            });
                        }
                    }
                });
            });
        },
        
        load_luggage: function(kwargs) {
            var selected_tab = tabs.tabs('option', 'selected');
            application.ws.remote('/data/opensim/avatars/luggage/'+kwargs.name+'/load/',{},function(response){
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function(){
                    $(this).dialog('close');
                };
                i18nButtons[gettext('Load')] = function(){
                    var form_data = $("form:visible").serializeObject();
                    application.ws.remote('/data/opensim/avatars/luggage/'+kwargs.name+'/load/',{params:form_data},function(response){
                        if (response.status.code == 'FORM_INVALID') {
                            $('.dialog-luggage-load .ui-dialog-content').html(response.dom.dialog);
                            $.each($('.dialog-luggage-load .ui-dialog-content .errorlist'), function () {
                            $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                            });
                        }
                        else {
                            $chooseLuggageDialog.dialog('destroy');
                            this.view_avatars();
                        }
                    }); 
                };                
                $chooseLuggageDialog = $(response.data.dom.dialog).dialog({
                    resizable: false,width:600,height:550,modal: true,title: gettext("Load luggage file")+" "+kwargs.name+"...",
                    "dialogClass":'dialog-luggage-load',buttons: i18nButtons,zIndex:1000000
                });
            });
        },
        
        download_luggage: function(kwargs) {
            window.open("/dav/iar/"+kwargs.name,"Download IAR");
        },
        
        backup_luggage: function(kwargs) {
            application.ws.remote('/data/opensim/avatars/luggage/'+kwargs.uuid+'/backup/',{},function(response){
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function(){
                    $(this).dialog('close');
                }
                i18nButtons[gettext('Save')] = function(){
                    var form_data = $("form:visible").serializeObject();
                    form_data['profile_uuid'] = kwargs.uuid;
                    application.ws.remote('/data/opensim/luggage/'+kwargs.uuid+'/backup/',{params:form_data},function(response){
                        if (response.status.code != 'FORM_INVALID') {
                            var selected_tab = tabs.tabs('option', 'selected');
                            $backupLuggageDialog.dialog('destroy');
                            application.functions.profiles.view_profiles(response);
                        }
                        else {
                            $('.dialog-luggage-backup .ui-dialog-content').html(response.data.dom.dialog);
                            $.each($('.dialog-luggage-backup .ui-dialog-content .errorlist'), function () {
                            $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                            });
                        }
                    }); 
                }
                $backupLuggageDialog = $(response.data.dom.dialog).dialog({
                    bgiframe: true,resizable: false,width:630,height:550,modal: true,
                    title: gettext("Save luggage as")+"...",'dialogClass':'dialog-luggage-backup',
                    buttons: i18nButtons, zIndex:1000000
                });
            });
        },
        
        delete_regions: function() {
            var regions = '<ul>';
                $.each($(':checkbox:checked'), function(n, val) {
                regions = regions + "<li>" + $(this).parent().next().text() +"</li>";
                });
            regions += '</ul>';        
            application.ws.remote('/data/opensim/regions/delete/',{},function(response){
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function(){
                    $(this).dialog('close');
                }
                i18nButtons[gettext('Delete')] = function(){
                    var form_data = $(":checkbox:checked:visible").serializeObject();
                    application.ws.remote('/data/opensim/regions/delete/',{params:form_data},function(response){
                        application.maps.reset_cache();
                        application.cb_selected = 0;
                        application.functions.ui.transition(response.data.dom.main, $('.main'));                        
                        tabs = $('#region-tabs').tabs();
                    });
                    $(this).dialog('close'); 
                }
                
                $deleteRegion = $(response.data.dom.dialog).dialog({
                resizable: false,width:300, modal: true,
                title: '<span class="ui-icon ui-icon-arrow-4-diag"></span><span>'+gettext('Please confirm')+'...</span>',
                    open: function(event, ui) {
                    $('.confirm-list').html(get_cb_names());     
                    },
                    buttons: i18nButtons, zIndex:1000000
                });
            });        
        },
        
        create_region: function(kwargs) {
                if(tabs != undefined) {
                selected_tab = tabs.tabs('option', 'selected');
                }
            application.ws.remote('/opensim/regions/create/',{},function(response){
            application.functions.ui.transition(response.data.dom.main, $('.main'));
            application.maps.connect(application);
            });
        },
        
        cancel_create_region: function() {
            this.view_regions();            
        },
        
        save_create_region: function() {
            var selected_tab = 0;
            var form_data = $('form:visible').serializeObject();
            application.ws.remote('/opensim/regions/create/',{params:form_data},function(response){
                switch(response.status.code) {
                    case 'FORM_INVALID':  
                        $('.main').html(response.data.dom.main);
                        application.maps.connect(application);
                        
                        $.each($('form .errorlist'), function () {
                        $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');   
                        });     
                    break;
                    case 'REGION_CREATED':
                        application.maps.reset_cache();
                        application.functions.opensim.view_regions();
                    break;
                }
            });
        },
        
        edit_region: function(kwargs) {
            application.ws.remote('/opensim/regions/'+kwargs.uuid+'/edit/',{},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                application.maps.reset_cache();
                application.maps.connect(application);                
                init_helpers();
            });
        },
        
        cancel_edit_region: function() {
            application.functions.opensim.view_regions();        
        },
        
        save_edit_region: function(kwargs) {
            var form_data = $('form:visible').serializeObject();
            application.ws.remote('/opensim/regions/'+kwargs.uuid+'/edit/',{params:form_data},function(response){
                if (response.status.code == 'REGION_UPDATED') {
                    application.maps.reset_cache();
                    application.functions.opensim.view_regions();
                }
                else {
                $('.regioneditorform').html(response.dom.main);
                init_helpers();
                    $.each($('form .errorlist'), function () {
                    $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');   
                    });
                }
            });
        },
        
        backup_region: function(kwargs) {
                application.ws.remote('/data/opensim/regions/'+kwargs.uuid+'/backup/',{},function(response){
                i18nButtons = {};
                i18nButtons[gettext('Cancel')] = function() {
                    $(this).dialog('close');
                }
                i18nButtons[gettext('Save')] = function() {
                    var form_data = $('form:visible').serializeObject();
                    application.ws.remote('/data/opensim/regions/'+kwargs.uuid+'/backup/',{params:form_data},function(response){
                        var selected_tab = tabs.tabs('option', 'selected');
                        application.cb_selected = 0;
                        application.functions.ui.transition(response.data.dom.main, $('.main'));
                        tabs = $('#region-tabs').tabs();
                        tabs.tabs('option', 'selected',selected_tab);
                    });
                $(this).dialog('close');
                }
                $backupRegion = $(response.data.dom.dialog).dialog({
                bgiframe: true,resizable: false,width:470,height:185,modal: true,title: gettext('Save scene as')+'...',
                    buttons: i18nButtons,zIndex:1000000
                });
            });
        },
        
        delete_scenes: function() {
            var selected_tab = tabs.tabs('option', 'selected');
            application.ws.remote('/data/opensim/regions/scenes/delete/',{},function(response){
                i18nButtons = {};
                i18nButtons[gettext('Cancel')] = function() {
                    $(this).dialog('close');
                }
                i18nButtons[gettext('Delete')] = function() {
                    var data = $(":checkbox:checked:visible").serializeObject();
                    application.ws.remote('/data/opensim/regions/scenes/delete/',{params:data},function(response){
                        application.cb_selected = 0;
                        application.functions.ui.transition(response.data.dom.main, $('.main'));                        
                        tabs = $('#region-tabs').tabs();
                        tabs.tabs('option', 'selected',selected_tab);
                    });
                $(this).dialog('close');
                }
                $deleteScene = $(response.data.dom.dialog).dialog({
                resizable: false,width:380, modal: true,
                title: '<span class="ui-icon ui-icon-arrow-4-diag"></span><span>'+gettext('Please confirm')+'...</span>',
                    open: function(event, ui) {
                    $('.confirm-list').html(get_cb_names());     
                    },
                    buttons: i18nButtons,zIndex:1000000
                });
            });
        },
        
        load_scene: function(kwargs) {
            var selected_tab = tabs.tabs('option', 'selected');
            application.ws.remote('/data/opensim/regions/scenes/'+kwargs.name+'/load/',{},function(response){
                i18nButtons = {};
                i18nButtons[gettext('Cancel')] = function() {
                    $(this).dialog('close');
                }
                i18nButtons[gettext('Load')] = function() {
                    var form_data = $("form:visible").serializeObject();
                    application.ws.remote('/data/opensim/regions/scenes/'+kwargs.name+'/load/',{params:form_data},function(response){
                        application.cb_selected = 0;
                        application.functions.ui.transition(response.data.dom.main, $('.main'));                        
                        tabs = $('#region-tabs').tabs();
                        tabs.tabs('option', 'selected',selected_tab);
                    });
                $(this).dialog('close'); 
                }
                $chooseRegionDialog = $(response.data.dom.dialog).dialog({bgiframe: true,resizable: false,width:470,
                    modal: true,title: gettext('Load scene')+' '+kwargs.name+'...', buttons: i18nButtons, zIndex:1000000
                });
            });
        },
        
        cancel_scenes_upload: function() {
            this.view_regions();            
        },
        
        upload_scenes: function() {
            if(tabs != undefined) {
                selected_tab = tabs.tabs('option', 'selected');
            }
            application.ws.remote('/opensim/regions/scenes/upload/',{},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                $('#id_scene').xhr_upload({
                    url:'/data/opensim/regions/scenes/upload/',
                    submit:'#upload-start-button',
                    cancel:'#upload-cancel-button',
                    formats:['.oar'],
                    select_box:'#upload-selected',
                    progress:'#upload-status',
                });
            });
        },
        
        start_upload_scenes: function() {
            $('#id_scene').xhr_upload('send',function(response){
                if(typeof $('#upload-start-button').val() !== 'undefined') {                    
                    application.functions.ui.transition(response.data.dom.main, $('.main'));                    
                    tabs = $('#region-tabs').tabs();
                    tabs.tabs('option', 'selected',selected_tab);
                }
                $("#notify-container").notify("create",application.ws.tt[response.status.type], {i18n: response.status.i18n});
            });
        },
        
        download_scene: function(kwargs) {
            window.open("/dav/oar/"+kwargs.name,"Download OAR");
        },
        
        update_map_settings: function () {
            var form_data = $("form:visible").serializeObject();
            var selected = tabs.tabs('option', 'selected');
            application.ws.remote('/data/settings/maps/update/',{params:form_data},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                application.maps.connect(application);
                tabs = $('#settings_tabs').tabs();
                tabs.tabs('option', 'selected',selected);
                //$('#id_mail_body').markItUp(mySettings,{multiUser:false});
                switch(response.status.code) {
                    case 'FORM_INVALID': 
                    $.each($('.errorlist'), function () {
                    $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');   
                    });
                    break;
                }
            });
        },
        render_maps: function() {
            application.ws.remote('/data/opensim/maps/render/',{},function(response){
            });
        },
        
        update_settings: function() {
            var form_data = $("form:visible").serializeObject();
            var selected = tabs.tabs('option', 'selected');
            application.ws.remote('/opensim/settings/',{params:form_data},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                tabs = $('#settings_tabs').tabs({show:
                    function(event, ui) {
                        if(ui.index == 1) {application.maps.connect();}
                    }
                });   
                tabs.tabs('option', 'selected',selected);
                
                switch(response.status.code) {
                    case "SETTINGS_UPDATE_OK":
                    break;
                    case "INVALID_FORM":
                        $('.errorlist').each(function() { 
                        $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                        });
                    break;
                }
            });
        }
    }
}

function bind_ws(){
    application.ws.method('^/opensim/settings/modified/$', function(kwargs){
        application.functions.opensim.view_settings(kwargs, true);
    });
    application.ws.method('^/opensim/avatars/modified/$', function(kwargs){
        application.functions.opensim.view_avatars(kwargs, true);
    });
    application.ws.method('^/opensim/regions/modified/$', function(kwargs){
        application.functions.opensim.view_regions(kwargs, true);
    });
    
}
    
function bind_events() {     
    $(document).bind('MAP_FREE_LOCATION', function(e,x,y) {
        $('input').each(function(index) {
            if($(this).attr('id') == 'id_sim_location_x'){
            $(this).val(x);
            }
            else if($(this).attr('id') == 'id_sim_location_y'){
            $(this).val(y);
            }
        });
    });
}


function unbind_events(){
    $(document).unbind('MAP_FREE_LOCATION');
}

    
    
return {
    init:function(uri, push_history){ 
        bind_functions();
        bind_events();
        bind_ws();
        application.functions.opensim.route(uri, push_history);
        return 'opensim';
    },
    load:function(uri, push_history){
        bind_events();
        application.functions.opensim.route(uri, push_history);
    },
    clean_up: function() {
        unbind_events();
    }
}
});