import os

from fabric import task, Connection
from fabric.transfer import Transfer
from mongoengine import connect
from models import Application
from jinja2 import Environment, FileSystemLoader

HOSTS = ['opal5.opalstack.com']
conn = connect('opalstack')

@task(hosts=HOSTS)
def deploy(c, app, version):
    app = Application.objects.get(name=app)
    jenv = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
        autoescape=False
    )
    for filename in ('kill', 'start', 'stop', 'uwsgi.ini'):
        with open(os.path.join("release", filename), 'w') as f:
            tpl = jenv.get_template(filename)
            content = tpl.render(PROJECT=app.name, PORT_NO=app.port, VERSION=version)
            f.write(content)
    c.local(f'echo {version} > release/version.txt')
    c.local(f'(cd release && tar cf ../release-{version}.tgz --exclude __pycache__ --exclude \*.DS_Store .)')
    with c.cd(f"apps/{app.name}"):
        c.run("./stop || echo Not running")
        c.run(f'mkdir -p apps/{version} envs/{version} tmp && rm -rf tmp/* ')
        Transfer(c).put(f'release-{version}.tgz', f'apps/{app.name}')
        c.run(f"cd apps/{version} && tar xf ../../release-{version}.tgz")
        print("About to run", f"ln -sF apps/{version} myapp && ln -sF envs/{version} env")
        c.run(f"rm -f myapp env && ln -sF apps/{version} myapp && ln -sF envs/{version} env")
        c.run(f"""\
chmod +x kill start stop &&
python3.10 -m venv envs/{version} &&
source envs/{version}/bin/activate &&
pip install -qr apps/{version}/requirements.txt &&
rm -f myapp ; ln -s apps/{version} myapp &&
rm -f env ; ln -s envs/{version} env &&
ln -sf /home/sholden/bin/uwsgi env/bin &&
./start
""")

@task(hosts=HOSTS)
def list_app(c, directory=""):
    with c.cd(f"apps/{directory}"):
        c.run(f"ls -al")


if __name__ == '__main__':
    c = Connection(
        host=HOSTS[0],
        user="sholden",
        connect_kwargs={
            "key_filename": "/Users/sholden/.ssh/id_rsa",
        },
    )
    ensure_env(c, 'testing', '2.4.0')