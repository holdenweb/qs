"""
sync.py: Download the Opalstack state.
"""
import os
import sys

import opalstack as ostack

from qs.models import TYPE_NAMES, class_for, connect_db

# Derived from qs.models.CLASS_MAP so the sync list can never drift from
# the set of known document types.
object_type_names = TYPE_NAMES

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
    connect_db()
    for type_name in object_type_names:
        print("Grabbing", type_name)
        mgr = getattr(ostack.api, f"{type_name}Manager")(api)
        specials.get(type_name, generic_transfer)(mgr, type_name)

if __name__ == '__main__':
    main()
