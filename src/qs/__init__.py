import sys

from fabric import task, Connection
from fabric.transfer import Transfer
from mongoengine import connect
from qs.models import App
from jinja2 import Environment, PackageLoader

import logging
logging.basicConfig(level=logging.INFO)

DEBUG = True
HOSTS = ['opal5.opalstack.com']
conn = connect('opalstack')

__version__ = "0.2.0"


@task(hosts=HOSTS)
def deploy(c, app, version):

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
    c.local(fr'(tar cf release-{version}.tgz --exclude __pycache__ --exclude \*.DS_Store --exclude \*.tgz --exclude .git\* .)')

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
pip install -qr apps/{version}/requirements.txt &&
rm -f myapp ; ln -s apps/{version} myapp &&
rm -f env ; ln -s envs/{version} env &&
ln -sf /home/sholden/bin/uwsgi env/bin
""")
        crun("pwd && ./start")

    c.close()


def main():
    args = sys.argv[1:]
    print("Args are", args)
    c = Connection(
        host=HOSTS[0],
        user="sholden",
        connect_kwargs={
            "key_filename": "/Users/sholden/.ssh/id_rsa",
        },
    )
    return deploy(c, *args)


if __name__ == '__main__':
    main()
