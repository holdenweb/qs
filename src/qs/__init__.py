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

def deliver(c, app, version):
    """
    Actually deliver the code to the remote server and install it.
    """
    def remote(cmd):
        "Run a single remote command."
        if DEBUG:
            print("+", cmd)
        return c.run(cmd)

    print(f"Deploying with qs {__version__}")
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
    # Would it be easier to say what we do want?
    c.local(fr'(gtar cf release-{version}.tgz --no-xattrs -T Manifest.txt *.py kill stop start uwsgi.ini)')

    with c.cd(f"apps/{app.name}"):
        remote("./stop || echo Not running")
        remote(f'mkdir -p apps/{version} envs/{version} tmp && rm -rf tmp/* ')
        Transfer(c).put(f'release-{version}.tgz', f'apps/{app.name}')
        with c.cd(f'apps/{version}'):
            remote(f'tar xf ../../release-{version}.tgz')
            remote('mv kill start stop uwsgi.ini ../..')
        remote('pwd')
        remote('chmod +x kill start stop')
        remote(f'~/.local/bin/uv venv --clear envs/{version}')
        remote('rm -rf dist && ~/.local/bin/uv build')
        remote(f'rm -f myapp && ln -s apps/{version} myapp')
        remote(f'rm -f env && ln -s envs/{version} env')
        remote('ln -sf /home/sholden/bin/uwsgi env/bin/uwsgi')
        remote('rm -rf dist && ~/.local/bin/uv build')
        remote('source env/bin/activate && pip install dist/*.whl && ./start')
    c.close()


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
    version = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
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
