(function($){  
    
    var cpaint;
    var action_timer;
    var delta_timer;
    var limit_mouse_bc=0;
    var opts;
    
    var Layer = Class.extend({
        init:function(layer_name) {
            this.name = layer_name;
            opts['container'].append('<canvas id="'+layer_name+'-canvas"></canvas>');
            this.jobject = $('#'+layer_name+'-canvas');
            this.element = this.jobject.get(0);
            this.element.width = opts['container'].width();
            this.element.height  = opts['container'].height();
            this.ctx = this.element.getContext('2d');
        },
    });
   
    var Brush = Class.extend({
        init:function() {
        this.draw = false;
        this.points = [];
        this.size;
        this.color;          
        this._x1,this._x2,this._y1,this._y2;
        this.switch_x,this.switch_y;
        },
        set_layer: function(layer) {
            this.layer = layer;
        },
        stroke:function(x1,y1,x2,y2,dt) {
            if(x1 > x2) {this._x1 = x2; this._x2 = x1;}
            else {this._x1 = x1; this._x2 = x2;}
            if(y1 > y2) {this._y1 = y2; this._y2 = y1;}
            else {this._y1 = y1; this._y2 = y2;}   
        }
    });
    
    var BasicBrush = Brush.extend({
        init: function(){
            this._super();        
        },
        strokeStart: function(layer,x,y) {
            this.ctx = layer.ctx;
            this.ctx.beginPath();
            this.ctx.moveTo(x, y);    
        },
        stroke: function(x1,y1,x2,y2,dt,drag) {
            this.ctx.beginPath(); 
            this.ctx.globalCompositeOperation = 'destination-over'; 
            this.ctx.lineJoin = "round";
            this.ctx.lineWidth = this.size;
            this.ctx.fillStyle = 'rgba('+this.color[0]+','+this.color[1]+','+this.color[2]+','+this.color[3]+')';
            this.ctx.strokeStyle = 'rgba('+this.color[0]+','+this.color[1]+','+this.color[2]+','+this.color[3]+')';
            this.ctx.moveTo(x1, y1);
            this.ctx.lineTo(x2, y2);
            this.ctx.closePath(); 
            this.ctx.stroke();
            
        }
    });    
    
    var ExperimentalBrush = Brush.extend({
        init: function(){
            this._super();        
        },
        strokeStart: function(layer,x,y) {
            this.ctx = layer.ctx;
        },
        stroke: function(x1,y1,x2,y2,dt) {
            this._super(x1,y1,x2,y2,dt);
            this.ctx.globalCompositeOperation = 'source-over';   
            var di=0,dj=0;
            for(i = this._x1;i <= this._x2; i+=(this.size/4)) {
                dj = 0;
                for(j = this._y1;j <= this._y2; j+=(this.size/4)) {                    
                    if (di==dj) {
                    var radgrad = this.ctx.createRadialGradient(i,j,this.size/32,i,j,this.size/2);                
                    radgrad.addColorStop(0, 'rgba('+this.color[0]+','+this.color[1]+','+this.color[2]+','+1+')');
                    radgrad.addColorStop(1, 'rgba('+this.color[0]+','+this.color[1]+','+this.color[2]+','+0+')');
                    this.ctx.fillStyle = radgrad;
                    this.ctx.beginPath(); 
                    this.ctx.fillRect(i-(0.5*this.size),j-(0.5*this.size),this.size,this.size);
                    this.ctx.fill();
                    this.ctx.closePath();
                    }
                dj+=1;
                }
            di += 1;
            }
        }
    });  


    function CollaPaint(opts) {
        cpaint = this;
        this.opts = opts;
        this.layers = new Array(); 
        this._layer_index;
        this.worker  = new Worker('/media/scripts/lib/jquery/jquery.cpaint.worker.js');

        this.tmplog = [];
        this.fg_color,this.bg_color;
        this.tool = 'brush';
        this.tool_active = false;
        this.prev_action;
        
        this.remote_prev_action;
        
        this.shape = 'rect';        
        this.brushes = [new BasicBrush(), new ExperimentalBrush()];
        this.brush = 0;

        this.brush_size;
        this.font_size;
        this.text_line_width;
        this.bind_canvas_handlers();
    }
    
    CollaPaint.prototype.bind_canvas_handlers = function() {
        this.opts['container'].mousedown(function(e){cpaint.handle_cevent(e.offsetX, e.offsetY, false, e);});
        this.opts['container'].mouseup(function(e){cpaint.handle_cevent(e.offsetX, e.offsetY, false, e);});
        this.opts['container'].mousemove(function(e){cpaint.handle_cevent(e.offsetX, e.offsetY, true, e);});
        this.opts['container'].mouseleave(function(e){cpaint.handle_cevent(e.offsetX, e.offsetY, false, e);});
        this.opts['container'].mouseenter(function(e){cpaint.handle_cevent(e.offsetX, e.offsetY, false, e);});        
    }
    
    CollaPaint.prototype.unbind_canvas_handlers = function() {
        this.opts['container'].unbind();
    }
    
    CollaPaint.prototype.arrange_layers = function() {
        var start_z = 10;
        $.each(this.layers, function(index, layer) {
            layer.canvas.jobject.css('z-index',start_z);
            start_z -= 1;
        });
    }
    
    CollaPaint.prototype.create_layer = function(layer) {
        var exists = false;
        $.each(this.layers, function(index, _layer) {
            if(typeof(layer) !='undefined') {
                if(_layer.name == layer.name) {
                exists = true;    
                }
            }
        });
        if(!exists) {
        this.layers.push({
            'id':layer.id,
            'name':layer.name,
            'canvas':new Layer(layer.name),
            'log':layer.log.slice(0)
        });
        this.arrange_layers();
        //this.layer = this.layers[this.layers.length-1].id;
        return this.layers[this.layers.length-1];
        }
        else {
        return false;    
        }
    }
    
    CollaPaint.prototype.get_layer = function(id) {
        var layer_match = false;
        $.each(this.layers, function(index, _layer) {
            if(_layer.id == id) {
                layer_match = _layer;
            }
        });
        return layer_match;
    }

    CollaPaint.prototype.show_slide = function(slide) {
        $.each(this.layers, function(index, _slide) {
            if(_slide == slide) {
                $(_slide.canvas.element).show();
            }
            else {
                $(_slide.canvas.element).hide();
            }
        });
        
    }
    
    CollaPaint.prototype.delete_from_log = function(layer) {
        $.each(this.layers, function(index, layer) {
            
        });
    }
    
    CollaPaint.prototype.delete_layer = function(layer) {
        $.each(this.layers, function(index, _layer) {
            if(typeof(layer) !='undefined') {
                if(_layer !== undefined) {
                    if(layer.name == _layer.name) {
                        $('#'+_layer.name+'-canvas').remove();
                        cpaint.layers.splice(index,1);
                        
                    }
                }
            }
        });
        this.arrange_layers();
        this.layer = this.layers[this.layers.length-1].id;
    }

    
    CollaPaint.prototype.change_layer_order = function(layer_id, to_position) {
        if (to_position >=0 && to_position < this.layers.length) {
            $.each(this.layers, function(index, layer) {
                if(layer !== undefined) {
                    if(layer.id == layer_id) {                    
                    var _tmplayer = cpaint.layers.splice(index,1);
                    var part1 = cpaint.layers.slice(0, to_position);
                    var part2 = cpaint.layers.slice(to_position, cpaint.layers.length);
                    cpaint.layers = part1.concat(_tmplayer).concat(part2);
                    }
                }
            });
        this.arrange_layers();
        }
    }
    
    CollaPaint.prototype.resize = function() {
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
        $.each(this.layers, function(key, layer) {
            layer.canvas.ctx.canvas.width = cpaint.opts['container'].width();
            layer.canvas.ctx.canvas.height = cpaint.opts['container'].height();
            //cpaint.redraw(layer);
            apply_log(layer.log.slice(0), layer);
        });
    }
    

    CollaPaint.prototype.draw = function(type, params, dfd, layer) {     
        switch(type) {
        //{[brush,[x,y,color,dragging,brush_size,brush_type,delta_time]]}
        case 'brush':
            prev_params = params[0];
            params = params[1];
            //set brush type
            var _brush = this.brushes[params[5]];
            _brush.color = params[2];
            _brush.size = params[4];
            //if dragging
            if(!params[3]) {
                _brush.strokeStart(layer.canvas, params[0], params[1]);  
            }
            else {
            _brush.stroke(prev_params[0],prev_params[1], params[0], params[1],params[6], params[3]);
            }
            //return dfd.resolve();
        break;
        //{[shape,[x[],y[],color[],border,type,layer]]}
        case 'shape':
            //convert layer-id to list-order
            layer.canvas.ctx.globalCompositeOperation = 'source-over';
            layer.canvas.ctx.lineJoin = "round";
            layer.canvas.ctx.fillStyle = 'rgba('+params[2][0][0]+','+params[2][0][1]+','+params[2][0][2]+','+params[2][0][3]+')';
            layer.canvas.ctx.beginPath();  
                if (params[4] == 'rect') {
                    layer.canvas.ctx.rect(params[0][0], params[1][0], params[0][1], params[1][1]);        
                }
                else if (params[4] == 'circle') {
                var radius = Math.abs(params[0][1]);
                    if (radius > 0) {
                        var _layer = this.get_layer(this.layer);
                        layer.canvas.ctx.arc(params[0][0],params[1][0],radius,0,Math.PI*2, true);
                    }
                }
                if(params[3] > 0) {
                layer.canvas.ctx.lineWidth = params[3];
                layer.canvas.ctx.strokeStyle = 'rgba('+params[2][1][0]+','+params[2][1][1]+','+params[2][1][2]+','+params[2][1][3]+')';
                layer.canvas.ctx.stroke();
                }
            layer.canvas.ctx.closePath();
            layer.canvas.ctx.fill();
        break;
        //action = [[x,y],this.bg_color, startColor, this.layer];
        case 'fill':
            var canvasWidth = cpaint.opts['container'].width();
            var canvasHeight = cpaint.opts['container'].height();
            this.worker.postMessage({
                'pixeldata': layer.canvas.ctx.getImageData(0,0,canvasWidth,canvasHeight),
                'startXY': params[0],
                'fillColor': params[1],
                'startColor': params[2],
                'width':canvasWidth,
                'height':canvasHeight
            });
            this.worker.addEventListener('message',function(response){
            layer.canvas.ctx.putImageData(response.data.pixeldata, 0, 0);
            if(dfd != undefined) {
                return dfd.resolve();
            }
            }, false);
            //var idata = ImageProcessor.floodfill(_layer.canvas,params[0], params[1], params[2]);          
            
        break;
        //{[text,[x,y,color[],border,font,text,layer]]}
        case 'text':
            layer.canvas.ctx.font= params[4];
            layer.canvas.ctx.fillStyle= 'rgba('+params[2][0][0]+','+params[2][0][1]+','+params[2][0][2]+','+params[2][0][3]+')';
                if(params[3] > 0) {
                layer.canvas.ctx.lineWidth = params[3];
                layer.canvas.ctx.strokeStyle = 'rgba('+params[2][1][0]+','+params[2][1][1]+','+params[2][1][2]+','+params[2][1][3]+')';
                layer.canvas.ctx.strokeText(params[5], params[0], params[1]);                        
                } 
            layer.canvas.ctx.fillText(params[5], params[0], params[1]); 
        break;
        }               
    }  
    
    //TAKES AN ACTION, AND MANAGES THE DRAW FUNCTION
    CollaPaint.prototype.handle_action = function(type, action, layer) {
        var dfd = $.Deferred();
        //layer specific actions
        if(layer != undefined) {
            switch(type) {
                case 'brush':
                    if(!action[3]) {
                    this.remote_prev_action = action;    
                    }
                    layer.log.push(['brush',action]);
                    this.draw('brush',[this.remote_prev_action,action], dfd, layer); 
                    this.remote_prev_action = action;
                break;
                case 'shape':
                    layer.log.push(['shape',action]);   
                    this.draw('shape',action, dfd, layer);
                    return dfd.resolve();
                break; 
                case 'fill':
                    layer.log.push(['fill',action]);
                    this.draw('fill',action, dfd, layer);     
                break;
                case 'text':
                    layer.log.push(['text',action]);
                    this.draw('text',action, dfd, layer);   
                    return dfd.resolve();
                break;
            } 
        }
        return dfd;
    }
    
    //HANDLES ALL MOUSE RELATED EVENTS WITHIN THE CANVAS CONTAINER
    CollaPaint.prototype.handle_cevent = function(x, y, dragging, event) { 
        var action = [];
        if(event.type == 'mousemove' && !this.tool_active) {
            //possibility to limit mouse updates
            if (limit_mouse_bc % 1 == 0) {
            this.opts['ws_handler'].remote('/data/pad/'+this.opts['pad_id']+'/mouse/bc/',{params:[x,y]},function(response){});
            }
            limit_mouse_bc += 1;
        }
        else if(event.type == 'mouseleave') {
            this.opts['ws_handler'].remote('/data/pad/'+this.opts['pad_id']+'/mouse/leave/',{},function(response){});
        }
        else {
            switch(this.tool) {
                case 'brush':
                    switch(event.type) {                    
                        //new operations.brush(event)
                        case 'mousedown':                            
                            action_timer = new Date().getTime();
                            //{[brush,[x,y,color,dragging,brush_size,brush_type,delta_time]]}
                            action = [x,y,this.fg_color,dragging,this.brush_size,this.brush, 0];
                            this.prev_action = action;
                            this.layer.log.push(['brush',action]);
                            this.tool_active = true;
                            this.draw('brush',[this.prev_action,action],null,this.layer);
                            this.opts['ws_handler'].remote('/data/pad/'+this.opts['pad_id']+'/layers/'+this.layer.id+'/draw/brush/',{params:action},function(response){});
                        break;
                        case 'mousemove':
                            if(this.tool_active) {                        
                            delta_timer = new Date().getTime() - action_timer;
                            action_timer = new Date().getTime();
                            action = [x,y,this.fg_color,dragging,this.brush_size,this.brush, delta_timer];
                            this.layer.log.push(['brush',action]);   
                            this.draw('brush',[this.prev_action,action],null,this.layer);
                            this.opts['ws_handler'].remote('/data/pad/'+this.opts['pad_id']+'/layers/'+this.layer.id+'/draw/brush/',{params:action},function(response){});
                            this.prev_action = action;
                            }                        
                        break;
                        case 'mouseup':
                            this.tool_active = false;
                        break;
                        case 'mouseleave':
                        break;
                        case 'mouseenter':
                        break;
                        }
                break;
                //{[shape,[x[],y[],color[],border,type,layer]]}
                case 'shape':                       
                    switch(event.type) {                        
                    case 'mousedown':   
                        this.snapshot = this.layer.canvas.ctx.getImageData(0, 0, this.opts['container'].width(), this.opts['container'].height());
                        this.tmplog = new Array();
                        this.tmplog =[[],[],[this.bg_color, this.fg_color],this.line_width,this.shape];
                        this.tmplog[0].push(x);
                        this.tmplog[1].push(y);                    
                        this.tool_active = true;                         
                    break;
                    case 'mouseup':                    
                        this.tool_active = false;
                        this.tmplog[0].push(x-this.tmplog[0][0]);
                        this.tmplog[1].push(y-this.tmplog[1][0]);
                        this.layer.log.push(['shape',this.tmplog]);
                        this.opts['ws_handler'].remote('/data/pad/'+this.opts['pad_id']+'/layers/'+this.layer.id+'/draw/shape/',this.tmplog,function(response){});
                    break;
                    case 'mousemove':                        
                        if(this.tool_active == true) {                            
                            this.layer.canvas.ctx.putImageData(this.snapshot, 0, 0);
                            action = [[this.tmplog[0][0],x-this.tmplog[0][0]],[this.tmplog[1][0],y-this.tmplog[1][0]],[this.bg_color, this.fg_color],this.line_width,this.shape];
                            this.draw('shape',action, null, this.layer);                        
                        }
                        break;            
                    }
                break;
                //{[fill,}
                case 'fill':
                    switch(event.type) { 
                        case 'mouseup':
                            var startColor = this.layer.canvas.ctx.getImageData(x, y, 1, 1).data;
                            action = [[x,y],this.bg_color, startColor];
                            this.layer.log.push(['fill',action]);
                            this.draw('fill',action, null, this.layer);    
                            this.opts['ws_handler'].remote('/data/pad/'+this.opts['pad_id']+'/layers/'+this.layer.id+'/draw/fill/',{params:action},function(response){});
                        break;
                    }
                break;
                //{[text,[x,y,color[],border,font,text,layer]]}
                case 'text':
                    switch(event.type) {
                        case 'mousedown':
                        
                        var _text = $('#text-input').val()
                        if(_text != '') {
                            $('#text-input').val('');
                            action = [x,y,[this.bg_color,this.fg_color],this.text_line_width,this.font_size +'pt Calibri',_text];
                            this.layer.log.push(['text',action]);
                            this.draw('text',action, null, this.layer);   
                            this.opts['ws_handler'].remote('/data/pad/'+this.opts['pad_id']+'/layers/'+this.layer.id+'/draw/text/',{params:action},function(response){});
                        }
                        break;
                        case 'mouseup':
                        break;
                        case 'mousemove':
                        break;
                        case 'mousedown':
                        break;
                    }
                break;
            }
        }
    }

    //Remove all operations from the whiteboard draw array
    CollaPaint.prototype.clear_canvas = function() {
        $.each(this.layers, function(idx, layer) {
            layer.log = [];
            layer.canvas.ctx.clearRect(0,0,cpaint.opts['container'].width(),cpaint.opts['container'].height());
        });
    }
    
$.extend({
    cpaint_settings: {
        container:'',
        canvas: '',
        subscribe_action:'',    
        cb_insert:'',            
        cb_delete:'',            
        cb_undo:'',
    },    
    collapaint: function(ws_handler, params) {
    opts = $.extend($.cpaint_settings, params);
    opts['ws_handler'] = ws_handler;
    collapaint = new CollaPaint(opts);
    return collapaint;
    }   
});   
    
})(jQuery);