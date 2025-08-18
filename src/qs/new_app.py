"""
newapp.py: Create a new app in your Opalstack account using its API.
"""
import opalstack as ops
import os
import sys

from mongoengine import connect
from qs.models import App
from hu import ObjectDict as OD

MANAGER_NAME = "sholden"
SERVER_NAME = "opal5.opalstack.com"

token = os.getenv('OPALSTACK_TOKEN')
api = ops.Api(token=token)

def create_app(a_mgr, name, manager_id):
    """
    Create a new Opalstack application

    A custom application has a directory and a port number.
    Everything else is provided by Opalstack's install script,
    so ignoring that means you can set up the environment to
    suit your application.

    Oplstack apps also install a crontab line, which never
    seems to get deleted, to restart the app periodically
    if it's crashed - which would seem a bit arbitrary to a
    customer in th middle of a transaction.
    """
    app = a_mgr.create_one(
        dict(
            name=name,
            osuser=manager_id,
            type='CUS'
        )
    )
    db_app = App(**app)
    db_app.save()
    return OD(app)

def main(*argv):
    if len(argv) == 1:
        names = [input("Pam name: ")]
    elif len(argv == 2):
        names = [argv[1]]
    elif len(argv) > 2:
        sys.exit("Only one, please")
    else:
        sys.exit("Usage: new_app.py pam-name")
    s_mgr = ops.api.ServersManager(api)
    u_mgr = ops.api.OSUsersManager(api)
    servers = s_mgr.list_all()
    server = next(s for s in servers["web_servers"] if s['hostname']==SERVER_NAME)
    server_id = server['id']
    manager = OD(u_mgr.list_all({'name': MANAGER_NAME, 'server': server_id})[0])

    app_mgr = ops.api.AppsManager(api)

    conn = connect(db='opalstack')
    for name in names:
        app = create_app(app_mgr, name, manager.id)
        print("Created on port", app.port, file=sys.stderr)


if __name__ == '__main__':
    main(*sys.argv)
