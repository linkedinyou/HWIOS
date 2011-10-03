//Based on http://www.scottlogic.co.uk/2011/02/web-workers-part-2-using-jquery-deferred/
//Add a work helper function to the jQuery object
$.work = function(args) { 
    var def = $.Deferred(function(dfd) {
        var worker;
        if (window.Worker) {
            //Construct the Web Worker
            var worker = new Worker(args.file); 
            worker.onmessage = function(event) {
                //If the Worker reports success, resolve the Deferred
                dfd.resolve(event.data); 
            };
            worker.onerror = function(event) {
                //If the Worker reports an error, reject the Deferred
                dfd.reject(event); 
            };
            worker.postMessage(args.args); //Start the worker with supplied args
        } else {
            //Need to do something when the browser doesn't have Web Workers
        }
    });
 
    //Return the promise object (an "immutable" Deferred object for consumers to use)
    return def.promise(); 
};