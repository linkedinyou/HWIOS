Clients and Profiles
====================

Client is the HWIOS concept of a persistent user, that needs to set/get properties both from a persistent connection(a tranport) and from HTTP requests
within Django. It has a Profile, which is nothing more than a reference to the modified django user if logged in. Otherwise it is a reference to an anonymous
empty profile object. The client is not the same as the transport, because some of the client's properties have to be set from a
django http-view. This is especially true for the http bootstrapping view. At that poiunt, the client doesn't have a transport yet,
but things like language-preferences(found in the http-headers) can already be linked to the client from there.


Code References
---------------
.. automodule:: services.web_ui.models.profiles
   :members:
   :show-inheritance:

.. automodule:: services.web_ui.auth.default
   :members:
   :show-inheritance:

.. automodule:: services.web_ui.models.client
   :members:
   :show-inheritance:

.. automodule:: services.web_ui.models.ws_auth
   :members:
   :show-inheritance:

.. automodule:: services.web_ui.models.dj_tracker
   :members:
   :show-inheritance:
       