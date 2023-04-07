"""
sync.py: Download the Opalstack state.
"""
import os
import sys

from mongoengine import connect
from qs.models import Application
from hu import ObjectDict as OD
import opalstack as ops

MANAGER_NAME = "sholden"
SERVER_NAME = "opal5.opalstack.com"

token = os.getenv('OPALSTACK_TOKEN')
api = ops.Api(token=token)
a_mgr = ops.api.AppsManager(api)

def main():
    print("Yeah!")
    connect("opalstack")
    app_list = a_mgr.list_all()
    for app in app_list:
        Application(**app).save()


if __name__ == '__main__':
    main()