Installation
============

Currently HWIOS is supposed to work on all UNIX systems like Linux, OSX and FreeBSD. However, due to limited resources, it has only been tested on
Linux(Ubuntu & Archlinux) so far. In theory the software should also be able to run on Windows, although that may require some additional compatibility code.
Problems may well as be only occur in the optional Teknon client, in which services make use of named pipes. Those are AFAIK not supported on Windows.


HWIOS Dependencies
------------------
* twisted 11 (networking)
* django 1.3 (web framework)
* wsgidav (webdav shares)
* python-graph-core (plasmoid wiki graph visualisation)
* mysql-python (advised when using cpython)
* ujson (json serializer)
* pyopenssl (optional)
* pil


Optional
++++++++

* Sphinx (Render documentation)
* Node.js (JS optimalization)
* Teknon DSM daemon (Distributed service management)
* Wdfs (Teknon dav-mounting for IAR/OAR sharing, \*NIX only)
* Pymysql (use this when running with pypy)
* Mono (VM for OpenSimulator)

UNIX Installation
-----------------

* Create a system user called hwios, and login with this new account

::
    
 adduser hwios 
 su hwios

* Get all python dependencies and install HWIOS

::
    
 sudo pip install twisted django wsgidav mysql-python ujson pyopenssl pil python-graph-core pyparsing django-autoslug markdown pymysql
 git clone git://github.com/phrearch/hwios.git ~/hwios
 cd ~/hwios
 cp hwios.ini.example hwios.ini
 vim hwios.ini
 
.. warning::
 It is important that the uri under the general section in hwios.ini is the same as the address you type in your browser. This may be both a domain name or an ip-address.
 
* Fill in your mysql credentials, load the setup and startup HWIOS

.. note::
 HWIOS asks you to provide a first-name, last-name and a password for the initial administrator profile.
 
::
    
 ./hwios --setup
 sudo ./hwios --debug

.. note::
 Point your html5 browser to the uri you provided in hwios.ini and check whether the interface loads succesfully.



Optional
--------

OpenSimulator
+++++++++++++

* Download and prepare vanilla OpenSimulator

::
    
 cd ~
 git clone git://opensimulator.org/git/opensim /home/hwios/simulator
 cd simulator
 sh runprebuild.sh
 nant
 cd bin
 mysqladmin -u root -pMYSQLPW create grid create sim_9000
 cp OpenSim.ini.example OpenSim.ini
 vim OpenSim.ini

* Enable remote admin, set it's password ('foobar' for dev-purposes) and uncomment **//Include-Architecture = "config-include/GridHypergrid.ini"//** at the bottom of the file

::
    
 cp Robust.HG.ini.example Robust.HG.ini
 vim Robust.HG.ini

* Edit database and url-settings in Robust.HG.ini ('grid' db-name is used by default in HWIOS)

::
    
 screen -S robust
 mono Robust.exe -inifile=Robust.HG.ini
 <ctrl><a>+<d>
 
.. note::
 The grid-server filled the grid database with tables if everything went well. Navigate to the opensim section in HWIOS, and click on the sync button
 to create a linked opensim account.
 
* Setup the Simulator

::

 cd /home/hwios/simulator/bin
 cp config-include/GridCommon.ini.example config-include/GridCommon.ini
 cp config-include/FlotsamCache.ini.example config-include/FlotsamCache.ini
 vim config-include/GridCommon.ini

.. note::
 Edit the mysql database settings for the simulator(use 'sim_9000' for instance). Make sure you uncomment sqlite in the process.
 Point the service connectors(AssetServerURI, InventoryServerURI, etc.) to your local ip (for dev, for production use lan/wan ip)

* Start the simulator

::

 cd ..
 mono OpenSim.exe
 New region name []: test
 Region UUID [4e939f2c-89cb-4449-9eb9-409bfa5ff4dd]:<enter>
 Region Location [1000,1000]:<enter>
 Internal IP address [0.0.0.0]:<enter>
 Internal port [9000]:<enter>
 Allow alternate ports [False]:<enter>
 External host name [SYSTEMIP]:127.0.0.1
 Do you wish to join an existing estate? [no]:<enter>
 New estate name [My Estate]:<enter>
 state owner first name [Test]: test
 Estate owner last name [User]: test

* Close the simulator and grid-server if they keep running. They will be running in a Teknon subprocess in a moment. Try to debug any errors before preceding.

::
 <ctrl><c>
 screen -r robust
 <ctrl><c>
 exit
 cd ~

* Install and setup the Teknon DMS client

::
 git clone git://github.com/phrearch/teknon.git ~/teknon
 cd ~/teknon
 mkdir webdav
 cp teknon.ini.example teknon.ini
 cp services.ini.example services.ini

.. note::
 teknon.ini has the config parameters to connect to the HWIOS server. The services.ini defines local services that are controlled by Teknon.
 The example services.ini file reflects the values used in this manual, so you don't need to change anything there. To login the teknon client,
 you need to use the credentials of a HWIOS admin user(for example our account that was created during the HWIOS setup).
 
* Start teknon

::
 sudo ./teknon --debug

.. note::
 Everything went right if you'll see that the client connected to HWIOS(something like *[Broker,client] joined group CLIENTS*), and no error shows indicating a
 webdav mount-failure occured.

* Login to HWIOS and go to the backend's dsm controlpanel. In the services tab you should see a "Robust Grid" and "Simulator 1" service listed.
* Check the ROBUST service entry and start the service
* Check the Simulator service entry and start the service
* Render the initial map from backend > settings > maps > Render

The OpenSimulator tools should now allow you to manage regions of that simulator. You can also add new teknon clients from different hosts and/or add new simulators
the same way. When creating new regions, you just select which simulator you want it to be running on.