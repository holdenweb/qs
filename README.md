## OpalStack Flask Site Generator

This project allows you to build a Flask application
and host it in the OpalStack estate.
Ultimately we plan to manipulate the OpalStack API
to perfom action such as "create site."
For now we ask for your patience
in performing certain operations manually
with the assistance of OpalStack's control panel.

### Creating your site

First, create a new OpalStack application,
selecting "Python/uWSGI" from the "Type" drop-down menu.
We'll write here about an application named **app-name**.
You should, of course, make it avaialble
by registering the app to a siuotable domain name.

After creating your application you should
perform the following command immediately,
precisely once.

     make init

On your development system
the site code should be stored in the _release_ directory.
Each time you deploy
its entire contents will be uploaded
to the OpalStack server,
saved as a release in _apps/version_id_,
and the _myapp_ symbolic link updated
to point to this new version.
Nothing else will transferred to the server.

You deploy the site code with the command

     make deploy VERSION=version_id


In order to see the newly-deployed site
you will need to stop and restart the server.

At present a new virtual environment created,
and the _env_ symbolic link updated
to point to the new virtualenv
for each version you deploy,
until I can figure out a way to avoid it
where possible.

Assuming you don't delete prior versions,
you can roll back to them
simply by updating two symbolic links.
