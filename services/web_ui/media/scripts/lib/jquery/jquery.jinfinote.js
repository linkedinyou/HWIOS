/** Based on "Collaborative editor example code from Simon Veith"
 * @author  Simon Veith
 * @license Mit Style License
 *
 * JQuerified for the HWIOS project
 * 
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
(function($){

    var ce;  
    
    function CollabEditor(opts) {
        ce = this;
        ce.remote_cursors = {};
        ce.editor_colors = {};
        ce.suppress_change = false;
        ce.opts = opts;
        ce._initialized = false;
        ce.log = [];
        ce.cursor_history = [];

        ce._state = new State();
        //Init request
        ce.opts['ws_handler'].remote(ce.opts['ws_connect'],{},function(response){
            ce._localUser = parseInt(response.data.uid);
            $.each(response.data.online, function(idx, user){
                if(user.id == ce._localUser){
                ce._localColor = user.color;
                }
            });
            //in some cases, only a create page is shown and none created. Do not proceed in that case.
            if(!('log' in response.data.page)) {
                ce.opts['init'](response.data, null);
                return false;
            }
            else {
                ce._state.buffer = new Buffer([new Segment(0, response.data.page.state[1])]); 
                ce._state.vector = new Vector(response.data.page.state[0]);                
                ce.sync_log(response.data.page.log[1], function(){
                    //arbitrary init function, in which user can customize stuff
                    var init_response = ce.opts['init'](response.data);
                    if('mode' in ce.opts) {
                        ce.init_code_editor(init_response, response.data);
                    }
                    else {
                        ce.init_code_listener(init_response, response.data);
                        
                    }
                });
                if('mode' in ce.opts) {
                ce.update_online(response.data.online);
                }
            } 
            ce._prevValue = ce._state.buffer.toString();            
            if (isNaN(this._localUser) && ce.opts['mode'] == 'edit') {return false;}
            ce._initialized = true;
            $(document).trigger('infinote_synced',[ce._state.log.length, , ce._textarea]);
        }); 
        return true;
    }
    
    //SYNC THE INCOMING LOG TO THE DOCUMENT STATE
    CollabEditor.prototype.sync_log = function(log_array, callback) {
        $.each(log_array, function (index,params) {
            switch(params[0]) {
            case "i":
                var params = params[1];
                var buffer = new Buffer([new Segment(params[0], params[3])]);
                var operation = new Operations.Insert(params[2], buffer);
                var request = new DoRequest(params[0], new Vector(params[1]), operation);
                var executedRequest = ce._state.execute(request);
            break;
            case "d":
                var params = params[1];
                var operation = new Operations.Delete(params[2], params[3]);
                var request = new DoRequest(params[0], new Vector(params[1]), operation);
                var executedRequest = ce._state.execute(request);
            break;
            case "u":
                var params = params[1];
                var request = new UndoRequest(params[0], new Vector(params[1])); 
                var executedRequest = ce._state.execute(request);          
            break;
            default:
            break;
            }
        }); 
        callback();
    }
    
    
    //Show the document's editors
    CollabEditor.prototype.update_online = function(online) {
        $('.infinote-online').empty();
        $.each(online, function(index, user) {
            ce.editor_colors[user.id] = user.color;
            ce._set_cursor_color(user.id, user.color);
            var participant_line;
            if(user.id == application.settings.user.id) {
                participant_line = '<div id="infinote-participant-'+user.id+'" data-id="'+user.id+'" class="infinote-participant"><div class="infinote-participant-color"></div><div class="infinote-participant-name">'+user.name+' ('+gettext('You')+')</div></div>';
            }
            else {
                participant_line = '<div id="infinote-participant-'+user.id+'" data-id="'+user.id+'" class="infinote-participant"><div class="infinote-participant-color"></div><div class="infinote-participant-name">'+user.name+'</div></div>';
            }
            $('.infinote-online').append(participant_line);
            $('#infinote-participant-'+user.id+' > .infinote-participant-color').css('background-color',user.color);
        });
        //clean out left-over cursors and selections
        var match = false;
        $.each(ce.remote_cursors, function(idx, value){
            //match each remote cursor against online list.
            $.each(online, function(index, user) {
                //online user is in remote cursor list
                if(user.id == idx) {
                    match = true;

                }
            });
            //user in remote_cursor has no match in online list. delete this user
            if(!match){
                ce.delete_remote_cursor(idx);
            }
        });
        ce.update_cursors();
    }    
    
    //UNBIND HANDLERS
    CollabEditor.prototype.disconnect = function() {
        this.opts['ws_handler'].remote(this.opts['ws_disconnect'],{},function(response){});
    }    
   
    //Listen mode, not much to do unless you want to make it fancier
    CollabEditor.prototype.init_code_listener = function(init_response, data) {}
   
    
    //Editor mode. Initialize codemirror and setup events
    CollabEditor.prototype.init_code_editor = function(init_response, data) {
        ce.dmp = new diff_match_patch();        
        ce._container = $(init_response.editor_element);
        $(ce._container).append('<div class="infinote-online"></div><div id="infinote-textarea"><textarea></textarea></div>');
        ce.editor = CodeMirror.fromTextArea($('#infinote-textarea textarea').get(0), {
            lineNumbers: true,
            theme: "default",
            mode: ce.opts['mode'],
            smartHome:false,
            enterMode:"flat",
            onCursorActivity: function(cm, tc){
                //handle exclusive cursor movement
                if(tc == false){
                    var params = {id:ce._localUser, cursor:cm.getCursorRange()};
                    $('span.CodeMirror-selected').css('background-color',ce.editor_colors[ce._localUser]);                    
                    ce.opts['ws_handler'].remote(ce.opts['ws_caret'], {params: params},function(response){});
                }
            },
            onChange: this._handle_local_operation,
            onFocus: function(cm){
                var params = {id:ce._localUser, cursor:cm.getCursorRange()};
                params.cursor.focus = true;
                ce.opts['ws_handler'].remote(ce.opts['ws_caret'], {params: params},function(response){});
            },
            onBlur: function(cm){
                var params = {id:ce._localUser, cursor:cm.getCursorRange()};
                params.cursor.blur = true;
                ce.opts['ws_handler'].remote(ce.opts['ws_caret'], {params: params},function(response){});
            },
            onKeyEvent: function(cm, e) {
                if(e.type == 'keydown'){
                    //capture ctrl-z
                    if (e.ctrlKey){
                        if (e.keyCode == 90) {
                            ce.suppress_change = true;
                            e.preventDefault();
                            ce._handle_local_undo();
                        }
                    }
                    //all regular text-input
                    else {
                        ce.suppress_change = false;
                        ce.early_selection = cm.getSelection();
                        ce.early_cursor = cm.getCursor();
                    }
                }
            }
        });
        //set the local cursor color
        $('.CodeMirror-cursor').css('border-left','3px solid '+ce._localColor);
        //setting editor value triggers onchange. ignore this to prevent state flood
        ce.suppress_change = true;
        this.editor.setValue(ce._state.buffer.toString());
        ce._prevValue = ce._state.buffer.toString();
        ce.suppress_change = false;
    }


    CollabEditor.prototype._handle_local_undo = function() {
        ce.suppress_change = true;
        var request = new UndoRequest(ce._localUser, ce._state.vector);   
        if (ce._state.canExecute(request)) {
            var executedRequest = ce._state.execute(request);
            ce.opts['ws_handler'].remote(ce.opts['ws_undo'], [ce._localUser,request.vector.toString()],function(response){});
            ce.editor.setValue(ce._state.buffer.toString());
            ce.editor.setCursor(ce.early_cursor);
            ce.opts['ws_handler'].remote(ce.opts['ws_caret'], {params: {id:ce._localUser, cursor:ce.early_cursor}},function(response){});
            ce._prevValue = ce._state.buffer.toString();
            $(document).trigger('infinote_update',[]);
        }
    }


    CollabEditor.prototype._handle_local_operation = function(cm, tc) {
        if (ce.suppress_change == true) {
            return;
        }
        else {
            ce.suppress_change == true;
            var diffs = ce.dmp.diff_main(ce._prevValue, ce.editor.getValue());
            var offset = 0;
            for (var diffIndex = 0; diffIndex < diffs.length; diffIndex++) {
                var diffData = diffs[diffIndex];
                var diffType = diffData[0];
                var diffText = diffData[1];

                if (diffType == 1) {
                    // Text has been inserted. Create an insert request out of the change.

                    var buffer = new Buffer([new Segment(ce._localUser, diffText)]);
                    var operation = new Operations.Insert(offset, buffer);
                    var request = new DoRequest(ce._localUser, ce._state.vector, operation);
                    var _cursor = {from: ce.early_cursor, to: ce.editor.getCursor()}
                    var params = [ce._localUser,request.vector.toString(),offset, diffText, _cursor];
                    var executedRequest = ce._state.execute(request);
                    if (ce._state.canExecute(request)) {
                        ce.opts['ws_handler'].remote(ce.opts['ws_insert'], params, function(response){
                            ce.update_cursors();
                        });
                    }
                    offset += diffText.length;
                } else if (diffType == -1) {
                    // Text has been removed.
                    var buffer = ce._state.buffer.slice(offset, offset + diffText.length);
                    var operation = new Operations.Delete(offset, buffer);
                    var request = new DoRequest(ce._localUser, ce._state.vector, operation);
                    var _cursor = {from: tc.from, to: tc.to}
                    var params = [ce._localUser,request.vector.toString(),offset, diffText.length, _cursor];
                    var executedRequest = ce._state.execute(request);
                    if (ce._state.canExecute(request)) {
                        ce.opts['ws_handler'].remote(ce.opts['ws_delete'], params, function(response){
                        });
                    }
                } else {
                    offset += diffText.length;
                }                
            }
            ce._prevValue = ce._state.buffer.toString();
            $(document).trigger('infinote_update',[]);
            ce._check_state();
        }
    }

    CollabEditor.prototype._hide_remote_cursor = function(user_id){
        $('#rc_'+user_id).removeClass('remote-cursor-focused');
    }

    CollabEditor.prototype._show_remote_cursor = function(user_id){
        $('#rc_'+user_id).addClass('remote-cursor-focused');
    }


    CollabEditor.prototype._set_cursor_color = function(user_id, color){
        $('#rc_'+user_id).css('border-left','3px solid '+color);
    }

    //Takes cursor as parameter
    CollabEditor.prototype._set_remote_cursor = function(user_id, cursor, force_caret){

        if (!(user_id in ce.remote_cursors)) {
            ce.remote_cursors[user_id] = cursor;
            $('body').append("<span id='rc_"+user_id+"' class='remote-cursor'></span>");
            ce._set_cursor_color(user_id, ce.editor_colors[user_id]);
            ce.remote_cursors[user_id].node = $('#rc_'+user_id).get(0);
        }
        else {
            ce.remote_cursors[user_id].from.line = cursor.from.line;
            ce.remote_cursors[user_id].from.ch = cursor.from.ch;
            ce.remote_cursors[user_id].to.line = cursor.to.line;
            ce.remote_cursors[user_id].to.ch = cursor.to.ch;
        }
        //cursor is always from/to. This may not be equal, but not wanting to result in a selection(insert/delete ops).
        //force_caret forces the cursor to be a caret at some position
        if(force_caret !== undefined){
            ce.remote_cursors[user_id].fc = force_caret;
        }
        else {
            delete ce.remote_cursors[user_id].fc;
        }
        ce.update_cursors();
    }

    CollabEditor.prototype.delete_remote_cursor = function(user_id){
        $(ce.remote_cursors[user_id].node).remove();
        if('rsc' in ce.remote_cursors[user_id]){
            ce.remote_cursors[user_id].rsc();
        }
        delete ce.remote_cursors[user_id];
        ce.update_cursors();
    }


    CollabEditor.prototype.update_cursors = function(){
        $.each(ce.remote_cursors, function(user_id, cursor){
            if('rsc' in cursor){
                ce.remote_cursors[user_id].rsc();
            }
            //actual cursor, not a selection
            if((cursor.from.line == cursor.to.line) && (cursor.from.ch == cursor.to.ch)){
                ce.editor.addWidget(cursor.from, cursor.node,false);
            }
            else if('fc' in cursor){
                ce.editor.addWidget(cursor.fc, cursor.node,false);
            }
            //selection
            else {
                ce.remote_cursors[user_id].rsc = ce.editor.markText(cursor.from, cursor.to, 'remote-selection-'+user_id);
                $('.remote-selection-'+user_id).css('background-color',ce.editor_colors[user_id]).addClass('remote-selection');
            }
        });
    }


    CollabEditor.prototype.textpos_to_linepos = function(offset) {
        var lines = this.editor.getValue().split('\n');
        var row = 0;
        $.each(lines,function(idx, line){
            if (offset <= line.length) {
            row = idx;
            return false;
            }
            //for each line, substract line-length and delimiter
            offset -= line.length + 1;
            row = idx;
        });
        return {line: row,ch: offset}
    }


    CollabEditor.prototype._check_state = function(cursor) {
        var editorText, otText,  total_length;
        editorText = ce.editor.getValue();
        otText = ce._state.buffer.toString();
        //console.log(editorText);
        if (editorText != otText) {
            ce.suppress_change = true;
            var _cursor = ce.editor.getCursor();
            ce.editor.setValue(ce._state.buffer.toString());
            console.warn('Editor state differs from ot-state(ot-length:'+otText.length+',ce-length:'+editorText.length+'). Updating editor from state buffer!');
            //var diffs = ce.dmp.diff_main(otText, editorText);
            //console.log(diffs);
            ce.editor.setCursor(_cursor);
            ce.suppress_change = false;
        }
    }
    

    CollabEditor.prototype._handle_remote_insert = function(params) {
        ce.suppress_change = true;
        var buffer = new Buffer([new Segment(params[0], params[3])]);
        var operation = new Operations.Insert(params[2], buffer);
        var request = new DoRequest(params[0], new Vector(params[1]), operation);
        if (ce._state.canExecute(request)) {
            var executedRequest = ce._state.execute(request);
            //insert text directly at remote cursor position
            if(ce.editor !== undefined) {
            ce.editor.replaceRange(params[3],params[4].from, params[4].from);
            ce._set_remote_cursor(params[0], params[4], params[4].to);
            }
        }
        $(document).trigger('infinote_update',[]);
        ce._prevValue = ce._state.buffer.toString();
        ce.suppress_change = false;
    }


    CollabEditor.prototype._handle_remote_delete = function(params) {
        ce.suppress_change = true;
        var operation = new Operations.Delete(params[2], params[3]);
        var request = new DoRequest(params[0], new Vector(params[1]), operation);
        if (ce._state.canExecute(request)) {
            var executedRequest = ce._state.execute(request);
            if(ce.editor !== undefined){
                ce.editor.replaceRange("",params[4].from, params[4].to);
                ce._set_remote_cursor(params[0], params[4], params[4].from);
            }
        }
        ce._prevValue = ce._state.buffer.toString();
        $(document).trigger('infinote_update',[]);
        ce.suppress_change = false;
    }


    CollabEditor.prototype._handle_remote_undo = function(params) {
        ce.suppress_change = true;
        var request = new UndoRequest(params[0], new Vector(params[1]));
        if (ce._state.canExecute(request)) {
            var executedRequest = ce._state.execute(request);
            ce.editor.setValue(ce._state.buffer.toString());
        }
        
        //console.log(ce._state.buffer.toString());
        //ce._prevValue = ce._state.buffer.toString();
        $(document).trigger('infinote_update',[]);
        ce.suppress_change = false;
    }



$.extend({
    infinoteSettings: {
        ws_connect: '',
        ws_disconnect: '',
        ws_insert: '',
        ws_delete: '',
        ws_undo: '',
        ws_caret: '',
        cb_insert:'',            
        cb_delete:'',            
        cb_undo:'',
        cb_caret:'',
        editor:'code',
        init:'',

    },    
    jinfinote: function(ws_handler, params) {
    opts = $.extend($.infinoteSettings, params);
    opts['ws_handler'] = ws_handler;
    ce = new CollabEditor(opts);
        opts['ws_handler'].method(opts['cb_insert'],function(request){
            ce._handle_remote_insert(request['params']);
            if(ce.editor !== undefined) {ce._check_state();}
        });
        opts['ws_handler'].method(opts['cb_delete'],function(request){
            ce._handle_remote_delete(request['params']);
            if(ce.editor !== undefined) {ce._check_state();}
        });
        opts['ws_handler'].method(opts['cb_undo'],function(request){
            ce._handle_remote_undo(request['params']);
            if(ce.editor !== undefined) {ce._check_state();}
        });
        //{id:userid,cursor:{line,ch}}
        opts['ws_handler'].method(opts['cb_caret'],function(request){
            ce._set_remote_cursor(request['id'],request['cursor']);
            if ('blur' in request.cursor){
                ce._hide_remote_cursor(request['id']);
            }
            else if('focus' in request.cursor){
                ce._show_remote_cursor(request['id']);
            }
            
        });
    return ce;
    }   
});
})(jQuery);

