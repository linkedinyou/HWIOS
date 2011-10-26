Teknon Module
=============
The teknon module provides a distributed service management client-pool for teknon daemons. It's basically a twisted pb-server, listening
for incoming Teknon deamons that want to login to HWIOS. Teknon logins use the same authentication model as django; moderators can use their
credentials to login these service daemons, which are then controllable through the HWIOS webinterface. The teknon project started when
realtime notification of service changes were needed, and the existing xmlrpc implementation(osservices) turned out to be insufficient. 

Code References
---------------
.. automodule:: services.web_ui.controllers.ws.teknon
   :members:
   :show-inheritance:

.. automodule:: services.dsm.service
   :members:
   :noindex:
   :show-inheritance:

.. automodule:: services.dsm.dsm_server
   :members:
   :show-inheritance:

       