/*# -*- coding: utf-8 -*-
"""
    scripts.modules.pad
    ~~~~~~~~~~~~~~~~~~~

    Pad module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
*/
define('modules/pad',[
'order!lib/jquery/jquery.color',
'order!lib/jquery/jquery.cpaint',    
],
       
function(){
    var plasmoid_editor;
    var plasmoid_editor_lc;
    var plasmoid_container;
    var cpaint;
    //var layer_accordion;
    var _bg_color, _fg_color;
    var r=255,g=0,b=0,a=1,h=0,s=1,v=1;
    var spectrum_click = false, opacity_click = false, wb_click = false;
    var pos_store = {};
    var pad_id;
    var resizeTimeoutId;
    var urls;

    var slide_context;
    
    function add_widgets(left_widgets, right_widgets) {
        $.each(left_widgets, function(idx, widget) {
            $('.sidebar').prepend(widget);
        });
        $.each(right_widgets, function(idx, widget) {
            $('.menu').prepend(widget);
        });
    }
    
    
    function switch_tool(tool) {
        cpaint.tool = tool;
        switch(tool) {
        case 'brush':
        $('#shape-tools').hide();
        $('#text-tools').hide();
        $('#brush-tools').show();
        $('canvas').removeClass('canvas-shape');  
        $('canvas').removeClass('canvas-text');
        $('canvas').addClass('canvas-brush');  
        break;
        case 'shape':
        $('#brush-tools').hide();
        $('#text-tools').hide();
        $('#shape-tools').show();        
        $('canvas').removeClass('canvas-brush'); 
        $('canvas').removeClass('canvas-text');
        $('canvas').addClass('canvas-shape');   
        break;
        case 'fill':
        $('#brush-tools').hide();
        $('#shape-tools').hide();
        $('#text-tools').hide();
        $('canvas').removeClass('canvas-brush'); 
        $('canvas').removeClass('canvas-shape');
        $('canvas').removeClass('canvas-text');   
        $('canvas').addClass('canvas-fill');
        break;
        case 'text':
        $('#brush-tools').hide();
        $('#shape-tools').hide();
        $('#text-tools').show();
        $('canvas').removeClass('canvas-brush'); 
        $('canvas').removeClass('canvas-shape');
        $('canvas').addClass('canvas-text');   
        break;
        }
    }  
    
    
function bind_functions() {
    application.functions.pad = {
        route: function(uri, push_history) {
            if(urls == undefined){
                urls = [
                    [XRegExp('^/pad/(?<pad_id>[^/]+)/$'),application.functions.pad.view_pad],
                ];
            }
            application.route_uri_to_mod_function(uri, urls, push_history);
        },
       
        view_pad: function(kwargs){
            application.ws.remote('/pad/'+kwargs.pad_id+'/',{},function(response){  
                application.functions.ui.transition(response.data.dom.main, $('.main'));
                application.functions.ui.add_widgets([response.data.dom.left]);

                cpaint = $.collapaint(application.ws, {pad_id: kwargs.pad_id, container:$('.canvas-container'),width:$('.canvas-container').width(),height:500});
                cpaint.fg_color = [0,174,239,1];
                cpaint.bg_color = [0,0,0,1];
                //layer_accordion = $('#layer-tools-accordion').accordion();            
                function apply_log(log, layer){
                    var operation = log.shift();
                    if(operation != undefined) {
                        if(operation[0] == 'fill') {
                            cpaint.layer = layer;
                            cpaint.handle_action(operation[0],operation[1],layer).done(function(){
                                if(log.length > 0) {
                                    apply_log(log, layer);                    
                                }
                                else {
                                return;
                                }
                            });  
                        }
                        else {
                            cpaint.layer = layer;
                            cpaint.handle_action(operation[0],operation[1],layer);
                            apply_log(log, layer);   
                        }
                    }
                }
                //response.data.layers.reverse();
                $.each(response.data.layers,function(idx, layer) {
                    var layer_obj = cpaint.create_layer(layer);
                    apply_log(layer.log, layer_obj);
                });
                cpaint.arrange_layers();
                cpaint.layer = cpaint.layers[0];
                application.functions.pad.show_layers(cpaint.layer.id);            
                switch_tool('brush');
                //layer_accordion.accordion('resize');
                bind_events();               
                $('div[id*="psycopad-widget"]').hide().fadeIn('fast', function() { } );  
            }); 
        },
       
        clear_pad: function() {
            cpaint.clear_canvas();
            application.ws.remote('/data/pad/'+pad_id+'/clear/',{params:[]},function(response){});            
        },
       
        save_pad: function() {
            application.ws.remote('/data/pad/'+pad_id+'/save/',{},function(response){
            });  
        },
        select_brush_tool: function() {switch_tool('brush');},
        select_shape_tool: function() {switch_tool('shape');},
        select_fill_tool: function() {switch_tool('fill');},
        select_text_tool: function() {switch_tool('text'); },
        
        create_layer: function() {
            var layer_name = 'Unnamed_'+Math.ceil(Math.random()*100);
            application.ws.remote('/data/pad/'+pad_id+'/layers/'+layer_name+'/create/',{},function(response){});
        },
       
        delete_layer: function() {            
            var layer_name = $('.slide-overview-slide-selected > span').text();
            if(cpaint.layers.length > 1) {
            application.ws.remote('/data/pad/'+pad_id+'/layers/'+layer_name+'/delete/',{},function(response){});
            }
            else {
            console.log('Can\'t remove last layer');    
            }
        },
       
        move_layer_up: function() {
            var target_element = $('.slide-overview-slide-selected');
            var layer_id = target_element.attr('id').substring(3);
            var target_pos = target_element.prevAll().length;
            application.ws.remote('/data/pad/'+pad_id+'/layers/'+layer_id+'/order/',{'to_position':target_pos-1},function(response){
            });
        },
        move_layer_down: function() {
            var target_element = $('.slide-overview-slide-selected');
            var layer_id = target_element.attr('id').substring(3);
            var target_pos = target_element.prevAll().length;
            application.ws.remote('/data/pad/'+pad_id+'/layers/'+layer_id+'/order/',{'to_position':target_pos+1},function(response){
            });
        },
        //FIXME: Disabled for now
        open_plasmoid_layer: function() {
            var target_element = $('.slide-overview-slide-selected');
            var layer_id = target_element.attr('id').substring(3);
            if($('#plasmoid-editor').is(":visible")) {
                cpaint.bind_canvas_handlers();
                $('#plasmoid-editor').hide('slide', {direction:'up'}, 300, function(){ 
                    plasmoid_editor.disconnect();
                });
            }
            else {
                cpaint.unbind_canvas_handlers(); 
                $('#plasmoid-title').text(target_element.text());
                $('#plasmoid-editor').show('slide', {direction:'up',easing: 'easeOutBounce'}, 800, function(){ 
                    
                    ///$('#plasmoid-editor').keypress(function(event) {
                    //    format_plasmoid_editor(event);                    
                    //});
                });
                var plasmoid_id = pad_id+'_'+layer_id;
                plasmoid_editor = $.jinfinote(application.ws, {
                ws_connect:'/data/plasmoid/'+plasmoid_id+'/connect/',
                ws_disconnect:'/data/plasmoid/'+plasmoid_id+'/disconnect/',
                ws_insert:'/data/plasmoid/'+plasmoid_id+'/insert/',
                ws_delete:'/data/plasmoid/'+plasmoid_id+'/delete/',
                ws_undo:'/data/plasmoid/'+plasmoid_id+'/undo/',
                ws_caret:'/data/plasmoid/'+plasmoid_id+'/caret/',
                cb_insert:'^/data/plasmoid/'+plasmoid_id+'/insert/$',      
                cb_delete:'^/data/plasmoid/'+plasmoid_id+'/delete/$',
                cb_undo:'^/data/plasmoid/'+plasmoid_id+'/undo/$',
                cb_caret:'^/data/plasmoid/'+plasmoid_id+'/caret/$',
                editor:'code',
                init: function(data) {return $('#plasmoid-editor')},                
                });
            }
        },
        //FIXME: Disabled for now
        play_plasmoid_layer: function() {
            var target_element = $('.slide-overview-slide-selected');
            var layer_id = target_element.attr('id').substring(3);
            var layer_name = target_element.text();
            application.ws.remote('/data/plasmoid/'+pad_id+'_'+layer_id+'/play/',{},function(response){
                var jsCode = Processing.compile(response.data.script).sourceCode; 
                console.log(jsCode);
                plasmoid_container = new Processing($('#'+layer_name+'-canvas').get(0), response.data.script);
            });
        },
        //FIXME: Disabled for now
        pause_plasmoid_layer: function() {
            
        },
        //Colorpicker
        set_selected_slot_color: function(rgba, persist) {
            var slot_id = $('.pp-color-slot-selected > div').attr('id');
            if (typeof(slot_id) != 'undefined') {
                if(persist) {
                    if (rgba.length == 4) {
                        if (slot_id.indexOf('fgcolor') != -1) {
                        cpaint.fg_color = rgba;
                        _fg_color = rgba;
                        $('.pp-color-slot-selected > div').css('background-color','rgba('+rgba[0]+','+rgba[1]+','+rgba[2]+','+rgba[3]+')');
                        }
                        else if (slot_id.indexOf('bgcolor') != -1) {
                        cpaint.bg_color = rgba;
                        _bg_color = rgba;
                        $('.pp-color-slot-selected > div').css('background-color','rgba('+rgba[0]+','+rgba[1]+','+rgba[2]+','+rgba[3]+')');
                        }
                    }
                    else if(rgba.length == 2) {
                        if (slot_id.indexOf('fgcolor') != -1) {rgba = rgba[1];}
                        else if (slot_id.indexOf('bgcolor') != -1) {rgba = rgba[0];}
                        if(rgba != undefined) {
                        $('.pp-color-slot-selected > div').css('background-color','rgba('+rgba[0]+','+rgba[1]+','+rgba[2]+','+rgba[3]+')');
                        }
                    }
                }
                else {
                $('.pp-color-slot-selected > div').css('background-color','rgba('+rgba[0]+','+rgba[1]+','+rgba[2]+','+rgba[3]+')');    
                }
            }  
        },
       
        show_layers: function(selected_layer_id) {
            $('#slide-overview-slides').empty();
            $.each(cpaint.layers, function(key, slide) {
                //disable plasmoid layer functionality for now.
                //$('#slide-overview-slides').append('<div id="id_'+layer.id+'" class="slide-overview-slide"><span>'+layer.name+'</span><button id="btn-plasmoid-layer-open" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-gear"></span></button></div>');
                $('#slide-overview-slides').append('<div data-name="'+slide.name+'" id="id_'+slide.id+'" class="slide-overview-slide"><span>'+slide.name+'</span></div>');
                if(selected_layer_id != null) {
                    if(selected_layer_id == slide.id) {
                        $('#id_'+selected_layer_id).addClass('slide-overview-slide-selected');
                        $('#slide-title').text(slide.name);
                        cpaint.show_slide(slide);
                    }
                }
            });
            if(selected_layer_id == null) {
            $('#slide-overview-slides div:last-child').addClass('slide-overview-slide-selected');
            //cpaint.layer = parseInt($('#slide-overview-slides div:last-child').attr('id').substr(3));
            }
            //layer_accordion = $('#layer-tools-accordion').accordion();
        },
       
        draw_remote_pointer: function(x,y,username) {
            username = username.replace(" ", "_");
            var pointer = $('#pointer-'+username);
            if(!pointer.length > 0) {
                $('body').append('<div id="pointer-'+username+'" class="remote-brush"><span>'+username+'</span></div>');
            }
            if(pos_store[username] === undefined) {
                pos_store[username] = [];
            }        
            var container_pos = $('.canvas-container').offset();
            var container_width =  $('.canvas-container').width();
            var container_height =  $('.canvas-container').height();
            var pointer_width = $('.remote-brush').width();
            var pointer_height = $('.remote-brush').height();
            pos_store[username].push([x,y]);
            $(pointer).css('left',(container_pos.left+x- (pointer_width/2))+'px' );
            $(pointer).css('top',(container_pos.top + y - (pointer_height/2))+'px');
            if(((container_pos.left+x) > (container_pos.left + container_width)) || ((container_pos.top+y) > (container_pos.top + container_height))) {
                $(pointer).css('display','none');
            }
            else if (((container_pos.left+x) < (container_pos.left)) || ((container_pos.top+y) < (container_pos.top))){
                $(pointer).css('display','none');   
            }
            else {
            $(pointer).css('display','block');   
            }
        },
       
        kill_remote_pointers: function(username) {            
            if(username !== undefined){
                username = username.replace(" ", "_");
                $('#pointer-'+username).remove();
            }
            else {
                $('.remote-brush').remove();
            }
        }
    }
}
    

function bind_ws() {
    //response.params = [x,y,username]
    application.ws.method('^/data/pad/'+pad_id+'/mouse/receive/$',function(response){
        application.functions.pad.draw_remote_pointer(response.params[0],response.params[1],response.params[2]);
    });
    application.ws.method('^/data/pad/'+pad_id+'/mouse/leave/$',function(response){
        application.functions.pad.kill_remote_pointers(response.params[0]);        
    });
    application.ws.method('^/data/pad/'+pad_id+'/layers/(?<layer_id>[^/]+)/draw/brush/$',function(response){
        application.functions.pad.draw_remote_pointer(response.params[0],response.params[1],response.params[7]);
        cpaint.handle_action('brush',response.params, cpaint.get_layer(parseInt(response.layer_id)));
    });
    application.ws.method('^/data/pad/'+pad_id+'/layers/(?<layer_id>[^/]+)/draw/shape/$',function(response){
        application.functions.pad.draw_remote_pointer(response.params[0],response.params[1],response.params[5]);
        cpaint.handle_action('shape',response.params, cpaint.get_layer(parseInt(response.layer_id)));
    });
    application.ws.method('^/data/pad/'+pad_id+'/layers/(?<layer_id>[^/]+)/draw/text/$',function(response){
        application.functions.pad.draw_remote_pointer(response.params[0],response.params[1],response.params[6]);
        cpaint.handle_action('text',response.params, cpaint.get_layer(parseInt(response.layer_id)));
    });
    application.ws.method('^/data/pad/'+pad_id+'/layers/(?<layer_id>[^/]+)/draw/fill/$',function(response){
        //application.functions.pad.draw_remote_pointer(response.params[0],response.params[1],response.params[8]);
        cpaint.handle_action('fill',response.params, cpaint.get_layer(parseInt(response.layer_id)));
    });
    
    application.ws.method('^/data/pad/'+pad_id+'/clear/$',function(response){
        cpaint.clear_canvas();
    });
    application.ws.method('^/data/pad/'+pad_id+'/save/$',function(response){

    });
    application.ws.method('^/data/pad/'+pad_id+'/layers/(?<layer_name>[^/]+)/create/$',function(response){
        cpaint.layer = cpaint.create_layer(response.data.layer);
        application.functions.pad.show_layers(cpaint.layer.id);
        //layer_accordion.accordion('resize');
    });
    application.ws.method('^/data/pad/'+pad_id+'/layers/(?<layer_name>[^/]+)/delete/$',function(response){
        cpaint.delete_layer(response.data.layer);
        cpaint.layer = cpaint.layers[cpaint.layers.length-1];
        application.functions.pad.show_layers(cpaint.layers[cpaint.layers.length-1].id);
        //layer_accordion.accordion('resize');
    });
    application.ws.method('^/data/pad/'+pad_id+'/layers/(?<layer_name>[^/]+)/order/$',function(response){
        var _remote_layers = response.data.layers;
        $.each(_remote_layers, function(idx1, _remote_layer){
            $.each(cpaint.layers, function(idx2, _layer){
                if(_remote_layer.id == _layer.id) {
                    _remote_layers[idx1].canvas = _layer.canvas;
                }
            });
        });        
        cpaint.layers = _remote_layers;
        cpaint.layer = cpaint.get_layer(response.data.id);
        cpaint.arrange_layers();
        application.functions.pad.show_layers(response.data.id); 
    });
    
    application.ws.method('^/data/plasmoid/(?<plasmoid_id>[^/]+)/online/update/$', function(params){
        plasmoid_editor.update_online(params.online);
    }); 
}
 
 
function bind_events() {
    
    //SELECT LAYER FROM LIST
    $('#slide-overview-slides').delegate('.slide-overview-slide','click', function(event){
        $('#slide-overview-slides > .slide-overview-slide').removeClass('slide-overview-slide-selected');
        $(this).addClass('slide-overview-slide-selected');
        $('#slide-title').text($(this).data('name'));
        cpaint.layer = cpaint.get_layer(parseInt($(this).attr('id').substring(3)));
        cpaint.show_slide(cpaint.layer);
    });
    
            //we need a way to capture remote textarea update events
    $(document).bind('infinote_update', function(event) {});      
        
    //****************************SLIDERS***********************************************************************
    $('#brush-tools-size').slider({min:1, max:100, value:8,
        create: function(event, ui) {cpaint.brush_size = 8;
        $('#brush-tools-size-indicator').html(cpaint.brush_size+'px');
        },
        change:function(event, ui) {
        cpaint.brush_size = ui.value;
        $('#brush-tools-size-indicator').html(cpaint.brush_size+'px');
        }
    });
    $('#shape-tools-line-width').slider({min:0, max:50, value:1,
        create: function(event, ui) {cpaint.line_width = 1;
        $('#shape-tools-line-width-indicator').html(cpaint.line_width+'px');
        },
        change:function(event, ui) {cpaint.line_width = ui.value;
        $('#shape-tools-line-width-indicator').html(cpaint.line_width+'px');
        }
    });
    $('#text-tools-line-width').slider({min:0, max:10, value:0,
        create: function(event, ui) {cpaint.text_line_width = 0;
        $('#text-tools-line-width-indicator').html(cpaint.text_line_width+'px');
        },
        change:function(event, ui) {cpaint.text_line_width = ui.value;
        $('#text-tools-line-width-indicator').html(cpaint.text_line_width+'px');
    }});
    $( '#text-tools-font-size').slider({min:8, max:50, value:8,
        create: function(event, ui) {cpaint.font_size = 8;
        $('#text-tools-font-size-indicator').html(cpaint.font_size+'px');
        },
        change:function(event, ui) {cpaint.font_size = ui.value;
        $('#text-tools-font-size-indicator').html(cpaint.font_size+'px');
        }
    });
    
    
    //***********************************************************************************************************
    $('#brush-selector').change(function() {cpaint.brush = $('#brush-selector').val();});
    $('#shape-selector').change(function() {cpaint.shape = $('#shape-selector').val();}); 
    
    //HUE PALET
    $('#pp-picker-hue').mousedown(function(event) {
        spectrum_click = true;
        _bg_color = cpaint.bg_color;
        _fg_color = cpaint.fg_color;    
    });
    $('#pp-picker-hue').mouseout(function(event) {
        spectrum_click = false;
        application.functions.pad.set_selected_slot_color([_bg_color,_fg_color], true);
    });
    $('#pp-picker-hue').mouseup(function(event) {
        spectrum_click = false;
        application.functions.pad.set_selected_slot_color([r,g,b,a], true);
    });
    //calculate the current mousecolor based on relative positioning.
    $('#pp-picker-hue').mousemove(function(event) {        
        if(spectrum_click == false) return;
        h = event.layerX / event.currentTarget.clientWidth;
        var ratio;
        switch(true) {
            case (h < 1/6):            
                ratio = h / (1/6);
                with (Math) {r = 255;g = ceil(ratio * 255);b = 0;}
            break;
            case (h < 2/6):
                ratio = (h - 1/6) / (1/6);
                with (Math) {r = ceil(abs(ratio - 1) * 255);g = 255;b = 0;}
            break; 
            case (h < 3/6):
                ratio = (h - 2/6) / (1/6);
                with (Math) {r = 0;g = 255;b = ceil(ratio * 255);}
            break;
            case (h < 4/6):
                ratio = (h - 3/6) / (1/6);
                with (Math) {r = 0;g = ceil(abs(ratio - 1) * 255);b = 255;}
            break;
            case (h < 5/6):
                ratio = (h - 4/6) / (1/6);
                with (Math) {r = ceil(ratio * 255);g = 0;b = 255;}
            break;
            case (h < 6/6):
                ratio = (h - 5/6) / (1/6);
                with (Math) {r = 255;g = 0;b = ceil(abs(ratio - 1) * 255);}
            break;
        }        
        var _c = $.Color( [ h, s, v], 'HSV' ).toRGB();
        //pass the raw rgb hue to the hsv palet
        $('#pp-picker-hsv-color').css('background-color','rgb('+r+','+g+','+b+')');
        //console.log(Math.floor(h*255));
        //$('#pp-picker-hsv-color').css('background-color','hsla('+(Math.floor(h*255))+',100%,50%,1)');
        r = _c[0]; g = _c[1]; b = _c[2];        
        $('#pp-picker-alpha').css('background-image','-webkit-gradient(linear,left center,right center,color-stop(0, rgba('+r+','+g+','+b+',1)),color-stop(1, rgba('+r+','+g+','+b+',0)))');
        $('#pp-picker-alpha').css('background-image','-moz-linear-gradient(left, rgba('+r+','+g+','+b+',1),rgba('+r+','+g+','+b+',0))');
        application.functions.pad.set_selected_slot_color([r,g,b,a], false);    
    });
    
    //ALPHA PALET
    $('#pp-picker-alpha').mousedown(function(event) {
        opacity_click = true;
        _bg_color = cpaint.bg_color;
        _fg_color = cpaint.fg_color;          
    });
    $('#pp-picker-alpha').mouseout(function(event) {
        opacity_click = false;  
        application.functions.pad.set_selected_slot_color([_bg_color,_fg_color], true);
    });
    $('#pp-picker-alpha').mouseup(function(event) {
        opacity_click = false;
        application.functions.pad.set_selected_slot_color([r,g,b,a], true);
    });    
    
    $('#pp-picker-alpha').mousemove(function(event) {
        if(opacity_click == false) return;
        a = 1- (event.layerX / event.currentTarget.clientWidth);
        application.functions.pad.set_selected_slot_color([r,g,b,a], false);
    });
    
    //HSV PALET
    $('#pp-picker-hsv').mousedown(function(event) {
        wb_click = true;
        _bg_color = cpaint.bg_color;
        _fg_color = cpaint.fg_color;    
    });
    $('#pp-picker-hsv').mouseout(function(event) {
        wb_click = false;
        application.functions.pad.set_selected_slot_color([_bg_color,_fg_color], true);
    });
    $('#pp-picker-hsv').mouseup(function(event) {
        wb_click = false;
        application.functions.pad.set_selected_slot_color([r,g,b,a], true);
    });
    $('#pp-picker-hsv').mousemove(function(event) {
        if(wb_click == false) return;
        s = (event.layerX / event.currentTarget.clientWidth); 
        v = 1- (event.layerY / event.currentTarget.clientHeight); 
        var _c = $.Color( [ h, s, v], 'HSV' ).toRGB();
        r = _c[0]; g = _c[1]; b = _c[2];
        application.functions.pad.set_selected_slot_color([r,g,b,a], false);
        $('#pp-picker-alpha').css('background-image','-webkit-gradient(linear,left center,right center,color-stop(0, rgba('+r+','+g+','+b+',1)),color-stop(1, rgba('+r+','+g+','+b+',0)))');
    });
        
        
    $('#pp-color-slots > div').click(function(event) {
        if(!$(this).hasClass('pp-color-slot-selected')) {
        $(this).addClass('pp-color-slot-selected');
        var neighbour = $(this).siblings();
        if (neighbour.hasClass('pp-color-slot-selected')) {
            neighbour.removeClass('pp-color-slot-selected');
        }
        }
        else {
            $(this).removeClass('pp-color-slot-selected');
        }
    });  
    //***********************************************************************************************************
    $(window).resize(function(event) {
        window.clearTimeout(resizeTimeoutId); 
        resizeTimeoutId = window.setTimeout(function(){ cpaint.resize(); }, 1000);             
    });  
}  

return {
    init: function(uri, push_history) {
        slide_context = $.context({anchor:'.main',delegate:'#slide-context',uri:'/pad/context/',id:'ctx-slide'});
        application.cache.load.context.slide = true;
        bind_functions();
        pad_id = 'development';
        bind_ws();      
        application.functions.pad.route(uri, push_history);
        return 'pad';
    },
    load: function(uri, push_history) {
        if(typeof application.cache.load.context.slide == 'undefined') {
            application.cache.load.context.slide = true;
            slide_context.reload();
        }
        $('div[class*="slide-widget"]').remove();
        application.functions.pad.route(uri, push_history);
    },
    
    clean_up: function() {
        $('div[class*="slide-widget"]').remove();
        application.functions.pad.kill_remote_pointers();
    }
}
    


});