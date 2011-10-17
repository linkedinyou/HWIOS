/*# -*- coding: utf-8 -*-
"""
    scripts.modules.ui
    ~~~~~~~~~~~~~~~~~~

    User Interface module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
*/
define('modules/ui',[
'lib/jquery/jquery.misc',
'lib/tools/jit',
'order!lib/jquery/jquery.ui',
'order!lib/jquery/jquery.notify',
'order!lib/jquery/jquery.elfinder',
],



function(){
   
    var $login, $register, $depload;
    var root = 'media/js/';        

        
function bind_functions() {
    application.functions.ui = {
        route: function(uri, push_history) { 
            if(typeof urls == 'undefined') {
                urls = [];
            }
            application.route_uri_to_mod_function(uri, urls, push_history);
        },
        update_buttons: function(checkbox) {
            application.params.cb_selected = 0;            
            checkboxes = $(':checkbox:not(#cb-all):visible').size();
            $(':checkbox:not(#cb-all):visible').each(function(index,value) {
                if(value.checked == true) {
                application.params.cb_selected += 1;
                }
            });
            if(application.params.cb_selected == 1) {
                $('.btn-active-one').removeClass('ui-state-disabled');
                $('.btn-active-many').removeClass('ui-state-disabled'); 
            }
            else if(application.params.cb_selected > 1) {
                $('.btn-active-many').removeClass('ui-state-disabled');
                $('.btn-active-one').addClass('ui-state-disabled');
            }
            else {
                $('.btn-active-one').addClass('ui-state-disabled');
                $('.btn-active-many').addClass('ui-state-disabled');
            }
        },
        add_widgets: function(left_widgets, right_widgets) {
            $.each(left_widgets, function(idx, widget) {
                $('.sidebar').append(widget).hide().fadeIn('fast');
            });
        },
        transition: function(content, target, transition_type){
            switch(transition_type){
                case 'fade':
                    $(target).hide().html(content).fadeIn();
                break;
                case 'FORM_INVALID':
                    $(target).html(content);
                break;
                default:
                    $(target).hide().html(content).fadeIn('fast');
                break;
            }
        },
        mark_menu: function(){
            //on first load, set our menu like when clicked on
            $('.menu-item').each(function(idx,value){
                _data = $(this).data();
                if('uri' in _data && location.pathname.indexOf(_data.uri) != -1){
                    $(this).addClass('menu-item-selected');
                    $(this).parents('li').addClass('menu-item-selected');
                }
            });
        }
    }
}

function bind_events() {
    /**
    * Standard button effects
    */
    $('button.btn').die('hover').live('hover',function(ev){
            $(this).toggleClass("ui-state-hover");
    });
    $('button.btn').die('mousedown').live('mousedown',function(){
        if(!$(this).hasClass('ui-state-disabled')){
            $(this).parents('.btn-set-single:first').find(".btn.ui-state-active").removeClass("ui-state-active");
            if( $(this).is('.ui-state-active.btn-toggleable, .btn-set-multi .ui-state-active') ){ $(this).removeClass("ui-state-active"); }
            else { $(this).addClass("ui-state-active"); }
        }
    });
    $('button.btn').die('mouseup').live('mouseup',function(){
            if(! $(this).is('.btn-toggleable, .btn-set-single .btn, btn-set-multi .btn') ){
                $(this).toggleClass("ui-state-active");
            }
    });
    /**
    * Links a button marker to a hwios module function, either through a data-url or a data-function
    */
    $('body').undelegate('.btn', 'click').delegate('.btn', 'click', function(event){
        if(!($(this).hasClass('ui-state-disabled')) && !($(this).hasClass('action-icon-disabled'))) {
        application.route_button($(this));
        }
    });
    /**
    * Handle the function-call events when clicking on the menu items
    */
    $('body').undelegate('.menu-item','click').delegate('.menu-item', 'click', function(event){
        $('.menu-item-selected').removeClass('menu-item-selected');
        if(!$(this).hasClass('menu-item-selected')) {
            $(this).addClass('menu-item-selected');
            $(this).parents('li').addClass('menu-item-selected');
            console.log('booh');
        }
        var params = $(this).data();
        if('uri' in params){
            //Don't push state of data function's to navbar state
            if(params.uri.indexOf('data') != -1) {
                application.route_uri_to_mod(params.uri, false);
            }
            else {
                application.route_uri_to_mod(params.uri, true);
            }
        }
    });    
    $(document).unbind('USER_LOGIN USER_LOGOUT WS_ONLINE').bind('USER_LOGIN USER_LOGOUT WS_ONLINE',function(ev){
        application.functions.ui.mark_menu();
    });
    
    /**
    * Hides and shows django form validation indicators on hover
    */
    $('p:has(.ui-icon-info)').live('hover', function () {
        console.log('show');
        $(this).prev('.errorlist').toggleClass('errorlist-show');
    });
    
    
    //Checkbox logic
    $('html').undelegate('.datatable tr','click').delegate('.datatable tr',"click", function(event){
        if ($(event.target).is('td')) {            
            if (event.target.type !== 'checkbox') {
                if(!$(':checkbox', this).is(':checked')) {
                    $(':checkbox', this).attr('checked',true);                    
                }
                else $(':checkbox', this).attr('checked',false);
                application.functions.ui.update_buttons();
            }
        }
    });
    
    $(':checkbox:not(#cb-all):visible').live("click",function() {application.functions.ui.update_buttons();});
    $('#cb-all').live('click', function(event){
        if($(this).attr('checked') == 'checked') {
            $.each($(':checkbox:visible:not(#cb-all)'), function(idx, value){
                $(this).attr('checked',true);
            });
        }
        else {
            $.each($(':checkbox:visible:not(#cb-all)'), function(idx, value){
                $(this).attr('checked',false);
            });
        }
    application.functions.ui.update_buttons();
    });     
    
    //Handle browser back-button
    window.addEventListener('popstate', function() {
        application.route_uri_to_mod(location.pathname, false);            
    }, false);
    
    $("#notify-container").notify({speed: 200,stack:'above',custom:false});

    $("html").undelegate('a','click').delegate('a', 'click', function(event){
        event.preventDefault();
        var site_url = application.settings.services.web_ui.uri.split(':')[0];
        var uri = $(event.target).attr('href');
        if(event.target.href.indexOf(site_url) == -1) {
            window.open(event.target.href);
        }
        else if(uri.indexOf('docs') != -1 || uri.indexOf('media') != -1) {
            window.open(event.target.href);
        }
        else {
            
            //Site references to docs or media dir
                //Placeholder url-dummies for jquery ui's tabbing
                if(uri == '#'){
                return;
                }
            //check for proper url ending '/'
            if(uri.substr(-1) != '/'){
            uri = uri + '/';
            }
            $(this).attr('data-uri',uri);
            application.route_button($(this));
        }
    });    
    /**
    * XHR preprocessors
    */
    $('body').ajaxComplete(function(event, xhr, options) {
        if(typeof xhr !=='undefined') {
        var data = $.parseJSON(xhr.responseText);
            if (typeof data !== 'undefined' && typeof data.status !== 'undefined' && typeof data.status.code !=='undefined') {
                switch(data.status.code) {
                    case 'LOGIN': 
                    application.functions.login();
                    break;
                }
            }
            
        }
    });
}
    
    return {
        init: function(uri, push_history) {
            bind_functions();
            bind_events();
            return 'ui';
        },
        load: function(uri, push_history) {
            //bind_events();
        },
        clean_up: function() {
            unbind_events();
           
        }
    }
});