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

(function($){

function RTE(opts) {
    rte = this;
    rte.mh = {timer: 0, offset:[],size:[],ctrl: false, element: {}};
    rte.opts = opts;
    rte.finder = [];
    var last_range;
    rte._state_commands = ['bold','italic','underline','strikethrough','subscript','superscript','insertOrderedList','insertUnorderedList',
 'justifyLeft','justifyCenter','justifyRight','fontSize'];
    rte.editor_container = $(opts.editor_element);
    rte.editor_container.html("\
        <div id='rte-toolbar'>\
        <button type='button' class='rte-icon' id='rte-icon-bold'></button>\
        <button type='button' class='rte-icon' id='rte-icon-italic'></button>\
        <button type='button' class='rte-icon' id='rte-icon-underline'></button>\
        <button type='button' class='rte-icon' id='rte-icon-strikethrough'></button>\
        <button type='button' class='rte-icon rte-button-no-state' id='rte-icon-outdent'></button>\
        <button type='button' class='rte-icon rte-button-no-state' id='rte-icon-indent'></button>\
        <button type='button' class='rte-icon' id='rte-icon-subscript'></button>\
        <button type='button' class='rte-icon' id='rte-icon-superscript'></button>\
        <button type='button' class='rte-icon rte-button-no-state' id='rte-icon-insertHorizontalRule'></button>\
        <button type='button' class='rte-icon' id='rte-icon-insertOrderedList'></button>\
        <button type='button' class='rte-icon' id='rte-icon-insertUnorderedList'></button>\
        <button type='button' class='rte-icon' id='rte-icon-justifyLeft'></button>\
        <button type='button' class='rte-icon' id='rte-icon-justifyCenter'></button>\
        <button type='button' class='rte-icon' id='rte-icon-justifyRight'></button>\
        <button type='button' class='rte-icon rte-button-no-state' id='rte-icon-removeFormat'></button>\
        <button type='button' class='rte-icon rte-selection rte-icon-custom rte-button-no-state rte-icon-inactive' id='rte-icon-createLink'></button>\
        <button type='button' class='rte-icon rte-icon-custom rte-button-no-state' id='rte-icon-insertImage'></button>\
        <select id='rte-value-fontSize'>\
        <option value='select' selected='selected'>Font Size</option>\
        <option value='1'>Smallest</option>\
        <option value='2'>Smaller</option>\
        <option value='3'>Small</option>\
        <option value='4'>Medium</option>\
        <option value='5'>Large</option>\
        <option value='6'>Larger</option>\
        <option value='7'>Largest</option>\
        </select>\
        </div>\
        <div class='rte-contenteditable'></div>");
    //move id from container to actual contenteditable
    var _id = rte.editor_container.attr('id');
    $('.rte-contenteditable').attr('id', _id);
    $('.rte-contenteditable').bind('paste', function(e) {
        console.log(e);
        
    });
    rte.editor_container.attr('id', _id+'_container');
    rte.editor = $('.rte-contenteditable');
    var _hiddenfield_content = $('#id_'+_id).val();
    rte.editor.html(_hiddenfield_content);        
    rte.editor.attr('contenteditable',true);
    rte.editor.focus();
    rte._bind_handlers();
}

RTE.prototype.get_html = function(){
    return $(rte.editor).html();
}

RTE.prototype.set_html = function(content){
    $(rte.editor).html(content);
}

RTE.prototype.focus = function(){
    $(rte.editor).focus();
}

RTE.prototype._bind_handlers = function() {

    //Styling button handlers
    $('.rte-button-no-state').unbind('webkitAnimationEnd').bind('webkitAnimationEnd', function(){this.style.webkitAnimationName = '';});
    //Toolbar button click handling
    $('#rte-toolbar > button').unbind('click').click(function() {
        var command = $(this).attr('id').split('-')[2];
        //custom function, which requires more than executing the command
        if($(this).hasClass('rte-icon-custom')){
            if(!$(this).hasClass('rte-icon-inactive')){
            rte._handle_execCommand(command);
            }            
        }
        //simple command, just parse
        else {
            console.log(command);
            document.execCommand(command, false, null);
            
        }
        //Basic button state styling
        if($(this).hasClass('rte-icon-inactive')){
           // $(rte.editor).attr('contenteditable',false);
        }
        //Basic button state styling
        if($(this).hasClass('rte-icon-active')){
            $(this).removeClass('rte-icon-active');            
        }
        //animation for buttons without state
        if($(this).hasClass('rte-button-no-state')){
            $(this).css('webkitAnimationName','push_button');            
        }
        //animation for buttons with state
        else {
            $(this).addClass('rte-icon-active');
        }
        //rte._query_toolbar_state();
    });
    //Selection box changes
    $('#rte-toolbar > select').unbind('change').change(function() {
        var command = $(this).attr('id').split('-')[2];
        document.execCommand(command, false, $(this).val());
        $(this).val('select');
    });
    
    //Toolbar state handlers, bound to the contenteditable
    this.editor.unbind('keydown selectstart mouseup focusout').bind('keydown selectstart mouseup mousedown focusout drag', function(event){
        if(event.type == 'mouseup') {
            rte.editor.attr('contenteditable',true);
        }
        else if(event.type == 'focusout') {
            rte._query_toolbar_state(event);
        }
        else if(event.type == 'selectstart') {
            $("img").trigger('rm-handler');
            window.setTimeout(function() {
                rte._query_toolbar_state(event);
                },300);
            //rte._query_toolbar_state(event);
        }
        else if(event.type == 'mousedown') {
            //prevent normal behaviour
            if(event.ctrlKey == true) {
                event.preventDefault();
            }
        }
        else if(event.type == 'drag') {

        }
        else {
            window.setTimeout(function() {
                rte._query_toolbar_state(event);                
            },0);
        }
    });

//INLINE IMAGE RESIZING*****************************************
    function resize_image(element, offset) {
        var cur_width = element.width();
        var cur_height = element.height();        
        if(offset[0] >= offset[1]){
            var speed = 0.5 * Math.abs(offset[0] - cur_width/2);
            if(offset[0] >= (cur_width / 2)){
                element.width(Math.floor(cur_width+speed));
            }
            else {
                element.width(Math.floor(cur_width-speed));
            }
        }
        else {
            var speed = 0.5 * Math.abs(offset[1] - cur_height/2);
            if(offset[1] >= (cur_height / 2)){
                element.width(Math.floor(cur_height+speed));
            }
            else {
                element.width(Math.floor(cur_height-speed));
            }
        }
    }

    $(".rte-contenteditable").delegate('img','contextmenu', function(event){
        event.preventDefault();
        event.stopPropagation();
        rte._show_img_context(event);
    });

    $(".rte-contenteditable").delegate('img','mouseover mouseout mouseup mousedown mousemove',function(event){
        rte.mh.element = $(this);
        //R-Mouse button clicked
            if(rte.mh.ctrl) {
                if(!rte.mh.element.hasClass('image-resizable')){
                    rte.mh.element.addClass('image-resizable');
                }
            }
            else {
                if(rte.mh.element.hasClass('image-resizable')) rte.mh.element.removeClass('image-resizable');
            }
            if(event.offsetX != undefined) {
                rte.mh.offset = [event.offsetX, event.offsetY];
            }
            var current_size = [event.target.clientWidth,event.target.clientHeight];
            if(event.type == 'mouseout' || event.type == 'mouseup'){
                clearTimeout(rte.mh.timer);
                rte.mh.ctrl = false;
                rte.mh.element.removeClass('image-resizable');
            }
            else if(event.type == 'mousemove') {

                rte.mh.offset = [event.offsetX, event.offsetY];
                rte.mh.ctrl = event.ctrlKey;
                //
            }
            else if(event.type == 'mousedown') {
                if(rte.mh.ctrl) resize_image(rte.mh.element, rte.mh.offset);
                rte.mh.timer = setTimeout(function(){
                    rte.mh.element.trigger('mousedown', rte.mh.offset);},0);
            }

    });

    //**********************************************************************************************************

    //set default text properties
    document.execCommand('justifyLeft', false, null);
    //document.execCommand('fontSize', false, 2);
    //rte._query_toolbar_state();
}

RTE.prototype._show_img_context = function(event){
    if($('.image-context-menu').length == 0) {
        var _content = '<div class="image-context-menu">\
        <div id="rte-float-left"><span class="ui-icon ui-icon-arrowstop-1-w"></span>Float left</div>\
        <div id="rte-float-right"><span class="ui-icon ui-icon-arrowstop-1-e"></span>Float right</div>\
        <div id="rte-float-clear"><span class="ui-icon ui-icon-arrowstop-1-e"></span>Clear Float</div>\
        </div>';
        $('body').append(_content);
        $('.image-context-menu').bind('mouseleave click',this._hide_img_context);
        $('.image-context-menu > div').bind('click',this._select_img_ctx_option);
    }
    $('.image-context-menu').css('left',event.clientX - 5);
    $('.image-context-menu').css('top',event.clientY - 5);
    $('.image-context-menu').css('display','block');
}

RTE.prototype._hide_img_context = function(event){
    $('.image-context-menu').css('display','none');
}

RTE.prototype._select_img_ctx_option = function(event){
    switch(event.srcElement.id){
        case 'rte-float-left':
            $(rte.mh.element).addClass('rte-float-left');
            $(rte.mh.element).removeClass('rte-float-right');
        break;
        case 'rte-float-right':
            $(rte.mh.element).addClass('rte-float-right');
            $(rte.mh.element).removeClass('rte-float-left');
        break;
        case 'rte-float-clear':
            $(rte.mh.element).removeClass('rte-float-right');
            $(rte.mh.element).removeClass('rte-float-left');
        break;
    }
}

RTE.prototype._handle_execCommand = function(command){
    switch(command){
        case 'createLink':
            //rte._has_selection();
            var _dialogdata = "<form>\
                <p><label for='id_url'>Unique Resource Locator</label><input id='id_url' type='text' name='url'/></p>\
                </form>\
            ";
            var i18nButtons = {};
            i18nButtons[gettext('Cancel')] = function() {
                $(this).dialog("destroy");
                $register = undefined;
                //rte.editor.focus();
                //$(rte.editor).attr('contenteditable',false);
                console.log('should NOT have selection!!!');
                rte._query_toolbar_state();
            };
            i18nButtons[gettext('Insert')] = function() {
                var form_data = $("form:visible").serializeObject();
                $(this).dialog("destroy");
                selection.addRange(range);
                document.execCommand('createLink', false, form_data.url);
            };
            var selection = window.getSelection();
            var range = rte._get_selection();
            
            var _dialog = $(_dialogdata).dialog({
                autoOpen: true,position:"center",width:450,
                title: '<span class="ui-icon ui-icon-person"></span><span>'+gettext('Insert URL')+'</span>',
                resizable: false,draggable: true,modal: true, buttons: i18nButtons
            });
           
        break;
        case 'insertImage':
            $('#rte-finder').remove();
            $('body').append($('<div id="rte-finder"/>'));
            rte.finder = $('#rte-finder').elfinder({
                url : '/misc/elconnector/',
                dialog: {autoOpen: true, width: 950, modal: true,resizable:false,
                title:'<span class="ui-icon ui-icon-document"></span><span>File Manager.</span>', zIndex: 400001},
                editorCallback: function(urls) {
                    rte._get_focus();
                    $.each(urls, function(idx, url){
                    document.execCommand('insertHTML', true, '<img class="rte-image" src="'+url+'" />');
                    });                    
                },
                closeOnEditorCallback: true,
                docked: false,
                selectMultiple:true
            });
        break;
    }
}

RTE.prototype._query_toolbar_state = function(event) {
    //State can be checked against caret position
    $.each(this._state_commands,function(idx, command){
        if(document.queryCommandState(command) == true) {$('#rte-icon-'+command).addClass('rte-icon-active');}
        else {$('#rte-icon-'+command).removeClass('rte-icon-active');}
    });
    if(event != undefined) {
        //Checking state against selection
        var selection = rte._has_selection();
        if(selection != undefined && (event.type != 'focusout' && event.type !='mouseup')) {
            //regular selection
            if(selection != -1){
                console.log('REENABLE');
                $.each($('.rte-selection'), function(idx, _button){
                    $(_button).removeClass('rte-icon-inactive');
                });
            }
            //caret only
            else {
                $.each($('.rte-selection-caret-only'), function(idx, _button){
                    $(_button).removeClass('rte-icon-inactive');
                });
                $.each($('.rte-selection'), function(idx, _button){
                    $(_button).addClass('rte-icon-inactive');
                });
            }
        }
        //no selection, disable all selection-based buttons
        else {
            if(event.type == 'mouseup') {
                $.each($('.rte-selection-caret-only'), function(idx, _button){
                    $(_button).removeClass('rte-icon-inactive');
                });
                $.each($('.rte-selection'), function(idx, _button){
                    $(_button).addClass('rte-icon-inactive');
                });
            }
            if(event.type == 'focusout') {                //make buttons inactive

            }
        }
        //options that require a selection'
    }
    else {
    //console.log(window.getSelection());
    }
}

RTE.prototype._inactivate_buttons = function() {
    $.each($('.rte-selection'), function(idx, _button){
        $(_button).addClass('rte-icon-inactive');
    });
}

RTE.prototype._get_selection = function() {
    var selection = window.getSelection();
    range = selection.getRangeAt(0);
    return range;
}

RTE.prototype._get_focus = function() {
    if(last_range != undefined) {
    var range = last_range;
    }
    else {
        var range = document.createRange();
    }
    //range.selectNodeContents($(this.editor).get(0));
    selection = window.getSelection();
    //selection.removeAllRanges();
    selection.addRange(range);
}

//Checks whether there is at least a selection of one char or more
RTE.prototype._has_selection = function() {
    var selection = window.getSelection();
    //Is the caret focussed on the editor at all?
    if(selection != undefined) {
        if(selection.anchorNode !== null){
            last_range = selection.getRangeAt(0);
        }
        //same line
        if(selection.anchorNode == selection.focusNode) {
            //no selection, only caret positioned
            if(selection.anchorOffset != selection.focusOffset) {return true;}
            //Caret yes, selection no
            else {
                return -1;
            }
        }
        //selection spans multiple lines.
        else {return true;}
    }
    else {return false;}
}

$.extend({
    rte_settings: {
        editor_element:''
    },
    rte: function(editor_element, params) {
    opts = $.extend($.rte_settings, params);
    opts['editor_element'] = editor_element;
    ce = new RTE(opts);
    return ce;
    }
});
    
})(jQuery);