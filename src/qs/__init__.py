import os
import subprocess
import sys
from .models import App

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

WSGIPY_TEMPLATE = """\
from {name} import app, application

if __name__ == '__main__':
    app.run(port = {port}, debug = True)
"""
def create_wsgi(name, port=2400):
    with open("wsgi.py", 'w') as f:
        f.write(
            WSGIPY_TEMPLATE.format(
                name=name,
                port=port
            )
        )

def create_wsgi_cli():
    args = sys.argv[1:]
    create_wsgi(*args)

def deliver(c, app, version):
    """
    Actually deliver the code to the remote server and install it.
    """
    def remote(cmd):
        "Run a single remote command."
        if DEBUG:
            print("=", cmd)
        return c.run(cmd)

    proj_name = subprocess.run(cmd, capture_output=True, text=True).stdout.split()[0]
    mod_name = proj_name.replace("-", "_")

    print(f"qs{__version__} delivering {app} v{version}")
    try:
        app = App.objects.get(name=app)
    except App.DoesNotExist:
        sys.exit(f"Application {app!r} not found: do you need to run opalsync?")

    loader = PackageLoader('qs', 'templates')
    jenv = Environment(
        loader=loader,
        autoescape=False
    )

    if not app.port:
        sys.exit("App has no port number: please re-sync by running opalsync.")
    for filename in ('kill', 'start', 'stop', 'uwsgi.ini'):
        with open(filename, 'w') as f:
            tpl = jenv.get_template(filename)
            content = tpl.render(PROJECT=app.name, PORT_NO=app.port, VERSION=version)
            f.write(content)
    c.local(f'echo {version} > version.txt')
    create_wsgi(name=mod_name, port=app.port)
    sys.exit("OK so far?")

    c.local(f'echo {version} > version.txt')
    cmd = fr'(gtar cf {proj_name}-{version}.tgz --no-xattrs -T Manifest.txt wsgi.py dist/{proj_name}-{version}-py3-none-any.whl)'
    c.local(cmd)
    with c.cd(f"apps/{app.name}"):
        remote("mkdir -p html md apps dist envs releases wsgis")
    Transfer(c).put(f'{proj_name}-{version}.tgz', f'apps/{app.name}/releases/{proj_name}-{version}.tgz')
    cmd = f"ensconce {app.name} {proj_name} {version}"
    remote(cmd)


def deploy():
    args = sys.argv[1:]
    if len(args) != 1:
        sys.exit(f"""\
Usage: {os.path.basename(sys.argv[0])} appname

This delivers the currently checked-out version of the current directory's
application to the named Opalstack app using its version number as
identification.""")
    app = args[0]
    cmd = ["git", "tag", "--points-at", "HEAD"]
    version = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()[1:]
    if not version:
        sys.exit("Unable to find tag for this commit")
    c = Connection(
        host=HOSTS[0],
        user="sholden",
        connect_kwargs={
            "key_filename": "/Users/sholden/.ssh/id_rsa",
        },
    )
    return deliver(c, app, version)

if __name__ == '__main__':
    deploy()
