GIS-Related
===========

The HWIOS TMS-service offers a specialized cell renderer and map-client, with the idea of having a virtual world layer on top of the
real world layer available some day. The non-mashup mode can be used one-to-one with OpenSim and Secondlife viewer 2 clients.
It will only show the OpenSim map without any real world layer like OSM involved. As soon as the Secondlife viewer has been modified
to work with the TMS service, plans can be made to integrate and mashup objects in more exotic ways. Some cooperation with opensim
developers is necessary here. Django has extensive GIS-support through geo-django, which could help to define the virtual world layer
on top of the real world. This kind of system would work really well for augmented-reality applications, since the avatar location and
mobile location can be synchronized, while the client is moving in real space. Virtual objects are then able to interact with the
mobile client based on location. 

Code References
---------------
.. automodule:: services.tms.service
   :members:
   :noindex:
   :show-inheritance:

.. automodule:: services.tms.processor
   :members:
   :show-inheritance:

.. automodule:: services.tms.grabber
   :members:
   :show-inheritance:

.. automodule:: services.tms.tiler
   :members:
   :show-inheritance:

