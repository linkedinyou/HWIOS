#!/bin/bash
./requirejs/build/build.sh name=app out=deploy/app.js baseUrl=.
./requirejs/build/build.sh name=modules/ui out=deploy/modules/ui.js baseUrl=.
./requirejs/build/build.sh name=modules/settings out=deploy/modules/settings.js baseUrl=.
./requirejs/build/build.sh name=modules/messenger out=deploy/modules/messenger.js baseUrl=.
./requirejs/build/build.sh name=modules/wiki out=deploy/modules/wiki.js baseUrl=.
./requirejs/build/build.sh name=modules/profiles out=deploy/modules/profiles.js baseUrl=.
./requirejs/build/build.sh name=modules/pad out=deploy/modules/pad.js baseUrl=.
./requirejs/build/build.sh name=modules/pages out=deploy/modules/pages.js baseUrl=.
./requirejs/build/build.sh name=modules/teknon out=deploy/modules/teknon.js baseUrl=.
./requirejs/build/build.sh name=modules/opensim out=deploy/modules/opensim.js baseUrl=.
./requirejs/build/build.sh name=modules/blog out=deploy/modules/blog.js baseUrl=.
./requirejs/build/build.sh name=modules/activity out=deploy/modules/activity.js baseUrl=.
./requirejs/build/build.sh name=modules/my_mod out=deploy/modules/my_mod.js baseUrl=.