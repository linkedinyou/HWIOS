/**
 * jQuery mousehold plugin - fires an event while the mouse is clicked down.
 * Additionally, the function, when executed, is passed a single
 * argument representing the count of times the event has been fired during
 * this session of the mouse hold.
 *
 * @author Remy Sharp (leftlogic.com)
 * @date 2006-12-15
 * @example $("img").mousehold(200, function(i){  })
 * @desc Repeats firing the passed function while the mouse is clicked down
 *
 * @name mousehold
 * @type jQuery
 * @param Number timeout The frequency to repeat the event in milliseconds
 * @param Function fn A function to execute
 * @cat Plugin
 */

jQuery.fn.extend({

    mousehold: function(timeout, f) {
        if (timeout && typeof timeout == 'function') {
            f = timeout;
            timeout = 100;
        }
        if (f && typeof f == 'function') {
            var timer = 0;
            var fireStep = 0;
            return this.each(function() {
                jQuery(this).mousedown(function(_event) {
                    fireStep = 1;
                    var t = this;
                    var offsetX = _event.offsetX;
                    var offsetY = _event.offsetY;
                    timer = setInterval(function() {
                        f.call(t, offsetX, offsetY);
                        fireStep = 2;
                    }, timeout);
                });

                clearMousehold = function() {
                    clearInterval(timer);
                    if (fireStep == 1) f.call(this, 1);
                    fireStep = 0;
                }

                jQuery(this).mouseout(clearMousehold);
                jQuery(this).mouseup(clearMousehold);
            })
        }
    }
});