Pad Module
==========
The pad module provides a simple collaborative painting application. It offers remote mouse-cursor sharing and basic paint functionality,
like brush, fill, shape and text. It's a proof of concept, initially started to show the responsiveness nature of websockets, but can
be extended to offer more useful functionality, like offering a collaborative space to create presentations and flowcharts.
Lately there has been some interesting development in the field of vector-graphics and html5, getting available within the
canvas element through libraries like fabric.js and paper.js. Further development should probably go in that direction. Another
useful thing would be a serverside canvas renderer, so the initial image-data can be send(which is faster), instead of only a
log of operations.


Code References
---------------
.. automodule:: services.web_ui.models.pad
   :members:
   :show-inheritance:

.. automodule:: services.web_ui.controllers.ws.pad
   :members:
   :show-inheritance:


