"""
newapp.py: Create a new app in your Opalstack account using its API.
"""
import getpass
import os
import sys

import opalstack as ops
from hu import ObjectDict as OD

from qs.models import App, connect_db

# Configuration via environment variables with sensible defaults.
MANAGER_NAME = os.environ.get("QS_MANAGER_NAME", getpass.getuser())
SERVER_NAME = os.environ.get("QS_SERVER_NAME", "opal5.opalstack.com")


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

def main():
    return build(sys.argv)

def build(argv):
    if len(argv) == 2:
        names = [argv[1]]
    else:
        sys.exit("Usage: new_app.py pam-name")
    token = os.getenv('OPALSTACK_TOKEN')
    if not token:
        sys.exit("OPALSTACK_TOKEN not found in environment")
    api = ops.Api(token=token)
    s_mgr = ops.api.ServersManager(api)
    u_mgr = ops.api.OSUsersManager(api)
    servers = s_mgr.list_all()
    server = next(s for s in servers["web_servers"] if s['hostname']==SERVER_NAME)
    manager = [u for u in u_mgr.list_all()
                      if u['name']==MANAGER_NAME and u['server']==server['id']][0]
    manager = OD(manager)
    app_mgr = ops.api.AppsManager(api)

    connect_db()
    for name in names:
        app = create_app(app_mgr, name, manager.id)
        print("Created on port", app.port, file=sys.stderr)

if __name__ == '__main__':
    main()
