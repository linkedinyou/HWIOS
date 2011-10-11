/*# -*- coding: utf-8 -*-
"""
    scripts.modules.profiles
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Profiles module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
*/
require.def('modules/profiles',[
'lib/jquery/jquery.xhr_upload',	
],
function(){

    var profiles_context;
    var selected_tab;
    var urls;
    
function get_cb_names() {
    var names = '<ul>';
        $.each($(':checkbox:checked:visible'), function(n, val) {
        names = names + "<li>" + $(this).parent().next().text() +"</li>";
        });
    names += '</ul>'; 
    return names;
}  
    
    
function bind_functions() {    
    application.functions.profiles = {
        route: function(uri, push_history) {
            if(urls == undefined) {
                urls = [
                    [XRegExp('^/data/profiles/login/$'),this.login],
                    [XRegExp('^/data/profiles/logout/$'),this.logout],
                    [XRegExp('^/data/profiles/register/$'),this.register],
                    [XRegExp('^/profiles/activate/(?<profile_uuid>[^/]+)/$'),this.activate],
                    [XRegExp('^/profiles/manage/$'),this.manage_profiles],
                    [XRegExp('^/profiles/(?<profile_name>[^/]+)/$'),this.view_profile],                   
                    [XRegExp('^/profiles/create/$'),this.create_profile],
                    [XRegExp('^/profiles/(?<profile_name>[^/]+)/edit/$'),this.edit_profile],
                ];
            }
            application.route_uri_to_mod_function(uri, urls, push_history);
        },
        
        view_profile: function(kwargs, update) {
            if(update == undefined){
                application.ws.remote('/profiles/'+kwargs.profile_name+'/',{},function(response){
                    application.functions.ui.transition(response.data.dom.main, $('.main'));
                    var _tabs = $('#personal_tabs').tabs();
                    _tabs.tabs('option', 'selected',selected_tab);
                });
            }
            else {
                application.functions.ui.transition(kwargs.data.dom.main, $('.main'));
                var _tabs = $('#personal_tabs').tabs();
                _tabs.tabs('option', 'selected',selected_tab);
            }
        },        
        
        manage_profiles: function(kwargs, update) {
            if(update == undefined){
                application.ws.remote('/profiles/manage/',{},function(response){
                    application.functions.ui.transition(response.data.dom.main, $('.main'));                    
                    var _tabs = $('#personal_tabs').tabs();
                    _tabs.tabs('option', 'selected',selected_tab);
                });
            }
            else {
                application.functions.ui.transition(kwargs.data.dom.main, $('.main'));
                var _tabs = $('#personal_tabs').tabs();
                _tabs.tabs('option', 'selected',selected_tab);
            }
        },
        
        register: function() {
            application.ws.remote('/data/profiles/register/',{},function(response){ 
                var i18nButtons = {};
                i18nButtons[gettext('Cancel')] = function() {
                    $(this).dialog("destroy"); 
                    _dialog = undefined;
                };
                i18nButtons[gettext('Register')] = function() {
                    //Make our dialog read-only while processing is going on
                    $(".ui-dialog-buttonpane").find("button").hide();
                    $(_dialog).find("input").attr('readonly',true);
                    _dialog.dialog('option', 'title', '<span class="ui-icon ui-icon-person"></span><span>'+gettext('Registration pending')+'</span>');
                    var form_data = $("form:visible").serializeObject();
                    application.ws.remote('/data/profiles/register/',{params:form_data},function(response){ 
                        switch(response.status.code) {
                            case 'REGISTER_OK':
                            $('.registerDialog > .ui-dialog-content').html(response.data.dom.dialog);
                            _dialog.dialog('option', 'title', '<span class="ui-icon ui-icon-person"></span><span>'+gettext('Registration completed')+'</span>');
                                var i18nButtons = {};
                                i18nButtons[gettext('Close')] = function() {
                                    $(this).dialog("destroy");
                                    _dialog = undefined;
                                }
                                _dialog.dialog('option', 'buttons', i18nButtons);
                            break;
                            case 'FORM_INVALID':
                                //undo our pending changes to the dialog
                                $(".ui-dialog-buttonpane").find("button").show();
                                $(_dialog).find("input").attr('readonly',false);
                                _dialog.dialog('option', 'title', '<span class="ui-icon ui-icon-person"></span><span>'+gettext('Register')+'</span>');
                                
                                $('.registerDialog > .ui-dialog-content').html(response.data.dom.dialog);
                                $.each($('.registerDialog .errorlist'), function () {
                                $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                                })      
                            break;
                            default:
                        }
                    });
                }
                var _dialog = $(response.data.dom.dialog).dialog({
                    dialogClass: 'registerDialog',autoOpen: true,position:"center",width:450,
                    title: '<span class="ui-icon ui-icon-pencil"></span><span>'+gettext('Register')+'</span>',
                    resizable: false,draggable: true,modal: true, buttons: i18nButtons,
                    open: function(event, ui) {
                    // Get the dialog
                        var dialog = $(event.target).parents(".ui-dialog.ui-widget");
                        var buttons = dialog.find(".ui-dialog-buttonpane").find("button");
                        var cancelButton = buttons[0];
                        var registerButton = buttons[1];
                        // Add class to the buttons
                        // Add class to the buttons
                        $(cancelButton).addClass("dialog-button");
                        $(registerButton).addClass("dialog-button");
                    } 
                });
            },"html");
        },

        activate: function(kwargs) {
            application.ws.remote('/profiles/activate/'+kwargs.profile_uuid+'/',{},function(response){
                switch(response.status.code) {
                    case 'PROFILE_ACTIVATED':
                        var i18nButtons = {};
                        i18nButtons[gettext('Ok')] = function() {
                            $(this).dialog("destroy");
                            $register = undefined;
                            application.route_uri_to_mod('/', true);
                        };
                        var _dialog = $(response.data.dom.dialog).dialog({
                            dialogClass: 'activateDialog',autoOpen: true,position:"center",width:450,
                            title: '<span class="ui-icon ui-icon-person"></span><span>'+gettext('Your account has been activated!')+'</span>',
                            resizable: false,draggable: true,modal: true, buttons: i18nButtons, zIndex:1000000,
                            close:function(){
                                application.route_uri_to_mod('/', true);
                            },
                        });
                        break;
                    case 'PROFILE_ALREADY_ACTIVATED':
                        application.route_uri_to_mod('/', true);
                    break;
                }
            });
            
        },
        
        login: function(){
            application.ws.remote('/data/profiles/login/',{},function(response){
                var i18nButtons = {};
                i18nButtons[gettext('Cancel')] = function(){
                    $(this).dialog("close"); 
                };
                i18nButtons[gettext('Login')] = function(){
                    var str = $("form:visible").serialize();
                    $.post("/data/profiles/login/",str, function(response){ 
                        switch(response.status.code) {
                            case 'FORM_INVALID':
                                $('.loginDialog > .ui-dialog-content').html(response.data.dom.dialog);
                                $.each($('.loginDialog .errorlist'), function () {
                                    $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                                });
                            break;
                            case 'CRED_OK':
                                application.settings.user = response.data.user;
                                $('#menu-container').html(response.data.dom.navbar);
                                $login.dialog("close");
                                application.ws.close();
                            break;
                            default:
                                $('.loginDialog > .ui-dialog-content').html(response.data.dom.dialog);
                            }
                        $("#notify-container").notify("create",application.ws.tt[response.status.type], {i18n: response.status.i18n});     
                    },"json");
                }                    
                $login = $(response.data.dom.dialog).dialog({
                dialogClass: 'loginDialog',position:"center", width:450,
                title: '<span class="ui-icon ui-icon-person"></span><span>'+gettext('Login')+'</span>',
                resizable: false,draggable: true,modal: true, buttons: i18nButtons, autoOpen: true
                });                
            });
        },
        //logs a user out of HWIOS, closes the websocket and updates the navigation bar
        logout: function() {
            $.getJSON('/data/profiles/logout/', function(response){ 
                if(response.status.code == 'LOGOUT_OK') {
                $('#menu-container').html(response.data.dom.navbar);
                //set anonymous user id
                application.settings.user = response.data.user;
                //application.redirect = '/blog/';
                application.ws.close();
                }
                else {
                    console.log('An error occured');
                }
                $("#notify-container").notify("create","notify-info", {i18n: response.status.i18n});   
            }); 
        },
        
        create_profile: function() {
            application.ws.remote('/profiles/create/',{},function(response){ 
                application.functions.ui.transition(response.data.dom.main, $('.main'));
            });
        },
        
        save_create_profile: function() {
            var form_data = $("form:visible").serializeObject();
            application.ws.remote('/profiles/create/',{params:form_data},function(response){ 
                    switch(response.status.code) {
                        case 'PROFILE_CREATE_OK':
                        application.functions.ui.transition(response.data.dom.main, $('.main'));                  
                        $('#personal_tabs').tabs();
                        break;
                        case 'FORM_INVALID':
                        application.functions.ui.transition(response.data.dom.main, $('.main'),response.status.code);
                        $.each($('.errorlist'), function () {$(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');})
                        break;
                    }
            });
        },
        
        cancel_create_profiles: function() {
            this.manage_profiles();        
        },
        
        delete_profiles: function(kwargs) {
            application.ws.remote('/data/profiles/delete/',{},function(response){
                var i18nButtons = {};
                i18nButtons[gettext('Cancel')] = function(){
                    $(this).dialog("close");
                }
                i18nButtons[gettext('Delete')] = function(){
                    var profiles = {};
                    $.each($(":checkbox:checked:visible"),function(idx, value){
                        profiles[$(this).data('uuid')] = {first_name: $(this).data('first_name'), last_name: $(this).data('last_name')};
                    });
                        application.ws.remote('/data/profiles/delete/',{params:profiles},function(response){
                            application.functions.ui.transition(response.data.dom.main, $('.main'));
                            _dialog.dialog('destroy');
                            _dialog = undefined;
                            $('#personal_tabs').tabs();
                        });
                    $(this).dialog('close');
                }
                var _dialog = $(response.data.dom.dialog).dialog({                
                    resizable: false,width:300, modal: true,
                    title:'<span class="ui-icon ui-icon-alert"></span><span>'+gettext("Warning")+'!</span>',
                    open: function(event, ui) {
                    $('.confirm-list').html(get_cb_names());     
                    },
                    buttons: i18nButtons
                });
            });
        },
        
        edit_profile: function(kwargs) {
            application.ws.remote('/profiles/'+kwargs.profile_name+'/edit/',{},function(response){
                
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                $('#profile-drag-avatar')
                .bind('dragenter', function(ev) {return false;})
                .bind('dragstart', function(ev) {return false;})
                .bind('dragleave', function(ev) {return false;})
                .bind('dragover', function(ev) {return false;})
                .bind('drop', function(ev) {
                var evt = ev.originalEvent;
                evt.stopPropagation();
                evt.preventDefault();
                var files = evt.dataTransfer.files;
                var count = files.length;
                    if(count == 1){
                    var file = files[0];
                    $('#profile-drag-avatar-current > span').text('Processing');
                    var reader = new FileReader();
                    reader.onloadend = function(evt) {
                        var img = $('#profile-avatar-preview')[0];
                        //img.src = evt.target.result;  
                        application.ws.remote('/profiles/'+kwargs.profile_name+'/edit/',{params:{'avatar':evt.target.result}},function(response){
                            //
                            if($('#profile-drag-avatar-current > img').length > 0) {
                                $('#profile-drag-avatar-current > img').attr('src','/media/files/avatars/'+response.data.avatar);
                            }
                            else {
                                $('#profile-drag-avatar-current > div').remove();
                                $('#profile-drag-avatar-current').append('<img src="/media/files/avatars/'+response.data.avatar+'"/>');
                            }
                            $('#profile-drag-avatar-current > span').text('');
                        });
                    };
                    reader.readAsDataURL(file);
                    }
                });
            });
        },
        
        cancel_edit_profile: function() {
            this.manage_profiles();        
        },
        
        save_edit_profile: function(kwargs) {
            var form_data = $("form:visible").serializeObject();
            application.ws.remote('/profiles/'+kwargs.profile_name+'/edit/',{params:form_data},function(response){        
                switch(response.status.code) {
                    case 'FORM_INVALID':
                        application.functions.ui.transition(response.data.dom.main, $('.main'), response.status.code);
                        $.each($('.errorlist'), function () {$(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');});
                    break;
                    case 'PROFILE_EDIT_OK':
                        application.functions.ui.transition(response.data.dom.main, $('.main'), response.status.code);                  
                        $('#personal_tabs').tabs();
                    break;
                }
            });
        }
    } 
}

function bind_ws() {
    //Blog page was modified by another user, update it...
    application.ws.method('^/profiles/manage/modified/$', function(kwargs){
        application.functions.profiles.manage_profiles(kwargs, true);
    });


}

function bind_events() {
    
}

function unbind_events() {
    
}
    
return {
    init: function(uri, push_history) {
        profiles_context = $.context({anchor:'.main',delegate:'#profiles-context',uri:'/profiles/context/',id:'ctx-profiles'});
        bind_functions();
        bind_ws();
        bind_events();
        selected_tab = 0;
        application.functions.profiles.route(uri, push_history);
        return 'profiles';
        },
    load: function(uri, push_history) {
        if(typeof application.cache.load.context.profiles == 'undefined') {
            application.cache.load.context.profiles = true;
            profiles_context.reload();
            }
        bind_events();
        selected_tab = 0;
        application.functions.profiles.route(uri, push_history);
    },
    clean_up: function(){
        unbind_events();
    }
}
});