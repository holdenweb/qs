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

DEBUG = False
HOSTS = ['opal5.opalstack.com']
conn = connect('opalstack')

from .version import __version__

VERSION_TEMPLATE = """\

__version__ = "{version}"

"""

def deliver(c, app, version):

    def crun(cmd):
        if DEBUG:
            print("+", cmd)
        return c.run(cmd)

    print(f"Deploying with qs {__version__}")
    try:
        app = App.objects.get(name=app)
    except App.DoesNotExist:
        sys.exit(f"Application {app!r} not known: do you need to run sync-apps?")
    loader = PackageLoader('qs', 'templates')
    jenv = Environment(
        loader=loader,
        autoescape=False
    )

    if not app.port:
        sys.exit("App has no port number: please re-sync by running sync-apps.")
    for filename in ('kill', 'start', 'stop', 'uwsgi.ini'):
        with open(filename, 'w') as f:
            tpl = jenv.get_template(filename)
            content = tpl.render(PROJECT=app.name, PORT_NO=app.port, VERSION=version)
            f.write(content)
    c.local(f'echo {version} > version.txt')
    c.local(fr'(tar cf release-{version}.tgz --no-xattrs --exclude __pycache__ --exclude \*.DS_Store --exclude \*.tgz --exclude .git\* .)')

    with c.cd(f"apps/{app.name}"):
        crun("./stop || echo Not running")
        crun(f'mkdir -p apps/{version} envs/{version} tmp && rm -rf tmp/* ')
        Transfer(c).put(f'release-{version}.tgz', f'apps/{app.name}')
        crun(f"cd apps/{version} && tar xf ../../release-{version}.tgz && cp kill start stop uwsgi.ini ../..")
        crun(f"rm -rf myapp env && ln -sF apps/{version} myapp && ln -sF envs/{version} env")
        crun(f"""\
chmod +x kill start stop &&
python3.10 -m venv envs/{version} &&
source envs/{version}/bin/activate &&
pip install -r apps/{version}/requirements.txt &&
rm -f myapp ; ln -s apps/{version} myapp &&
rm -f env ; ln -s envs/{version} env &&
ln -sf /home/sholden/bin/uwsgi env/bin
""")
        crun("pwd && ./start")

    c.close()


def deploy():
    args = sys.argv[1:]
    if len(args) != 1:
        sys.exit(f"""\
Usage: {os.path.basename(sys.argv[0])} appname

This delivers the currently checked-out version of this directory's
application to the named Opalstack app.""")
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

def release():

    def usage():
        return f"""\
Usage: {os.path.basename(sys.argv[0])} [release]

where "release" is an acceptable argument for "poetry version".
Without an argument, displays the current release.
"""

    cmd = ["poetry", "version"]
    if len(sys.argv) == 1:
        retcode = subprocess.call(cmd)
        print(usage())
        if os.system("git diff --quiet") != 0:
            sys.exit("Git branch is dirty: please commit changes before releasing")
        sys.exit(0)

    if len(sys.argv) != 2:
        sys.exit(usage())

    # Modify version according to argument
    cmd.append(sys.argv[1])
    retcode = subprocess.call(cmd)
    if retcode:
        sys.exit(f"""Command {" ".join(cmd)!r} failed with return code {retcode}""")

    # Check in an updated version.py
    cmd = ["poetry", "version", "--short"]
    version = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    pystring = VERSION_TEMPLATE.format(version=version)
    with open("version.py", "w") as pyfile:
        pyfile.write(pystring)
        print("Wrote", pyfile)
    cmd = ["git", "add", "version.py"]
    retcode = subprocess.call(cmd)
    cmd = ["git", "commit", "-m", f"Release r{version}"]
    retcode = subprocess.call(cmd)

    # Tag the new version
    cmd = ["git", "tag", f"r{version}"]
    retcode = subprocess.call(cmd)

if __name__ == '__main__':
    deploy()
