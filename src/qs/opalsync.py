"""
sync.py: Download the Opalstack state.
"""
import os
import sys

from mongoengine import connect
from qs.models import App, Domain, Site, class_for
from hu import ObjectDict as OD
import opalstack as ostack

ostack.apps


MANAGER_NAME = "sholden"
SERVER_NAME = "opal5.opalstack.com"

token = os.getenv('OPALSTACK_TOKEN', None)
if not token:
    sys.exit("OPALSTACK_TOKEN not found in environment")

object_types = ['Accounts', 'Addresses', 'Apps', 'Certs', 'Dnsrecords', 'Domains', 'Ips', 'Mailusers',
                'Mariadbs', 'Mariausers', 'Notices', 'OSUsers', 'OSVars', 'Psqldbs', 'Psqlusers',
                'Quarantinedmails', 'Servers', 'Sites', 'Tokens']

def server_transfer(mgr, name):
    s_dict = mgr.list_all()
    for key in s_dict:
        for d in s_dict[key]:
            class_for(name)(**d).save()

def generic_transfer(mgr, name):
    """
    Standard routine to transfer _almost_ any Opalstack resource
    to a local MongoDB database.
    """
    item_list = mgr.list_all()
    for item in item_list:
        class_for(name)(**item).save()

specials = {'Servers': server_transfer}


def main():
    api = ostack.Api(token=token)
    connect("opalstack")
    for name in object_types:
        print("Grabbing", name)
        mgr = getattr(ostack.api, f"{name}Manager")(api)
        specials.get(name, generic_transfer)(mgr, name)

if __name__ == '__main__':
    main()
