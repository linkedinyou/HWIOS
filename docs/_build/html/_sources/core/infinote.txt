Infinote OT
===========

HWIOS offers asynchronous collaborative text editing through the Operational transformation based infinote protocol. The infinote protocol
became usable for the web, after the MIT-licensed javascript implementation jinfinote (http://www.jinfinote.com/) hit the web.
HWIOS uses jinfinote on the clientside. A python port of jinfinote has been developed to keep track of the common document state on
the server as well. Both together form the OT-based editing system that's available in HWIOS. On the clientside, a javascript module
has been developed to work with the ace code-editor. See the hyki and plasmoid system for some examples...


Code References
---------------
.. automodule:: services.web_ui.models.infinote
   :members: InfinoteEditor, InfinotePool
   :show-inheritance: