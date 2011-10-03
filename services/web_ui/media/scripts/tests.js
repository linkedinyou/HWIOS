define('tests',[
'order!lib/jquery/jquery.ws',
'order!lib/jquery/jquery.ui',
'lib/tools/processing',
'lib/jinfinote/diff_match_patch',
'lib/tools/json',
'lib/tools/jit',
'lib/jquery/jquery.animate',
'order!lib/jquery/jquery.class',
'order!lib/jquery/jquery.color',
'order!lib/jquery/jquery.cpaint',
'lib/tools/xregexp',
'lib/jinfinote/jinfinote',
'lib/jquery/jquery.jinfinote',
'lib/openlayers/OpenLayers',
'lib/jquery/jquery.datatables',
'lib/jquery/jquery.serialobj',
'modules/page'],
function(){
    var ws;
    var editor;
    
    function init_websocket() {
        ws_url = 'ws://192.168.1.101/ws';
        ws = $.websocket(ws_url, {
                open: function() {                    
                    $('body').append('<div>Test 1: Websocket opened</div>');
                    //test2
                    $('body').append('<div>Test 2: Infinote consistency</div>');
                    initEditor('69be6701-217b-4520-b9cb-df954bd97c5d');
                },
                close: function() {

                },
                message_cb: function(type, data){

                },
        });
    }
    
    function test_infinote() {
    console.log('running insertion tests');
            $(document).bind('infinote_update', function(e) {
                
            });
    //var e = jQuery.Event("keydown");
    //e.which = 'a';
    //$("input").trigger(e);
    for(var i=1; i < 20; i++) {
        $('#l'+i).html('\nfoobar, testing...'+i+'\n');
        editor._handle_local_operation();
        editor._update_tam(editor._state.buffer.toString());        
    }
    console.log($('.infinote-editor-textarea').html());
    ws.remote('/views/plasmoids/delete/',{params:{'69be6701-217b-4520-b9cb-df954bd97c5d':'on'}},function(response){
    });
    }
            
    function initEditor(plasmoid_uuid) {
        editor = $.jinfinote(ws, {
        ws_connect:'/views/plasmoids/'+plasmoid_uuid+'/edit/',
        ws_disconnect:'/views/plasmoids/'+plasmoid_uuid+'/disconnect/',
        ws_insert:'/data/plasmoids/'+plasmoid_uuid+'/insert/',
        ws_delete:'/data/plasmoids/'+plasmoid_uuid+'/delete/',
        ws_undo:'/data/plasmoids/'+plasmoid_uuid+'/undo/',
        ws_caret:'/data/plasmoids/'+plasmoid_uuid+'/caret/',
        cb_insert:'^/data/plasmoids/(?<plasmoid_uuid>[^/]+)/insert/$',      
        cb_delete:'^/data/plasmoids/(?<plasmoid_uuid>[^/]+)/delete/$',
        cb_undo:'^/data/plasmoids/(?<plasmoid_uuid>[^/]+)/undo/$',
        cb_caret:'^/data/plasmoids/(?<plasmoid_uuid>[^/]+)/caret/$',   
        editor:'code',
        init: 
            function(data) {
                console.log('editor init...');
                $('body').append('<div id="plasmoid-editor" class="infinote-editor"</div>');
            console.log(data.page);
            $('.infinote-editor-textarea').text(data.page.state[1]);                     
            $(document).bind('infinote_synced', function(e) {
                test_infinote();
            });
            return $('#plasmoid-editor');            
            }
        });
    }
    
    return {             
        init:function() {
            //test 1
            init_websocket();
            
        },

    }    
});