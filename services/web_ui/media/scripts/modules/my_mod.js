/*
* Copyright (c) OS-Networks, http://os-networks.net/
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

require.def('modules/my_mod',[],
function(){

    var urls;

    function round_trip() {
        application.ws.remote('/my_mod/trip/',{},function(response){
            var _average_trips = parseInt(response.data.trips / response.data.server_time);
            $('#trips-total').html(response.data.trips);
            if(response.data.continue == true) {
                $('#trips-second').html(_average_trips);
                return round_trip();
            }
            else {
                $('#trips-second').html('-');
            }
        });        
    }

    function bind_functions() {

        application.functions.my_mod = {
            route: function(uri, push_history) {
                if(urls == undefined) {
                    urls = [
                        [XRegExp('^/my_mod/$'),this.view_my_mod],
                    ];
                }
                application.route_uri_to_mod_function(uri, urls, push_history);
            },

            view_my_mod: function() {
                application.ws.remote('/my_mod/',{},function(response){
                    application.functions.ui.transition(response.data.dom.main, $('.main'));
                });
            },
            //function that takes care of sending our message to the hwios server
            notify: function(kwargs) {
                var _text = $('#textarea-my_mod').val();
                application.ws.remote('/my_mod/notify/',{text: _text},function(response){
                   $('#message-status').html(response.data.sent+' characters sent to '+response.data.clients+' others!');
                });
            },
            trip: function(kwargs){
                round_trip();
            }
        }
    }

    function bind_events() {

    }

    function bind_ws() {
        //Registers method for sending messages from HWIOS to here using an url
        application.ws.method('^/my_mod/message/$', function(kwargs){
            console.log(kwargs);
            $('#latest-message').html(kwargs.data.text);
        });
        application.ws.method('^/my_mod/notify_leave/$', function(kwargs){
            $('online_profile').empty();
            $.each(kwargs.data.online, function(idx, value){
                $('online_profile').append('<li>'+value+'</li>');
            });
            
        });
    }

    function unbind_events() {
        $(".main").undelegate("#blog-content a", "click");
    }

    return {
        init: function(uri, push_history) {
            bind_functions();
            bind_events();
            bind_ws();
            application.functions.my_mod.route(uri, push_history);            
            return 'my_mod';
        },
        load: function(uri, push_history) {
            bind_events();
            application.functions.my_mod.route(uri, push_history);
        },
        clean_up: function(){
            //remove unneeded dom parts when module is left
        }
    }
});
