/*
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

define('lib/tools/maps',[
'lib/openlayers/OpenLayers',
],
function(){

OpenLayers.Layer.OSM.Mapnik = OpenLayers.Class(OpenLayers.Layer.OSM, {
    initialize: function(name, options) {
        var url = ["http://a.tile.openstreetmap.org/${z}/${x}/${y}.png","http://b.tile.openstreetmap.org/${z}/${x}/${y}.png","http://c.tile.openstreetmap.org/${z}/${x}/${y}.png"];
        options = OpenLayers.Util.extend({}, options);
        var newArguments = [name, url, options];
        OpenLayers.Layer.OSM.prototype.initialize.apply(this, newArguments);
    },CLASS_NAME: "OpenLayers.Layer.OSM.Mapnik"
});

var map;
var popup;
var click;
var panZoomBar;
var osmaps_cache;
var osmaps_started = false;
var map_uri = '';
var rebuild = false;
/*
Updates map settings when administrator makes changes
*/
    
function bind_functions(){
    application.functions.maps = {};
    application.functions.maps.route = function(uri, push_history) {
        routes = [
            [XRegExp('^/maps/$'),application.functions.maps.view_maps],
        ];
        application.route_uri_to_mod_function(uri, routes, push_history);
    }
        
    application.functions.maps.view_maps = function(){
        application.ws.remote('/maps/',{},function(response){
            application.functions.ui.transition(response.data.dom.main, $('.main'));
            connect();
        });  
    }
}

