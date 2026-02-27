"""
sync.py: Download the Opalstack state.
"""
import os
import sys

from mongoengine import connect
from qs.models import class_for
import opalstack as ostack

object_type_names = ['Accounts', 'Addresses', 'Apps', 'Certs', 'Dnsrecords', 'Domains', 'Ips', 'Mailusers',
                'Mariadbs', 'Mariausers', 'Notices', 'OSUsers', 'OSVars', 'Psqldbs', 'Psqlusers',
                'Quarantinedmails', 'Servers', 'Sites', 'Tokens']

def server_transfer(mgr, type_name):
    class_for(type_name).drop_collection()
    s_dict = mgr.list_all()
    for key in s_dict:
        for d in s_dict[key]:
            class_for(type_name)(**d).save()

def generic_transfer(mgr, type_name):
    """
    Standard routine to transfer _almost_ any Opalstack resource
    to a local MongoDB database.
    """
    class_for(type_name).drop_collection()
    item_list = mgr.list_all()
    for item in item_list:
        class_for(type_name)(**item).save()

specials = {'Servers': server_transfer}


def main():
    token = os.getenv('OPALSTACK_TOKEN', None)
    if not token:
        sys.exit("OPALSTACK_TOKEN not found in environment")
    api = ostack.Api(token=token)
    connect("opalstack")
    for type_name in object_type_names:
        print("Grabbing", type_name)
        mgr = getattr(ostack.api, f"{type_name}Manager")(api)
        specials.get(type_name, generic_transfer)(mgr, type_name)

if __name__ == '__main__':
    main()
