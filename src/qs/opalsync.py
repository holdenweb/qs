"""
sync.py: Download the Opalstack state.
"""
import os
import sys

from mongoengine import connect
from qs.models import App, Domain, Site
from hu import ObjectDict as OD
import opalstack as ostack


MANAGER_NAME = "sholden"
SERVER_NAME = "opal5.opalstack.com"

token = os.getenv('OPALSTACK_TOKEN', None)
if not token:
    sys.exit("OPALSTACK_TOKEN not found in environment")

object_types = ['Accounts', 'Addresses', 'Apps', 'Certs', 'Dnsrecords', 'Domains', 'Ips', 'Mailusers',
                'Mariadbs', 'Mariausers', 'Notices', 'OSUsers', 'OSVars', 'Psqldbs', 'Psqlusers',
                'Quarantinedmails', 'Servers', 'Sites', 'Tokens']


def main():
    api = ostack.Api(token=token)
    a_mgr = ostack.api.AppsManager(api)
    d_mgr = ostack.api.DomainsManager(api)
    s_mgr = ostack.api.SitesManager(api)
    connect("opalstack")
    app_list = a_mgr.list_all()
    for app in app_list:
        App(**app).save()
    domain_list = d_mgr.list_all()
    for domain in domain_list:
        Domain(**domain).save()
    site_list = s_mgr.list_all()
    for site in site_list:
        Site(**site).save()

if __name__ == '__main__':
    main()
