"""
apiclient.py: Accesses the OpalStack system using its API.
"""
import os
import sys

from mongoengine import connect
from models import Application
from hu import ObjectDict as OD
import opalstack as ops

MANAGER_NAME = "sholden"
SERVER_NAME = "opal5.opalstack.com"

token = os.getenv('OPALSTACK_TOKEN')
api = ops.Api(token=token)
a_mgr = ops.api.AppsManager(api)

if __name__ == '__main__':
    connect("opalstack")

    app_list = a_mgr.list_all()
    for app in app_list:
        Application(**app).save()
