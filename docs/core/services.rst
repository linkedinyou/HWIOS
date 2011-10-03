Services
========

HWIOS can run multiple twisted services in the main application loop, which makes it easier to interact with multiple services.
Currently there are three services, all listening on their own port. The DSM service is an example of one service communicating
to another(Web-UI). Listed below you find a small overview of the current services and it's code references.

Web-UI Service
~~~~~~~~~~~~~~
The main websocket and HTTP service for HWIOS runs on port 80 by default. This service contains all web and websocket related
data and handlers. The service makes use of several resources. It uses a modified twisted site handler(txwebsocket) to
manage websocket connections, django is served through a twisted wsgi container, the media and docs directories are served 
as gzip-compatible staticfile resource, and webdav is served through wsgidav. All services can run on the same port. Within the
daemonize mode, multiple threads are enabled to handle connections.

.. automodule:: services.web_ui.service
   :members:
   :show-inheritance:


DSM Service
~~~~~~~~~~~
Distributed Service Management service for Teknon daemons. The service listens on port 7999 by default, and uses the twisted perspective broker protocol.
DSM in HWIOS looks a bit like regular websocket clients connecting. The teknon daemon on some system tries to open a connection to the DSM-server in HWIOS
using a moderator's credentials. Once the teknon daemon is authenticated and allowed to log in to HWIOS, the HWIOS system is free to call predefined methods
within that teknon daemon. The web-ui service conveniently arranges the Teknon daemons on the browser-screen and makes interacting with them easy by
providing the necessary buttons and event-listeners.

.. automodule:: services.dsm.service
   :members:
   :show-inheritance:

TMS Service
~~~~~~~~~~~
The Tile Map Service is related to virtual world mapping, and runs as a HTTP-service on port 8001 by default. The TMS-map structure can be viewed with any
compatible map-viewer, like openstreetmap or Marble. Tiles are accessible from the /tiles/ directory at http://myhost.org:8001/tiles/. The TMS-service is meant to
blur the seperation between virtual world and real world, by combining real-world maps with virtual world maps. This research produced an efficient tile-mapping algorithm
that is able to render *cells* (regions with multiple zoomlevels) on top of a map like OpenStreetMap. It's sad that further integration into the viewer haven't made it so far,
because it requires some extensive changes to the Secondlife viewer-code or switching to a different platform(like Tundra), and design a new way to supply mapping
from the virtual world system.

.. automodule:: services.tms.service
   :members:
   :show-inheritance:






