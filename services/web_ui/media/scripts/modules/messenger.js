/*# -*- coding: utf-8 -*-
"""
    scripts.modules.messenger
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Messenger module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
*/
define('modules/messenger',[
'lib/jquery/jquery.emoticon',
],function(emoticon){
    var messenger_context;
    
    
    function bind_ws() {
        application.ws.method('^/data/modules/messenger/online/update/$', function(params){
            get_online(params.online);    
        });
        application.ws.method('^/data/modules/messenger/messages/receive/$',function(params){
            var chatline = $('<div/>').text(params.message).html();
            chatline = $().emoticon(application.settings.services.web_ui.default_theme, chatline);
            $('#messages').prepend('\
            <div class="message-container">\
                <div class="message-header"><span>'+params.from+'</span><span>'+params.time+'</span></div>\
                <div class="message-text">'+chatline+'</div>\
            </div>');
            $('#messages > .message-container:first-child').hide().fadeIn(400);
            //$('#message_box').scrollTop($('#message_box > #messages').outerHeight());
        });
    }
    
    function bind_events() {
        $('#message_input_field').val(gettext("Type a message..."));
        $('#message_input_field').keypress(function(e){
            if (e.which == 13) {send_message();}
        });
        $('#message_input_field').focus(function(e){
            if($('#message_input_field').val() == gettext("Type a message...")) {
            $('#message_input_field').val('');
            }
        });
        $('#message_input_field').blur(function(e){
            if($('#message_input_field').val() != gettext("Type a message...") &&
               $('#message_input_field').val() != '') {
            
            }
            else {
            $('#message_input_field').val(gettext("Type a message..."));
            }
        });
        $(document).bind('WS_ONLINE', function(event) {
            application.ws.remote('/data/modules/messenger/init/',{},function(response){
                if(messenger_context === undefined){
                    //load context here
                    messenger_context = $.context({anchor:'.sidebar',delegate:'#messenger-context',data:response.data.dom.context,id:'ctx-messenger'});
                    application.cache.load.context.messenger = true;
                }
                else {
                    application.cache.load.context.messenger = true;
                    messenger_context.reload(response.data.dom.context);
                }
                get_online(response.data.online);
            });
            
        });
        $(document).unbind('WS_OFFLINE').bind('WS_OFFLINE', function(event) {
            $('#message_box').addClass('ws-disabled');
            $('#message_input_field').addClass('ws-disabled');
            $('#send_button').addClass('ws-disabled');
            $('#online-box').addClass('ws-disabled');
            $('#online-box').empty();
            $('#messages').append('<div class="message-notification">Disconnected...</div>');
        });   
    }
    
    function send_message() {
        var message = $('#message_input_field').val();
        $('#message_input_field').val('');
        if(message !='') {
            application.ws.remote('/data/modules/messenger/message/send/',{'message':message},function(response){
                chatline = $().emoticon(application.settings.services.web_ui.default_theme, response.data.message);
                $('#messages').prepend('<div class="message-container">\
                    <div class="message-header"><span>'+gettext("You")+'</span><span>'+response.data.time+'</span></div>\
                    <div class="message-text">'+chatline+'</div>\
                </div>');
                $('#messages > .message-container:first-child').hide().fadeIn(400);
                //$('#message_box').scrollTop($('#message_box > #messages').outerHeight());
            });
        }
    }    
        
    function enable_widget() {
        $('#message_box').removeClass('ws-disabled');
        $('#message_input_field').removeClass('ws-disabled');
        $('#send_button').removeClass('ws-disabled');
        $('#online-box').removeClass('ws-disabled');
        $('#messages').empty();  
    } 
    
    function get_online(users) {
        $('#online-box').empty();
        $.each(users,function(key,user) {
            var _avatar;
            if(user.avatar != ''){
            _avatar = '/media/files/avatars/'+user.avatar;
            }
            else {
            _avatar = '/media/themes/start/css/images/unknown_avatar.png'
            }
            
            var _user_dom;
            if(user.id == application.settings.user.id){
                if(user.name.indexOf('visitor') != -1){
                    _user_dom = '<div data-id="'+user.name+'" data-ctx-showid="'+user.id+'" class="messenger-participant"><div class="messenger-avatar"><img src="'+_avatar+'"/></div><div>'+user.name+' ('+gettext('You')+')</div></div>';
                }
                else {
                    _user_dom = '<div data-id="'+user.name+'" data-ctx-showid="'+user.id+'" data-ctxmatch="view-profile" class="messenger-participant"><div class="messenger-avatar"><img src="'+_avatar+'"/></div><div>'+user.name+' ('+gettext('You')+')</div></div>';
                }
                $('#online-box').prepend(_user_dom);
            }
            else {
                if(user.name.indexOf('visitor') != -1){
                //hide for own user when visitor
                _user_dom = '<div data-id="'+user.name+'" data-ctx-showid="'+user.id+'" class="messenger-participant"><div class="messenger-avatar"><img src="'+_avatar+'"/></div><div>'+user.name+'</div></div>';
                }
                else {
                _user_dom = '<div data-id="'+user.name+'" data-ctx-showid="'+user.id+'" data-ctxmatch="view-profile" class="messenger-participant"><div class="messenger-avatar"><img src="'+_avatar+'"/></div><div>'+user.name+'</div></div>';
                }
            $('#online-box').append(_user_dom);
            }
            
        });
    }
    
    return { 
            
        init:function() {
            bind_events();
            enable_widget();
            bind_ws();
            return 'messenger';
        }
    }
});