function create_smileys_from(a,b){for(var c in emoticons.emoticon){emoticon=emoticons.emoticon[c];for(var d in emoticon.emotes)d=RegExp.escape(d),b=b.replace(new RegExp(d,"gi"),'<img src="'+a+emoticon.image+'" />')}return b}function create_urls_from(a){return a.replace(/(ftp|http|https|file):\/\/[\S]+(\b|$)/gim,'<a href="$&" class="messenger_link" target="_blank">$&</a>').replace(/([^\/])(www[\S]+(\b|$))/gim,'$1<a href="http://$2" class="messenger_link" target="_blank">$2</a>')}RegExp.escape=function(a){if(!arguments.callee.sRE){var b=["/",".","*","+","?","|","(",")","[","]","{","}","\\"];arguments.callee.sRE=new RegExp("(\\"+b.join("|\\")+")","g")}return a.replace(arguments.callee.sRE,"\\$1")},$.fn.emoticon=function(a,b){var c="/media/themes/"+a+"/css/images/emotes/",d=create_smileys_from(c,b),e=create_urls_from(d);return e};var emoticons={emoticon:{"::smile":{image:"smile.png",emotes:{":-)":"",":)":"",":]":""}},"::bigSmile":{image:"bigsmile.png",emotes:{":D":"",":-D":"",XD:"",BD:""}},"::shock":{image:"shock.png",emotes:{":O":"",":0":"",":-0":"",":-O":""}},"::frown":{image:"frown.png",emotes:{":-(":"",":[":"",":<":"",":(":"",":-\\":""}},"::tongue":{image:"tongue.png",emotes:{":P":"",XP:""}},"::bored":{image:"bored.png",emotes:{":\\":"",":-\\":"",":|":""}},"::wink":{image:"wink.png",emotes:{";-)":"",";)":"",";]":""}},"::confused":{image:"confused.png",emotes:{":S":"",":?":""}}}};define("lib/jquery/jquery.emoticon",function(){}),define("modules/messenger",["lib/jquery/jquery.emoticon"],function(a){function g(a){$("#online-box").empty(),$.each(a,function(a,b){var c;b.avatar!=""?c="/media/files/avatars/"+b.avatar:c="/media/themes/start/css/images/unknown_avatar.png";var d;b.id==application.settings.user.id?(b.name.indexOf("visitor")!=-1?d='<div data-id="'+b.name+'" data-ctx-showid="'+b.id+'" class="messenger-participant"><div class="messenger-avatar"><img src="'+c+'"/></div><div>'+b.name+" (you)</div></div>":d='<div data-id="'+b.name+'" data-ctx-showid="'+b.id+'" data-ctxmatch="view-profile" class="messenger-participant"><div class="messenger-avatar"><img src="'+c+'"/></div><div>'+b.name+" (you)</div></div>",$("#online-box").prepend(d)):(b.name.indexOf("visitor")!=-1?d='<div data-id="'+b.name+'" data-ctx-showid="'+b.id+'" class="messenger-participant"><div class="messenger-avatar"><img src="'+c+'"/></div><div>'+b.name+"</div></div>":d='<div data-id="'+b.name+'" data-ctx-showid="'+b.id+'" data-ctxmatch="view-profile" class="messenger-participant"><div class="messenger-avatar"><img src="'+c+'"/></div><div>'+b.name+"</div></div>",$("#online-box").append(d))})}function f(){$("#message_box").removeClass("ws-disabled"),$("#message_input_field").removeClass("ws-disabled"),$("#send_button").removeClass("ws-disabled"),$("#online-box").removeClass("ws-disabled"),$("#messages").empty()}function e(){var a=$("#message_input_field").val();$("#message_input_field").val(""),a!=""&&application.ws.remote("/data/modules/messenger/message/send/",{message:a},function(a){chatline=$().emoticon(application.settings.services.web_ui.default_theme,a.data.message),$("#messages").prepend('<div class="message-container">\n                    <div class="message-header"><span>'+gettext("You")+"</span><span>"+a.data.time+'</span></div>\n                    <div class="message-text">'+chatline+"</div>\n                </div>"),$("#messages > .message-container:first-child").hide().fadeIn(400)})}function d(){$("#message_input_field").keypress(function(a){a.which==13&&e()}),$(document).bind("WS_ONLINE",function(a){application.ws.remote("/data/modules/messenger/init/",{},function(a){b===undefined?(b=$.context({anchor:".sidebar",delegate:"#messenger-context",data:a.data.dom.context,id:"ctx-messenger"}),application.cache.load.context.messenger=!0):(application.cache.load.context.messenger=!0,b.reload(a.data.dom.context)),g(a.data.online)})}),$(document).unbind("WS_OFFLINE").bind("WS_OFFLINE",function(a){$("#message_box").addClass("ws-disabled"),$("#message_input_field").addClass("ws-disabled"),$("#send_button").addClass("ws-disabled"),$("#online-box").addClass("ws-disabled"),$("#online-box").empty(),$("#messages").append('<div class="message-notification">Disconnected...</div>')})}function c(){application.ws.method("^/data/modules/messenger/online/update/$",function(a){g(a.online)}),application.ws.method("^/data/modules/messenger/messages/receive/$",function(a){var b=$("<div/>").text(a.message).html();b=$().emoticon(application.settings.services.web_ui.default_theme,b),$("#messages").prepend('\n            <div class="message-container">\n                <div class="message-header"><span>'+a.from+"</span><span>"+a.time+'</span></div>\n                <div class="message-text">'+b+"</div>\n            </div>"),$("#messages > .message-container:first-child").hide().fadeIn(400)})}var b;return{init:function(){d(),f(),c();return"messenger"}}})