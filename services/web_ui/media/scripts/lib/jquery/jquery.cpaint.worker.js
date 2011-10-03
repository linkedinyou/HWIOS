onmessage = function (event) {
    //Based on http://www.williammalone.com/articles/html5-canvas-javascript-paint-bucket-tool/
    var pixeldata = event.data.pixeldata;
    var startXY = event.data.startXY;
    var fillColor = event.data.fillColor;
    var startColor = event.data.startColor;
    var width = event.data.width;
    var height = event.data.height;
        //css rgba uses 0-1 as alpha, instead of 0-255 which is used in canvas imagedata
        fillColor[3] = parseInt(fillColor[3] * 255);        
        pixelStack = [startXY];
        while(pixelStack.length) {
            var newPos, x, y, pixelPos, reachLeft, reachRight;
            newPos = pixelStack.pop();
            x = newPos[0];
            y = newPos[1];
            
            pixelPos = (y*width + x) * 4;
            while(y-- >= 0 && matchStartColor(pixelPos)){
                pixelPos -= width * 4;
            }
            pixelPos += width * 4;
            ++y;
            reachLeft = false;
            reachRight = false;
            while(y++ < height-1 && matchStartColor(pixelPos)) {
                colorPixel(pixelPos);
                if(x > 0) {
                    if(matchStartColor(pixelPos - 4)) {
                        if(!reachLeft){
                        pixelStack.push([x - 1, y]);
                        reachLeft = true;
                        }
                    }
                    else if(reachLeft) {reachLeft = false;}
                }            
                if(x < width-1) {
                    if(matchStartColor(pixelPos + 4)) {
                        if(!reachRight) {
                        pixelStack.push([x + 1, y]);
                        reachRight = true;
                        }
                    }
                    else if(reachRight) {
                    reachRight = false;
                    }
                }                    
                pixelPos += width * 4;
            }        
            //canvas.ctx.putImageData(colorLayer, 0, 0);
        }
        postMessage({status: {code:'FLOODFILL_OK'}, pixeldata: pixeldata});
        
        function matchStartColor(pixelPos) {
        var r = pixeldata.data[pixelPos];    
        var g = pixeldata.data[pixelPos+1];  
        var b = pixeldata.data[pixelPos+2];
        var a = pixeldata.data[pixelPos+3];
        return (r == startColor[0] && g == startColor[1] && b == startColor[2] && a == startColor[3]);
        }

        function colorPixel(pixelPos) {
        pixeldata.data[pixelPos] = fillColor[0];
        pixeldata.data[pixelPos+1] = fillColor[1];
        pixeldata.data[pixelPos+2] = fillColor[2];
        pixeldata.data[pixelPos+3] = fillColor[3];
        }
   
};    
