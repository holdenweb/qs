"""
newapp.py: Create a new app in your Opalstack account using its API.
"""
import opalstack as ops
import os
import sys

from mongoengine import connect
from .models import App
from hu import ObjectDict as OD

MANAGER_NAME = "sholden"
SERVER_NAME = "opal5.opalstack.com"

token = os.getenv('OPALSTACK_TOKEN')
api = ops.Api(token=token)

def create_app(a_mgr, name, manager_id):
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
    if len(sys.argv) == 1:
        names = [input("App name: ")]
    else:
        names = sys.argv[1:]
    if len(names) > 1:
        sys.exit("One at a time, please")
    s_mgr = ops.api.ServersManager(api)
    u_mgr = ops.api.OSUsersManager(api)
    servers = s_mgr.list_all()
    server = next(s for s in servers["web_servers"] if s['hostname']==SERVER_NAME)
    server_id = server['id']
    manager = OD(u_mgr.list_all({'name': MANAGER_NAME, 'server': server_id})[0])

    a_mgr = ops.api.AppsManager(api)

    conn = connect(db='opalstack')
    for name in names:
        app = create_app(a_mgr, name, manager.id)
        print("Created on port", app.port, file=sys.stderr)


if __name__ == '__main__':
    main()
