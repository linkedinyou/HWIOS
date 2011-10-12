require.def("modules/wiki",[],function(){function r(){$(".main").undelegate("#wiki-markdown a","click")}function q(){application.ws.method("^/data/wiki/(?<id>[^/]+)/online/update/$",function(a){c.update_online(a.online)}),application.ws.method("^/data/wiki/(?<id>[^/]+)/edit/notify/$",function(a){}),application.ws.method("^/wiki/(?<id>[^/]+)/$",function(a){var b=window.location.pathname.split("/"),c=b[2],d=b[3];c==a.id&&(d==""&&m(a.id)),$(document).trigger("WIKI_ARTICLE_CREATED",{id:a.id})}),application.ws.method("/data/wiki/(?<id>[^/]+)/saved/",function(a){$("#undo_slider").length>0&&(i.push(a.data.revision),$("#undo_slider").slider("option","max",[i.length]),$("#undo_slider").slider("option","value",[i.length]),j(i)),$("#btn-frontend-wiki-edit-history").length>0&&$("#btn-frontend-wiki-edit-history").removeClass("ui-state-disabled")}),application.ws.method("/data/wiki/(?<id>[^/]+)/deleted/",function(a){var b=window.location.pathname.split("/"),c=b[2],d=b[3];$(document).trigger("WIKI_ARTICLE_CREATED",{id:a.id}),c==a.id&&m(a.id)})}function p(){$(".main").delegate("#wiki-markdown a","click",function(a){a.preventDefault(),url=$(a.target).attr("href"),application.functions.wiki.route(url,!0)}),$(document).bind("infinote_update",function(a){n($("#wiki-markdown"),c._state.buffer.toString())})}function o(){application.functions.wiki={route:function(a,b){k==undefined&&(k=[[XRegExp("^/wiki/(?<id>[^/]+)/$"),this.view_article],[XRegExp("^/wiki/(?<id>[^/]+)/edit/$"),this.edit_article],[XRegExp("^/wiki/(?<id>[^/]+)/edit/history/$"),this.edit_article_history]]),application.route_uri_to_mod_function(a,k,b)},view_article:function(a){console.log(a),$(document).trigger("WIKI_ARTICLE_LINK_FOLLOWED",{id:a.id}),m(a.id)},edit_article:function(a){a.id==undefined&&(a.id=$("#btn-frontend-wiki-edit").attr("data-url")),l(a.id)},edit_fullscreen:function(a){var b=$(".edit-wiki-page");$(b).hasClass("wiki-fullscreen")?($(b).removeClass("wiki-fullscreen"),$(".sidebar").removeClass("sidebar-fullscreen")):($(b).addClass("wiki-fullscreen"),$(".sidebar").addClass("sidebar-fullscreen")),c.editor.refresh()},cancel_edit_article:function(a){var b=$("form:visible").serializeObject();m(a.id)},edit_article_history:function(a){e=$(".main > .hwios-widget:first").html();var b=new diff_match_patch;j=function(a){h=$("#undo_slider").slider("option","value"),$("#id_submit_comments").val(a[h-1].submit_comments),a=a.slice(0,h),patches=[],$.each(a,function(a,c){patches.push(b.patch_fromText(c.patch))}),g="",$.each(patches,function(a,c){g=b.patch_apply(c,g)[0]}),n($("#wiki-markdown"),g)},application.ws.remote("/wiki/"+a.id+"/edit/history/",{},function(a){i=a.page.revisions,application.functions.ui.transition(a.data.dom.main,$(".main")),$.data($("#wiki-restore-button")[0],"revision",a.page.revisions.length);var b=$("#undo_slider").slider({animate:!0,min:1,max:a.page.revisions.length,value:a.page.revisions.length,change:function(a,b){var c=$("#undo_slider").slider("option","value");$("#undo_slider_value").html("@ "+c),$("#id_content").attr("disabled",!1)},slide:function(a,b){var c=$("#undo_slider").slider("option","value");$("#undo_slider_value").html('<div class="change_to_text">@ '+c+"</div>"),$("#id_content").attr("disabled",!0),typeof d=="number"&&clearTimeout(d),d=setTimeout(j(i),100)},stop:function(a,b){var c=$("#undo_slider").slider("option","value");$.data($("#wiki-restore-button")[0],"revision",c),$("#undo_slider_value").html('<div class="change_to_text">@ '+c+"</div>"),typeof d=="number"&&clearTimeout(d),j(i)}});i.length>0&&(j(i),$("#undo_slider_value").text("@ "+$("#undo_slider").slider("option","value")))})},cancel_edit_article_history:function(a){$(".main").html(e).hide(),l(a.id)},restore_article_history:function(a){application.ws.remote("/data/wiki/"+a.id+"/edit/notify/",{revision:a.revision},function(b){f=g,l(a.id,undefined,f)})},save_edit_article:function(a){var b=$("form:visible").serializeObject();b.content=c._state.buffer.toString(),application.ws.remote("/data/wiki/"+a.id+"/save/",{params:b},function(b){switch(b.status.code){case"WIKI_EDIT_OK":m(a.id),$(document).trigger("WIKI_ARTICLE_SAVED",{id:a.id});break;case"WIKI_EDIT_NO_CHANGE":m(a.id);break;case"FORM_INVALID":l(a.id,b)}})},save_new_article:function(a){application.ws.remote("/data/wiki/"+a.id+"/save/",{params:{id:a.id,submit_comments:"Page created",content:""}},function(b){l(a.id),$(document).trigger("WIKI_ARTICLE_CREATED",{id:a.id})})},delete_article:function(a){application.ws.remote("/data/wiki/"+a.id+"/delete/",{},function(b){i18nButtons={},i18nButtons[gettext("Cancel")]=function(){$(this).dialog("close")},i18nButtons[gettext("Delete")]=function(){application.ws.remote("/data/wiki/"+a.id+"/delete/",{params:{id:a.id}},function(b){switch(b.status.code){case"WIKI_DELETE_OK":$(".main").html(b.data.dom.main).hide().fadeIn(),$(document).trigger("WIKI_ARTICLE_DELETED",{id:a.id})}}),$(this).dialog("close")};var c=$(b.data.dom.dialog).dialog({resizable:!1,width:300,modal:!0,zIndex:1e6,title:'<span class="ui-icon ui-icon-alert"></span><span>'+gettext("Warning")+"!</span>",buttons:i18nButtons})})}}}function n(a,c){b.postMessage(c)}function m(a){c=$.jinfinote(application.ws,{ws_connect:"/wiki/"+a+"/",ws_disconnect:"/data/wiki/"+a+"/disconnect/",ws_insert:"/data/wiki/"+a+"/insert/",ws_delete:"/data/wiki/"+a+"/remove/",ws_undo:"/data/wiki/"+a+"/undo/",ws_caret:"/data/wiki/"+a+"/caret/",cb_insert:"^/data/wiki/(?<id>[^/]+)/insert/$",cb_delete:"^/data/wiki/(?<id>[^/]+)/remove/$",cb_undo:"^/data/wiki/(?<id>[^/]+)/undo/$",cb_caret:"^/data/wiki/(?<id>[^/]+)/caret/$",editor:"listen",init:function(a){application.functions.ui.transition(a.dom.main,$(".main"),""),a.page.state!==!1&&n($("#wiki-markdown"),a.page.state[1]);return{editor_element:"#wiki-editor"}}})}function l(a,b,d){c=$.jinfinote(application.ws,{ws_connect:"/wiki/"+a+"/edit/",ws_disconnect:"/wiki/"+a+"/disconnect/",ws_insert:"/data/wiki/"+a+"/insert/",ws_delete:"/data/wiki/"+a+"/remove/",ws_undo:"/data/wiki/"+a+"/undo/",ws_caret:"/data/wiki/"+a+"/caret/",cb_insert:"^/data/wiki/(?<id>[^/]+)/insert/$",cb_delete:"^/data/wiki/(?<id>[^/]+)/remove/$",cb_undo:"^/data/wiki/(?<id>[^/]+)/undo/$",cb_caret:"^/data/wiki/(?<id>[^/]+)/caret/$",mode:"markdown",init:function(a){layout=a.dom.main,page=a.page,typeof b=="undefined"?application.functions.ui.transition(layout,$(".main")):(application.functions.ui.transition(b.data.dom.main,$(".main"),b.status.code),$.each($(".main .errorlist"),function(){$(this).next().prepend('<span class="ui-icon ui-icon-info"></span>')})),a.page.revisions<2&&$("#wiki-edit-history").addClass("ui-state-disabled"),n($("#wiki-markdown"),a.page.state[1]);return d!==undefined?{editor_element:"#wiki-editor",add_text:d}:{editor_element:"#wiki-editor"}}})}var a,b=new Worker("/media/scripts/lib/tools/markdown_worker.js"),c,d,e,f=null,g=null,h=0,i,j,k;b.onmessage=function(a){$("#wiki-markdown").html(a.data)};return{init:function(b,c){a=$.context({anchor:".main",delegate:"#wiki-context",uri:"/wiki/context/",id:"ctx-wiki"}),application.cache.load.context.wiki=!0,o(),q(),p(),application.functions.wiki.route(b,c);return"wiki"},load:function(b,c){typeof application.cache.load.context.wiki=="undefined"&&(application.cache.load.context.wiki=!0,a.reload()),p(),application.functions.wiki.route(b,c),$(document).trigger("WIKI_ARTICLE_LINK_FOLLOWED",{id:"Main"})},clean_up:function(){$('div[class*="hwios-plasmoid"]').remove(),r()}}})