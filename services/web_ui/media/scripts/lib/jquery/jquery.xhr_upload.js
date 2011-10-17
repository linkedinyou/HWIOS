/** Based on "Basic upload manager for single or multiple files (Safari 4 Compatible)"
* @author  Andrea Giammarchi
* @blog    WebReflection [webreflection.blogspot.com]
* @license Mit Style License
*
* Modified for the HWIOS project
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

(function( $ ){
    var total_size = 0;
    var opts = {}
    var methods = {
        init : function(options) {
            var defaults = {
            url: '',
            submit:'',
            cancel:'',
            select_box:'',
            formats:[],
            progress:'',
            };
            opts = $.extend(defaults, options);
            this.each(function() {
                var input = $(this).get(0);
                $(opts['progress']).html('<div id="upload-progressbar"></div><div id="upload-status-text"></div>');
                $('#upload-progressbar').progressbar({ value: 0,disabled:true});

                $(this).change(function() {
                    total_size = 0;
                    var selected_files = ''
                    var enable = false;
                    if(this.files.length > 0) {
                        for(var i=0; i<this.files.length; i++){
                            if($.inArray(this.files[i].fileName.substr(-4,4), opts['formats']) != -1) {
                                total_size += this.files[i].fileSize;
                                selected_files+='<p>'+this.files[i].fileName+'</p>';
                                enable = true;
                            }
                        }
                        if(enable) {$(opts['submit']).removeClass('ui-state-disabled');}
                        else {
                            $(opts['submit']).addClass('ui-state-disabled');
                            var str_formats = '';
                            for(var i=0;i < opts['formats'].length;i++) {
                                if(i != (opts['formats'].length-1)) {str_formats +=opts['formats'][i]+",";}
                                else {str_formats +=opts['formats'][i];}
                            }
                            var _wrong_ft = gettext('Only files with the following extensions are allowed')+': '+str_formats;
                            $("#notify-container").notify("create",'notify-info', {i18n: _wrong_ft});
                        }
                    }
                    else {
                        $(opts['submit']).addClass('ui-state-disabled');
                    }
                    $(opts['select_box']).html(selected_files);
                });
            });	
        },
        send : function(callback) {
            this.each(function() {
                var input = $(this).get(0);
                $(this).attr("disabled", "true");
                $(opts['submit']).addClass('ui-state-disabled');
                $(opts['cancel']).addClass('ui-state-disabled');
                var div = $('#upload-status-text').get(0);
                sendMultipleFiles({                
                    url:opts['url'],
                    formats: opts['formats'],
                    files:input.files,                    
                    onloadstart:function(){
                    div.innerHTML = "Init upload ... ";
                    },                    
                    onprogress:function(rpe){
                    total_progress = parseInt(((this.sent + rpe.loaded) / total_size) * 100);
                    file_progress = parseInt((rpe.loaded / rpe.total) * 100);
                    $('#upload-progressbar').progressbar( "option", "value", total_progress);
                    div.innerHTML = [
                    "Uploading: " + this.file.fileName + " ("+file_progress+"%)",
                    "Sent: " + size(this.sent + rpe.loaded) + " of " + size(total_size)
                    ].join("<br />");
                    },                    
                    onload:function(rpe, xhr){
                    response = JSON.parse(xhr.responseText);
                    callback(response);
                    },                    
                    onerror:function(){
                    div.innerHTML = "The file " + this.file.fileName + " is too big [" + size(this.file.fileSize) + "]";
                    input.removeAttribute("disabled");
                    }
                });
            });
        }
    };

$.fn.xhr_upload = function(method) {
    if ( methods[method] ) {
    return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
    } else if ( typeof method === 'object' || ! method ) {
    return methods.init.apply( this, arguments );
    } else {
    $.error( 'Method ' +  method + ' does not exist on jQuery.xhr_upload' );
    }
}

function size(bytes){   // simple function to show a friendly size
var i = 0;
    while(1023 < bytes){
        bytes /= 1024;
        ++i;
    };
return  i ? bytes.toFixed(2) + ["", " Kb", " Mb", " Gb", " Tb"][i] : bytes + " bytes";
};

var sendFile = 102400000; // maximum allowed file size
                        // should be smaller or equal to the size accepted in the server for each file


// function to upload a single file via handler
sendFile = (function(toString, maxSize){
    var isFunction = function(Function){return  toString.call(Function) === "[object Function]";},
    split = "onabort.onerror.onloadstart.onprogress".split("."),length = split.length;
    return function(handler){
        if(maxSize && maxSize < handler.file.fileSize){
            if(isFunction(handler.onerror))
                handler.onerror();
            return;
        };
        var xhr = new XMLHttpRequest,upload = xhr.upload;
        for(var xhr = new XMLHttpRequest, upload = xhr.upload,i = 0;i < length;i++)
            upload[split[i]] = (function(event){
                return  function(rpe){
                    if(isFunction(handler[event]))
                        handler[event].call(handler, rpe, xhr);
                };
            })(split[i]);
        upload.onload = function(rpe){
            if(handler.onreadystatechange === false){
                if(isFunction(handler.onload))
                    handler.onload(rpe, xhr);
            } else {
                setTimeout(function(){
                    if(xhr.readyState === 4){
                        if(isFunction(handler.onload))
                            handler.onload(rpe, xhr);
                    } else
                        setTimeout(arguments.callee, 15);
                }, 15);
            }
        };
        if($.inArray(handler.file.fileName.substr(-4,4), handler.formats) != -1) {
            xhr.open("POST", handler.url);
            xhr.setRequestHeader("If-Modified-Since", "Mon, 26 Jul 1997 05:00:00 GMT");
            xhr.setRequestHeader("Cache-Control", "no-cache");
            xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
            xhr.setRequestHeader("X-File-Name", handler.file.fileName);
            xhr.setRequestHeader("X-File-Size", handler.file.fileSize);
            xhr.setRequestHeader("Content-Type", "application/octet-stream");
            xhr.send(handler.file);
        }
        return handler;
    };
})(Object.prototype.toString, sendFile);

// function to upload multiple files via handler
function sendMultipleFiles(handler){
    var length = 0;
    for(var i=0; i < handler.files.length; i++) {
        if($.inArray(handler.files[i].fileName.substr(-4,4), handler.formats) != -1) {
        length += 1;
        }
    }
    i = 0,onload = handler.onload;
    handler.total = 0;
    handler.sent = 0;
    while(handler.current < length)
        handler.total += handler.files[handler.current++].fileSize;
    handler.current = 0;
    if(length){
        for(var i=0; i < handler.files.length; i++) {
            if($.inArray(handler.files[i].fileName.substr(-4,4), handler.formats) != -1) {
            handler.file = handler.files[i];
            handler.current = i;
            break;
            }
        }
        sendFile(handler).onload = function(rpe, xhr){
            if(++handler.current < length){
                handler.sent += handler.files[handler.current - 1].fileSize;
                for(var i=handler.current; i < handler.files.length; i++) {
                    if($.inArray(handler.files[i].fileName.substr(-4,4), handler.formats) != -1) {
                        handler.file = handler.files[i];
                        handler.current = i;
                        break;
                    }
                }
                sendFile(handler).onload = arguments.callee;
            } else if(onload) {
                handler.onload = onload;
                handler.onload(rpe, xhr);
            }
        };
    }else {
        var formats = '';
        for(var i=0;i < handler.formats;i++) {
            if(i != (handler.formats.length-1)) {formats +=handler.formats[i]+",";}
            else {formats +=handler.formats[i];}
        }
    $.jGrowl('Only files with the following extensions are allowed:'+formats);
    }
    return  handler;
};

})(jQuery);