import os
import subprocess
import sys

from mongoengine import connect
from models import Application
from hu import ObjectDict as OD
import opalstack as ops
import fabric

MANAGER_NAME = "sholden"
SERVER_NAME = "opal5.opalstack.com"


def remote_run(cmd):
    connection = fabric.Connection(SERVER_NAME,
                                   connect_kwargs=dict(key_filename='/Users/sholden/.ssh/id_rsa')
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
    server = next(s for s in servers["web_servers"] if s['hostname']==SERVER_NAME)
    server_id = server['id']
    manager = OD(u_mgr.list_all({'name': MANAGER_NAME, 'server': server_id})[0])

    a_mgr = ops.api.AppsManager(api)

    conn = connect(db='opalstack')
    for name in names:
        try:
            app = Application.objects().get(name=name)
        except Application.DoesNotExist as e:
            sys.exit(f"{name!r}: no such app on server {SERVER_NAME!r}({server['hostname']},{server['id']})")
        remote_run(f"apps/{name}/stop")
        cmd = f"make deploy PROJECT={name} PORT_NO={app.port} VERSION=2.1.0"
        subprocess.run(cmd.split(), text="Alleged to be required")
        remote_run(f"apps/{name}/start")
