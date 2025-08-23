import os
import subprocess
import sys
from .models import App
from .create_wsgi import create_wsgi

from fabric import Connection
from fabric.transfer import Transfer
from mongoengine import connect
from jinja2 import Environment, PackageLoader

import logging
logging.basicConfig(level=logging.INFO)

DEBUG = True
HOSTS = ['opal5.opalstack.com']
conn = connect('opalstack')

from .version import __version__

VERSION_TEMPLATE = """\

__version__ = "{version}"

"""
def remote(cmd):
    "Run a single remote command."
    if DEBUG:
        print("=", cmd)
    return c.run(cmd)

def deploy(app_name: str):
    """
    Identify the tag for the current commit and deploy it to the server.

    At present this is relatively easy because we are only using one server.
    """
    def remote(cmd):
        "Run a single remote command."
        if DEBUG:
            print("=", cmd)
        return c.run(cmd)

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
        sys.exit("Unable to find tag for this commit")

    # Create server connection
    c = Connection(
        host=HOSTS[0],
        user="sholden",
        connect_kwargs={
            "key_filename": "/Users/sholden/.ssh/id_rsa",
        },
    )

    # Establish project and module names
    proj_name, v = subprocess.run(["uv", "version"], capture_output=True, text=True).stdout.split()
    assert v == version, "`uv version` and `git tag` disagree on version"
    mod_name = proj_name.replace("-", "_")
    print(f"qs{__version__} delivering {app_name} v{version}")

    # Get the app description from the database
    try:
        app = App.objects.get(name=app_name)
    except App.DoesNotExist:
        sys.exit(f"Application {app_name!r} not found: do you need to run opalsync?")
    if not app.port:
        sys.exit("App has no port number: please re-sync by running opalsync.")

    # Create deployment-specific files
    loader = PackageLoader('qs', 'templates')
    jenv = Environment(
        loader=loader,
        autoescape=False
    )
    for filename in ('kill', 'start', 'stop', 'uwsgi.ini'):
        with open(filename, 'w') as f:
            tpl = jenv.get_template(filename)
            content = tpl.render(PROJECT=app.name, PORT_NO=app.port, VERSION=version)
            f.write(content)
    c.local(f'echo {version} > version.txt')
    create_wsgi(name=mod_name, port=app.port)

    # Create a distribution to send up the wire to the server.
    # Note that there is no longer a need to create a wheel.
    cmd = (fr'(gtar cf {proj_name}-{version}.tgz --no-xattrs '
           './kill ./stop ./start ./uwsgi.ini ./wsgi.py ./src ./pyproject.toml ./README.md)')
    c.local(cmd)

    # Create necessary (?) remote directories and deliver the distro.
    # XXX Note that these should really be app-specfic.
    #     Back when the app saved its own versions things
    #     were different! Unlikely to hurt in the meantime.
    with c.cd(f"apps/{app.name}"):
        remote("rm -rf .venv *")
        remote("mkdir -p dist tmp")
    Transfer(c).put(f'{proj_name}-{version}.tgz', f'apps/{app.name}/dist/{proj_name}-{version}.tgz')

    # Now install it server-side!
    # f"ensconce {app.name} {proj_name} {version}"
    with c.cd(f"apps/{app.name}"):
        remote(f"tar xvf dist/{proj_name}-{version}.tgz")
        remote("chmod +x start stop kill")
        remote("uv sync")
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
