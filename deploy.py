import os
import subprocess
import sys

from jinja2 import Environment, FileSystemLoader
from mongoengine import connect
from models import Application
from hu import ObjectDict as OD
import opalstack as ops
import fabric

MANAGER_NAME = "sholden"
SERVER_NAME = "opal5.opalstack.com"
VERSION = "2.2.5"

def remote_run(cmd):
    connection = fabric.Connection(
        SERVER_NAME, connect_kwargs=dict(key_filename='/Users/sholden/.ssh/id_rsa')
    )
    result = connection.run(cmd)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        names = [input("App name: ")]
    else:
        names = sys.argv[1:]
    if len(names) > 1:
        sys.exit("One at a time, please")
    token = os.getenv('OPALSTACK_TOKEN')
    api = ops.Api(token=token)
    a_mgr = ops.api.AppsManager(api)
    u_mgr = ops.api.OSUsersManager(api)
    s_mgr = ops.api.ServersManager(api)
    servers = s_mgr.list_all()
    server = next(s for s in servers["web_servers"] if s['hostname'] == SERVER_NAME)
    server_id = server['id']
    manager = OD(u_mgr.list_all({'name': MANAGER_NAME, 'server': server_id})[0])

    a_mgr = ops.api.AppsManager(api)

    conn = connect(db='opalstack')

    jenv = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
        autoescape=False
    )
    for app_name in names:
        try:
            app = Application.objects().get(name=app_name)
        except Application.DoesNotExist as e:
            sys.exit(
                f"{app_name!r}: no such app on server {SERVER_NAME!r}({server['hostname']},{server['id']})"
            )
        for filename in ('kill', 'start', 'stop', 'uwsgi.ini'):
            with open(os.path.join("release", filename), 'w') as f:
                tpl = jenv.get_template(filename)
                content = tpl.render(PROJECT=app_name, PORT_NO=app.port, VERSION=VERSION)
                f.write(content)
        cmd = f"make deploy PROJECT={app_name} PORT_NO={app.port} VERSION={VERSION}"
        subprocess.run(cmd.split(), text="Alleged to be required")
        remote_run(f"apps/{app_name}/start")