function bind_ws() {
    application.ws.method('/data/maps/settings/update/',function(tms_settings){
    application.settings.services.tms = tms_settings;
    rebuild = true;
    });
}



    function tile2lonlat(zlevel,tile_x,tile_y) {
        n = Math.pow(2,zlevel);
        lon_deg = (tile_x / n) * 360.0 - 180.0;
        lat_rad = Math.atan(Math.sinh(Math.PI * (1 - 2 * tile_y / n)));
        lat_deg = lat_rad * 180.0 / Math.PI;
        return new Array(lon_deg,lat_deg);
    }


    function init(data) {
        if (rebuild) {
        rebuild = false;
            if (typeof grid != 'undefined') {
            delete grid;
            }
            if (typeof osm_layer != 'undefined') {
            delete osm_layer;
            }
            if (typeof map != 'undefined') {
            map.destroy();
            }
        return true;
        }
    OpenLayers.ImgPath = "/media/themes/"+data.theme+"/css/images/map/";
    return false;
    }


    function get_my_url(bounds) {
    var res = this.map.getResolution();
    var x = Math.round ((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
    var y = Math.round ((this.maxExtent.top - bounds.top) / (res * this.tileSize.h));
    var z = this.map.getZoom();
    var path = z + "/" + x + "/" + y + "." + this.type+"?cache="+application.settings.services.tms.cache;
    var url = this.url;
        if (url instanceof Array) {
        url = this.selectUrl(path, url);
        }
    return url + path;
    }


    function setupMap(data,render) {
        init(data);
        if(application.settings.services.tms.osm == true) {
            var osm_res = new Array('156543.0339','78271.51695','39135.758475','19567.8792375','9783.93961875','4891.96980937','2445.98490469','1222.99245234',
            '611.496226172','305.748113086','152.874056543','76.4370282715','38.2185141357','19.1092570679','9.55462853394','4.77731426697','2.38865713348','1.19432856674');
            $('head').append("<link type='text/css' href='http://"+application.settings.services.web_ui.uri+"/media/themes/"+data.theme+"/css/osm_map.css' media='screen' rel='stylesheet' />");
            map = new OpenLayers.Map ('map',{
                controls:[new OpenLayers.Control.Navigation(),new OpenLayers.Control.PanZoomBar(),new OpenLayers.Control.MousePosition()],
                maxExtent: new OpenLayers.Bounds(-20037508.34,-20037508.34,20037508.34,20037508.34),
                units: 'm',
                theme: null,
                projection: "EPSG:900913",
                displayProjection: new OpenLayers.Projection("EPSG:4326"),
                url: map_uri});		
            osm_grid = new OpenLayers.Layer.TMS("map", map.url+"/tiles/", { 'type':'png', 'getURL':get_my_url, displayOutsideMaxExtent: true});
            osm_grid.setIsBaseLayer(false);
            mapnik = new OpenLayers.Layer.OSM.Mapnik("Mapnik",{resolutions: osm_res});
            mapnik.setIsBaseLayer(true);
            map.addLayers([osm_grid,mapnik]);
            center_lonlat = tile2lonlat(application.settings.services.tms.osm_ztop,application.settings.services.tms.center[0],application.settings.services.tms.center[1]);
            var lonlat = new OpenLayers.LonLat(center_lonlat[0], center_lonlat[1])
            lonLat = new OpenLayers.LonLat(lonlat.lon, lonlat.lat).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject());
            map.setCenter(lonLat, data.center[2]);
        }
        else {
            $('head').append("<link type='text/css' href='http://"+application.settings.services.web_ui.uri+"/media/themes/"+data.theme+"/css/raw_map.css' media='screen' rel='stylesheet' />");
            gridsize = Math.pow(2,application.settings.services.tms.raw_ztop);
            boundspx = gridsize * 256;
            map = new OpenLayers.Map ({
                controls:[new OpenLayers.Control.Navigation(),new OpenLayers.Control.PanZoomBar()],
                numZoomLevels:data.zlevels+1,
                maxExtent: new OpenLayers.Bounds(0,-boundspx,boundspx,0),
                maxResolution:gridsize,
                theme: null,
                url: map_uri});
            raw_grid = new OpenLayers.Layer.TMS("map", map.url+"/tiles/", { 'type':'png', 'getURL':get_my_url, displayOutsideMaxExtent: true});
            raw_grid.setIsBaseLayer(true);
            map.addLayer(raw_grid);
            if (data.center != undefined) {
                center = new OpenLayers.LonLat(data.center[0]*256,-data.center[1]*256);
                if (map.isValidLonLat(center)) {
                map.setCenter(center,data.center[2]);
                }
                else {
                center = new OpenLayers.LonLat(1000,1000);
                map.setCenter(center,data.center[2]);
                }
            }
            else {
            map.setCenter(new OpenLayers.LonLat(boundspx/2,-boundspx/2),3);
            }
        }
        if (render == true) {
        map.render('map');
        }
        OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {                
            defaultHandlerOptions: {'single': true,'double': false,'pixelTolerance': 0,'stopSingle': false,'stopDouble': false}
            ,initialize: 
                function(options) {
                    this.handlerOptions = OpenLayers.Util.extend({}, this.defaultHandlerOptions);
                    OpenLayers.Control.prototype.initialize.apply(this, arguments); 
                    this.handler = new OpenLayers.Handler.Click(this, {'click': this.trigger}, this.handlerOptions);
                }
            ,trigger: 
                function(e) {
                    var lonlat = map.getLonLatFromViewPortPx(e.xy);
                    if(application.settings.services.tms.osm) {
                        lonlat = lonlat.transform(new OpenLayers.Projection("EPSG:900913"),new OpenLayers.Projection("EPSG:4326")); 
                    }

                    application.ws.remote('/data/maps/cells/read/',{lonlat:[lonlat.lon,lonlat.lat]},function(response){
                        var lonlat = new OpenLayers.LonLat(response.lonlat[0], response.lonlat[1]);
                            if(application.settings.services.tms.osm) {
                            lonlat = lonlat.transform(new OpenLayers.Projection("EPSG:4326"),new OpenLayers.Projection("EPSG:900913")); 
                            }
                        var popswitch = 0;
                            if(map.popups.length > 0) {
                            map.removePopup(popup);
                            }
                            if(response.name!=null) {
                            $(document).trigger('MAP_REGION_LOCATION',[response.x,response.y]);
                            var info = "<div class='hwios-widget'><div class='ui-widget-header'><span class='ui-icon menu-icon ui-icon-pin-s'></span><span>"+gettext("Region")+" "+response.name+"</span></div><div class='ui-widget-content ui-corner-bottom'><table id='map_popup_info'>" +
                            "<tr><td><b>"+gettext("Address")+":</b></td><td>" + response.ip+":"+response.port + "</td></tr>" +
                            "<tr><td><b>"+gettext("Position")+":</b></td><td> " + response.x + "," + response.y + "</td></tr></table></div></div>";
                            popswitch = 1;
                            }
                            else {
                            $(document).trigger('MAP_FREE_LOCATION',[response.x,response.y]);
                            }
                            if(popswitch > 0) {
                            popup = new OpenLayers.Popup("regionpopup",lonlat,new OpenLayers.Size(150,200),info,true);
                            popup.autoSize = true;
                            map.addPopup(popup);
                            }
                    
                    });
                }
        });
        if (panZoomBar === undefined) {
            panZoomBar = new OpenLayers.Control.PanZoomBar();	
        }	
        map.addControl(new OpenLayers.Control.PanZoomBar());
        click = new OpenLayers.Control.Click();
        map.addControl(click);
        click.activate();
    }
    
    function connect() {
            if(typeof(application.settings.services.tms) !== 'undefined') {
                if(application.settings.map_enabled == true) {
                reconnect();
                }
                else {
                if(application.settings.services.tms.ssl) {map_uri = 'https://'+application.settings.services.tms.uri;}
                else {map_uri = 'http://'+application.settings.services.tms.uri;}
                setupMap(application.settings.services.tms,true);
                application.settings.map_enabled = true;
                }
            }
            else {
            $('#map').html('<div class=\'osmaps-error\'>Error 1: Map-service not defined yet...</div>').addClass('osmaps-disabled');
            }        
    }


    function reconnect() {
        var changed = init(application.settings.services.tms);
        if (!changed) {
            if (application.settings.services.tms.osm) {
            center_lonlat = tile2lonlat(application.settings.services.tms.osm_ztop,application.settings.services.tms.center[0],application.settings.services.tms.center[1]);
            var lonlat = new OpenLayers.LonLat(center_lonlat[0], center_lonlat[1])
            var center = new OpenLayers.LonLat(lonlat.lon, lonlat.lat).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject());
            }
            else {
            var center = new OpenLayers.LonLat(application.settings.services.tms.center[0]*256,-application.settings.services.tms.center[1]*256);
            }
            if (!map.isValidLonLat(center)) {
            alert('Invalid center!');
            }
            map.setCenter(center, application.settings.services.tms.center[2]);
            map.render('map');
        }
        else {
        setupMap(application.settings.services.tms,true);
        }
    }
    
