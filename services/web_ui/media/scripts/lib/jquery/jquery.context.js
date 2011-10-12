(function($){

    function CTX(opts) {
        var ctx = this;
        ctx.name = opts.id;        
        ctx.opts = opts;


        ctx.setup_context = function(context_data) {
            //Init context-menu when not available yet
            if($('#'+ctx.opts.id).length == 0) {
                //only make a context menu if there is at least some content to handle
                //may not be the case if not authenticated or staff
                $('body').append('<div id='+ctx.opts.id+' class="context-menu"></div>');
                var _target = $('#'+ctx.opts.id);
                _target.html(context_data);
                _target.unbind().bind('mouseleave',function(e){
                    _target.find('div[data-ctx]').each(function(idx,value) {
                        $(this).addClass('ui-state-disabled');
                    });
                    _target.find('div[data-ctx-showid]').each(function(idx,value) {
                        $(this).addClass('ui-state-hidden');
                    });
                    $('.context-menu').hide();
                });
                //make sure mouseleave is triggered, since hwios-button delegate is called
                //after this click event, and ui-state-disabled cant be processed otherwise
                _target.find('.context-menu-option').die().live('click',function(e){
                    //do not hide when clicking a disabled item
                    if(!$(this).hasClass('ui-state-disabled')){
                    $('.context-menu').css('left',-1000);
                    }
                });
                //Handle contextmenu event for all relevant dom-elements
                $(ctx.opts.anchor).delegate(ctx.opts.delegate+' div','contextmenu', ctx.process_context);
            }
        }


        CTX.prototype.load_context = function() {
            if(ctx.opts.uri !== undefined){
                application.ws.remote(ctx.opts.uri,{},function(response){
                    ctx.setup_context(response.data.dom.context);
                });
            }
            else if(ctx.opts.data !== undefined){
                ctx.setup_context(ctx.opts.data);
            }
        }


        //Go through all context delegate divs in the dom
        ctx.process_context = function(event){
            //only proceed if contextmenu has options
            var _opts = $('#'+ctx.opts.id+' > .context-menu-option');
            if(_opts.size() > 0) {
                var dom_data = $(this).data();
                var _target = $('#'+ctx.opts.id);
                    //mix-in dom delegate data with context menu
                    _target.find('.context-menu-option').each(function(idx,value) {
                        if('id' in dom_data){
                            $(this).data('id',dom_data.id);
                        }
                    });
                //ctxmatch determins whether the item shows as disabled or enabled
                    if('ctxmatch' in dom_data) {
                        //each affected dom ctx item can have multiple targets
                        if(typeof dom_data.ctxmatch == 'object'){
                            $.each(dom_data.ctxmatch, function(idx, dom_ctx){
                                //loop over each context-menu item
                                _target.find('.context-menu-option').each(function(idx,value) {
                                    var ctx_menuitem_data = $(this).data();
                                    //has context and context equals that of dom-item
                                    if('ctx' in ctx_menuitem_data){
                                        if(ctx_menuitem_data.ctx == dom_ctx){
                                            $(this).removeClass('ui-state-disabled');
                                        }
                                    }
                                });
                            });
                        }else if(typeof dom_data.ctxmatch == 'string'){
                            console.log(dom_data.ctxmatch);
                            _target.find('.context-menu-option').each(function(idx,value) {
                                var ctx_menuitem_data = $(this).data();
                                //has context and context equals that of dom-item
                                if('ctx' in ctx_menuitem_data){
                                    if(ctx_menuitem_data.ctx == dom_data.ctxmatch){
                                        $(this).removeClass('ui-state-disabled');
                                    }
                                }
                            });
                        }
                    }
                    //showID/hideID hides or shows items based on the showID matching between target dom to context dom
                    $.each($('#'+ctx.opts.id+' > .context-menu-option'), function(idx, option_element){
                        var _option_data = $(this).data();
                        if('ctxShowid' in _option_data && 'ctxShowid' in dom_data){
                            if(_option_data.ctxShowid == dom_data.ctxShowid){
                            $(this).removeClass('ui-state-hidden');
                            }
                            else {
                            $(this).addClass('ui-state-hidden');
                            }
                        }
                        else if('ctxHideid' in _option_data && 'ctxHideid' in dom_data) {                            
                            if(_option_data.ctxHideid == dom_data.ctxHideid){
                                $(this).addClass('ui-state-hidden');
                            }
                            else {
                                $(this).removeClass('ui-state-hidden');
                            }
                        }
                        else {
                            //$(this).removeClass('ui-state-hidden');
                        }
                    });
                //Show our context menu if there is at least one option that's not supposed to be hidden,
                if($(_opts).filter(':not(.ui-state-hidden)').length > 0) {
                    _target.css('left',event.pageX - 10);
                    _target.css('top',event.pageY - 10);
                    _target.css('cursor','default');
                    _target.show();
                    event.preventDefault();
                }
            }
        }

        ctx.reload_context = function(context_data){
            if(context_data.length > 0){
                $('#'+ctx.opts.id).empty();
                //load context data in id-container
                $('#'+ctx.opts.id).html(context_data);
                $(ctx.opts.anchor).undelegate(ctx.opts.delegate+' div').delegate(ctx.opts.delegate+' div','contextmenu', ctx.process_context);
            }
            else {
                $(ctx.opts.anchor).undelegate(ctx.opts.delegate+' div','contextmenu',ctx.process_context);
                $('#'+ctx.opts.id).empty();
            }
        }

        ctx.reload = function(context_data) {

            if(context_data !== undefined){
                ctx.reload_context(context_data);
            }
            else if(ctx.opts.uri !== undefined){
                application.ws.remote(ctx.opts.uri,{},function(response){
                    ctx.reload_context(response.data.dom.context);
                });
            }
            else {
                console.warn('Invalid reload options');
            }
        }

        ctx.load_context();
    }

    $.extend({
        context: function(params) {            
            return new CTX($.extend({},$.ctx_defaults, params));
        }
    });

})(jQuery);