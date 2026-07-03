"""
deploy.py: Build and deploy a versioned application to Opalstack.
"""
import getpass
import logging
import os
import subprocess
import sys

from fabric import Connection
from fabric.transfer import Transfer
from jinja2 import Environment, PackageLoader
from mongoengine import connect

from .create_wsgi import create_wsgi
from .models import App, Server
from .version import __version__

logging.basicConfig(level=logging.INFO)

# Configuration via environment variables with sensible defaults.
SSH_USER = os.environ.get("QS_SSH_USER", getpass.getuser())
SSH_KEY = os.environ.get("QS_SSH_KEY", os.path.expanduser("~/.ssh/id_rsa"))


def deploy(app_name: str):
    """
    Identify the tag for the current commit and deploy it to the server.

    This was relatively easy when only using one server, but now we need to
    deal with multiple servers.
    """
    connect('opalstack')

    #
    # Locate the tag for the current commit - this can
    # fail if the same commit is given multiple tags
    #
    cmd = ["git", "tag", "--points-at", "HEAD"]
    version = subprocess.run(cmd,
                             capture_output=True,
                             text=True
    ).stdout.strip()[1:]
    if not version:
        sys.exit("Unable to find any tag for current commit")

    # Get the app description from the database
    try:
        app = App.objects.get(name=app_name)
    except App.DoesNotExist:
        sys.exit(f"Application {app_name!r} not found: do you need to run opalsync?")
    if not app.port:
        sys.exit("App has no port number: do you need to run opalsync?")

    try:
        server = Server.objects.get(id=app.server)
    except Server.DoesNotExist:
        sys.exit(f"App {app_name} has no server: cannot proceed.")

    # Create server connection
    c = Connection(
        host=server.hostname,
        user=SSH_USER,
        connect_kwargs={
            "key_filename": SSH_KEY,
        },
    )

    def remote(cmd):
        "Run a single remote command."
        return c.run(cmd)

    # Establish project and module names
    proj_name, v = subprocess.run(["uv", "version"], capture_output=True, text=True).stdout.split()
    if v != version:
        sys.exit(f"`uv version` ({v}) and `git tag` ({version}) disagree on version")
    mod_name = proj_name.replace("-", "_")
    print(f"qs{__version__} delivering {app_name} v{version}")

    # Create deployment-specific files
    loader = PackageLoader('qs', 'templates')
    jenv = Environment(
        loader=loader,
        autoescape=False
    )
    for filename in ('kill', 'start', 'stop', 'uwsgi.ini'):
        with open(filename, 'w') as f:
            tpl = jenv.get_template(filename)
            content = tpl.render(
                PROJECT=app.name, PORT_NO=app.port, VERSION=version,
                HOME_DIR=f"/home/{SSH_USER}",
            )
            f.write(content)
    with open('version.txt', 'w') as f:
        f.write(f"{version}\n")
    create_wsgi(name=mod_name, port=app.port)

    # Create a distribution to send up the wire to the server.
    # Note that there is no longer a need to create a wheel.
    cmd = (fr'(gtar cf {proj_name}-{version}.tgz --no-xattrs '
           './kill ./stop ./start ./uwsgi.ini ./wsgi.py ./src ./pyproject.toml ./README.md)')
    c.local(cmd)

    # Confirm the target directory exists before running anything
    # destructive in it: a missing or renamed app dir must abort loudly
    # rather than letting `rm -rf` run in an unexpected working directory.
    app_dir = f"apps/{app.name}"
    if not c.run(f"test -d {app_dir}", warn=True).ok:
        sys.exit(f"Remote app directory {app_dir!r} not found on {server.hostname}: "
                 "cannot deploy.")

    # Stop and wipe any existing app, wipe and reinstall.
    # XXX Note that these should really be app-specfic.
    #     Back when the app saved its own versions things
    #     were different! Unlikely to hurt in the meantime.
    with c.cd(app_dir):
        remote("if [ -e stop ] ; then ./stop || echo 'No stop file' ; fi")
        remote("rm -rf .venv *")
        remote("mkdir -p dist tmp")
    Transfer(c).put(f'{proj_name}-{version}.tgz', f'{app_dir}/dist/{proj_name}-{version}.tgz')

    # Now install it server-side!
    with c.cd(app_dir):
        remote(f"tar xvf dist/{proj_name}-{version}.tgz")
        remote("chmod +x start stop kill")
        remote("uv sync")
        remote(f"if [ -e ~/envs/{proj_name} ] ; then "
               f"(cp ~/envs/{proj_name} .env && "
               f"echo >&2 'Env file for project {proj_name} copied'); "
               f"else echo >&2 'No env file for project {proj_name}' ; fi")
        remote("./start")


def deploy_cli():
    args = sys.argv[1:]
    if len(args) != 1:
        sys.exit(f"""\
Usage: {os.path.basename(sys.argv[0])} appname

This delivers the currently checked-out version of the current directory's
application to the named Opalstack app using its version number as
identification.""")
    app_name = args[0]
    deploy(app_name)

if __name__ == '__main__':
    deploy_cli()