function bind_events(){
    
}

function unbind_events(){
    
}

return {
    init: function(uri, push_history) {
        bind_functions();
        bind_ws();
        application.functions.maps.route(uri, push_history);
        return 'maps';
    },
    load: function(uri, push_history) {
        bind_events();
        application.functions.maps.route(uri, push_history);
    },
    clean_up: function() {
        unbind_events();
    },
    connect: function() {
        if(typeof(application.settings.services.tms) !== 'undefined') {
            if(application.settings.map_enabled == true) {
            reconnect();
            }
            else {
            if(application.settings.services.tms.ssl) {map_uri = 'https://'+application.settings.services.tms.uri;}
            else {map_uri = 'http://'+application.settings.services.tms.uri;}
            setupMap(application.settings.services.tms,true);
            application.settings.map_enabled = true;
            }                
        }
        else {
        $('#map').html('<div class=\'osmaps-error\'>Error 1: Map-service not defined yet...</div>').addClass('osmaps-disabled');
        }
    },
    reset_cache: function(){
        application.settings.services.tms.cache = new Date().getTime();
    },
    get_zoom: function() {
        return map.getZoom();
    },
    center_lonlat: function(lon, lat, zoom) {
        zoom === undefined ? zoom = application.settings.services.tms.center[2] : zoom = zoom;
        var lonlat = new OpenLayers.LonLat(lon, lat)
        var center = new OpenLayers.LonLat(lonlat.lon, lonlat.lat).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject());
        map.setCenter(center, zoom);
    },
}
});