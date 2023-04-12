"""
sync.py: Download the Opalstack state.
"""
import os
import sys

from mongoengine import connect
from qs.models import Application, Domain, Site
from hu import ObjectDict as OD
import opalstack as ostack


MANAGER_NAME = "sholden"
SERVER_NAME = "opal5.opalstack.com"

token = os.getenv('OPALSTACK_TOKEN', None)
if not token:
    sys.exit("OPALSTACK_TOKEN not found in environment")
api = ostack.Api(token=token)
a_mgr = ostack.api.AppsManager(api)
d_mgr = ostack.api.DomainsManager(api)
s_mgr = ostack.api.SitesManager(api)

def main():
    connect("opalstack")
    app_list = a_mgr.list_all()
    for app in app_list:
        Application(**app).save()
    domain_list = d_mgr.list_all()
    for domain in domain_list:
        Domain(**domain).save()
    site_list = s_mgr.list_all()
    for site in site_list:
        Site(**site).save()
if __name__ == '__main__':
    main()
