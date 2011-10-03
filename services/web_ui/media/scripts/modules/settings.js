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

require.def('modules/settings',[
],
function(maps){
    
function bind_events() {        
    
    $(document).bind('MAP_FREE_LOCATION MAP_REGION_LOCATION', function(e,x,y) {
        $('input').each(function(index) {
            if($(this).attr('id') == 'id_center_x'){
            $(this).val(x);
            }
            else if($(this).attr('id') == 'id_center_y'){
            $(this).val(y);
            }
            else if($(this).attr('id') == 'id_center_z'){
            $(this).val(maps.get_zoom());
            }
        });
    });        
}
    
function bind_functions(){
    application.functions.settings = {};
    
    application.functions.settings.route = function(uri, push_history) {
        routes = [
            [XRegExp('^/settings/$'),application.functions.settings.view_settings],
        ];
        application.route_uri_to_mod_function(uri, routes, push_history);
    }
    
    
    application.functions.settings.view_settings = function(kwargs, update){
        if(update == undefined){
            application.ws.remote('/settings/',{},function(response){
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                $tabs = $('#settings_tabs').tabs();
            });
        }
        else {
            application.functions.ui.transition(kwargs.data.dom.main, $('.main'));
            $tabs = $('#settings_tabs').tabs();
        }
    }
    
    application.functions.settings.update_settings = function() {
        var form_data = $("form:visible").serializeObject();
        var selected = $tabs.tabs('option', 'selected');
        application.ws.remote('/data/settings/save/',{params:form_data},function(response){
            application.functions.ui.transition(response.data.dom.main, $('.main'));
            $tabs = $('#settings_tabs').tabs();
            $tabs.tabs('option', 'selected',selected);
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

function bind_ws() {
    //Blog page was modified by another user, update it...
    application.ws.method('^/settings/modified/$', function(kwargs){
        application.functions.settings.view_settings(kwargs, true);
    });

}
        
    
return {
    init: function(uri, push_history) {
        bind_events();
        bind_functions();
        bind_ws();
        application.functions.settings.route(uri, push_history);
        return 'settings';
    },
    load: function(uri, push_history) {
        bind_events();
        application.functions.settings.route(uri, push_history);
    },
    clean_up: function() {
        
    }
}
});
