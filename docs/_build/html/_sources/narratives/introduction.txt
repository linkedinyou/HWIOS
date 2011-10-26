============
Introduction
============

The HWIOS project was initiated in august 2009 as a web-based user interface for the Opensimulator virtual world platform,
which is - due to it's decentralized grid-like structure - a daunting environment to manage for non-technical orientated users.
The start of the project was the result of lessons-learned during development of a php-based prototype called WiXTD. WiXTD was
the first trial to a one-page web-ui; it used xhr-requests and dom manupilation with jquery to update page content. HWIOS was initially
just a personal endeavour to learn more about django, but slowly grew into what it is today: a general purpose realtime collaborative websocket-cms.

The project used django from the start in combination with apache for deployment and the django development server for debugging.
Twisted support was added initially as a replacement for apache deployment, but it turned out to be the trigger to switch to a
websocket-based infrastructure as well. The websocket connection was put to the test by writing a simple messenger first. All existing
opensim management views were then refactored to use the websocket as well after initial tests showed that websocket communication was
far more efficient, faster and especially more suitable for server-push than http.

An url-based websocket function-router was designed, in order
to make the routing process as clear as it is with http-based routing. From then on, the focus switched more and more from
development of opensim management tools to implementation of general realtime collaborative features like a collaborative text-editor, \
multi-user paint and notification systems. While Opensim is still supported as an optional module in HWIOS nowadays,
it's core purpose now has become to offer an open platform for writing efficient networked web-applications,
using tools and mimicking paradigms that are well known to web-developers.


Design
------

HWIOS acts like a regular networking application, since it uses persistent websocket connections instead of http-based workarounds like comet/long polling.
Loading an url in the browser's navigation bar works a bit differently from regular web-software, due to the persistent state the client's browser has to be in to
maintain the websocket connection. Retrieving a new url without modification would refresh the page, and destroy the client's state and connection. This is why HWIOS
is using a one-page approach in which content is dynamically altered and injected into the DOM. All serverside urls point to the same content; the bootstrapping procedure.
The bootstrapping takes care of loading initial css, html and javascript modules.

The javascript logic then opens a websocket connection to the HWIOS server,
registers methods that the server can route to, and routes the url in the navigation bar to a part of the javascript application, which in turn handles the actual
view-logic and data retrieval from the server using websocket requests that include urls as well. The HWIOS server routes these custom requests to a view,
and returns data to the client, and optionally send data to other clients which reside in the websocket clientpool. Each view a client tries to open,
is being tracked by HWIOS. This makes it possible to create client-aware pages, in which you can trigger content-updates based on an url, instead of a direct client-list.
These filters use regular expressions, so they are quite flexible...