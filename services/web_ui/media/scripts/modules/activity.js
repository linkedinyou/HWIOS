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
require.def('modules/activity',[
],function(){
    
    var post_rowclass = 0, profile_rowclass = 0, deliver_rowclass = 0;

    function bind_ws() {
        application.ws.method('^/data/activity/create/$', function(params){
            if($('#no-entries').length > 0){
                $('#no-entries').remove();
            }
            $('#activity-text').prepend(params.data.dom.activity);
            $('#activity-text > div:first-child').hide().fadeIn(800);
        });
    }

    function bind_events() {
        $(document).bind('WS_ONLINE', function(event) {
            application.ws.remote('/data/activity/',{},function(response){
                application.functions.ui.transition(response.data.dom.activity, $('#activity-text'));
            });
        });

    }

    return {

        init:function() {
            bind_events();
            $('.activity-loading').remove();
            bind_ws();
            return 'activity';
        }
    }
});