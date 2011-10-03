/*# -*- coding: utf-8 -*-
"""
    scripts.modules.blog
    ~~~~~~~~~~~~~~~~~~~~

    Blog module 

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
*/
require.def('modules/blog',[
'lib/jquery/jquery.rte',
],
function(){
    var blog_context;
    var delayed_update;
    var urls;
    var rte;

    function applyCreole(element, source) {
        if(typeof(creole_parser) == 'undefined') {
            var options = {};
            options.linkFormat = '/blog/';
            creole_parser = new Parse.Simple.Creole(options);
        }
        creole_parser.parse(element,source);
    }



function bind_functions() {

    application.functions.blog = {
        route: function(uri, push_history) {
            if(urls == undefined) {
                urls = [
                    [XRegExp('^/blog/$'),this.view_blog],
                    [XRegExp('^/blog/create/$'),this.view_new_article],
                    [XRegExp('^/blog/(?<id>[^/]+)/$'),this.view_article],
                    [XRegExp('^/blog/(?<id>[^/]+)/edit/$'),this.view_edit_article],
                ];
            }
            application.route_uri_to_mod_function(uri, urls, push_history);
        },

        view_blog: function(kwargs, update) {
            if(update == undefined){
                application.ws.remote('/blog/',{},function(response){
                    application.functions.ui.transition(response.data.dom.main, $('.main'));
                    $tabs = $('#blog-tabs').tabs({select: function(event, ui) {history.pushState(null, null, ui.tab.hash);}});
                    rte = $.rte('#text',{});
                });
            }
            else {
                application.functions.ui.transition(kwargs.data.dom.main, $('.main'));
                $tabs = $('#blog-tabs').tabs({select: function(event, ui) {history.pushState(null, null, ui.tab.hash);}});
                rte = $.rte('#text',{});
            }
        },
        view_article: function(kwargs, update) {
            if(update == undefined){
                application.ws.remote('/blog/'+kwargs.id+'/',{},function(response){
                    application.functions.ui.transition(response.data.dom.main, $('.main'));
                });
            }
            else {
                application.functions.ui.transition(kwargs.data.dom.main, $('.main'));
            }            
        },        

        view_new_article: function(kwargs) {
            application.ws.remote('/blog/create/',{},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                rte = $.rte('#text',{});
            });
        },

        view_edit_article: function(kwargs) {
            application.ws.remote('/blog/'+kwargs.id+'/edit/',{},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                rte = $.rte('#text',{});
            });
        },

        save_new_article: function(kwargs) {
            var form_data = application.prepare_form($("form:visible"));
            application.ws.remote('/blog/create/',{params:form_data},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'), response.status.code);
                if(response.status.code == 'FORM_INVALID') {
                    rte = $.rte('#text',{});
                    $.each($('.main .errorlist'), function () {
                    $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                    });
                }
            });
        },
        
        save_edit_article: function(kwargs) {
            var form_data = application.prepare_form($("form:visible"));
            application.ws.remote('/blog/'+kwargs.slug+'/edit/',{params:form_data},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'), response.status.code);
                if(response.status.code == 'FORM_INVALID') {
                    rte = $.rte('#text',{});
                    $.each($('.main .errorlist'), function () {
                    $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                    });
                }
            });
        },
        
        delete_article: function(kwargs) {
            application.ws.remote('/data/blog/'+kwargs.id+'/delete/',{}, function(response) {
                i18nButtons = {}
                i18nButtons[gettext('Cancel')] = function(){
                    $(this).dialog('close');
                }
                i18nButtons[gettext('Delete')] = function(){
                    application.ws.remote('/data/blog/'+kwargs.id+'/delete/',{params:{uuid:kwargs.uuid}},function(response){
                        switch(response.status.code) {
                            case "BLOG_ARTICLE_DELETED":
                                application.functions.ui.transition(response.data.dom.main, $('.main'));
                                $tabs = $('#blog-tabs').tabs({select: function(event, ui) {window.location.hash = ui.tab.hash;}});
                                $.rte('.contenteditable',{});
                            break;
                        }
                    });
                    $(this).dialog('close');
                }
                var _dialog = $(response.data.dom.dialog).dialog({
                    resizable: false,width:330, modal: true, zIndex:1000000,
                    title:'<span class="ui-icon ui-icon-alert"></span><span>'+gettext("Warning")+'!</span>',
                    buttons: i18nButtons
                });
            });
        },

        create_comment: function(kwargs) {
            var form_data = application.prepare_form($("form:visible"));
            application.ws.remote('/data/blog/'+kwargs.slug+'/comments/create/',{params:form_data}, function(response) {
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                switch(response.status.code) {
                    case "BLOG_COMMENT_CREATED":
                    break;
                    case "FORM_INVALID":
                        $.each($('.main .errorlist'), function () {
                        $(this).next().prepend('<span class="ui-icon ui-icon-info"></span>');
                        });
                    break;
                }
            });
        },

        delete_comment: function(kwargs) {
            application.ws.remote('/data/blog/'+kwargs.article+'/comments/'+kwargs.uuid+'/delete/',{}, function(response) {
                var _dialog = $(response.data.dom.dialog).dialog({
                    resizable: false,width:440, modal: true, zIndex:1000000,
                    title:'<span class="ui-icon ui-icon-alert"></span><span>'+gettext("Warning")+'!</span>',
                    buttons: {
                        Cancel: function() {
                        $(this).dialog('close');
                        },
                        Delete: function() {
                            application.ws.remote('/data/blog/'+kwargs.article+'/comments/'+kwargs.uuid+'/delete/',{params:{}},function(response){
                                switch(response.status.code) {
                                    case "BLOG_COMMENT_DELETED":
                                        application.functions.ui.transition(response.data.dom.main, $('.main'));
                                        $tabs = $('#blog-tabs').tabs({select: function(event, ui) {window.location.hash = ui.tab.hash;}});
                                        $.rte('.contenteditable',{});
                                    break;
                                }
                            });
                            $(this).dialog('close');
                        }
                    }
                });
            });
        }
    }
}



function bind_events() {
    //follow link to new blog article when clicked
    $(".main").delegate("#blog-content a", "click", function(event){
        event.preventDefault();
        url = $(event.target).attr('href')+'/';
        application.functions.blog.route(url, true);
    });
}


function bind_ws() {
    //Blog page was modified by another user, update it...
    application.ws.method('^/blog/modified/$', function(kwargs){
        var rte_content = rte.get_html();
        application.functions.blog.view_blog(kwargs, true);
        rte.set_html(rte_content);
    });

    //Blog article was modified by another user, update it...
    application.ws.method('^/blog/(?<slug>[^/]+)/modified/$',function(kwargs){
        kwargs = application.merge_objects(kwargs, $('.blog-article').data());
        application.functions.blog.view_article(kwargs, true);
    });
}

function unbind_events() {
    $(".main").undelegate("#blog-content a", "click");
}

    return {
        init: function(uri, push_history) {
            blog_context = $.context({anchor:'.main',delegate:'#blog-context',uri:'/blog/context/',id:'ctx-blog'});
            application.cache.load.context.blog = true;
            bind_functions();
            bind_ws();            
            application.functions.blog.route(uri, push_history);
            bind_events();
            return 'blog';
        },
        load: function(uri, push_history) {
            if(typeof application.cache.load.context.blog == 'undefined') {
                application.cache.load.context.blog = true;
                blog_context.reload();
            }
            bind_events();
            application.functions.blog.route(uri, push_history);
        },
        clean_up: function(){
            $('div[class*="hwios-plasmoid"]').remove();
            unbind_events();
        }
    }
});
