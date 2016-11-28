#! /usr/bin/env python

import logging
import sys
from optparse import OptionParser

from ovirtsdk3x4.api import API


def debug(f):
    import ipdb

    def inner(*args, **kwargs):
        with ipdb.launch_ipdb_on_exception():
            return f(*args, **kwargs)
    return inner


DEFAULT_API_USER = "admin@internal"


@debug
def main():
    opts = parse_args()
    debug = opts.debug
    setup_logging(debug)

    api_host = opts.api_host
    api_user = opts.api_user
    api_pass = opts.api_pass
    data_center_name = opts.data_center

    url = "https://%s/ovirt-engine/api" % (api_host)
    logging.debug("Connecting to oVirt API at: '%s' with user '%s'" % (api_host, api_user))
    logging.debug("Will check status of data center named '%s'" % (data_center_name))

    api = API(url=url, username=api_user, password=api_pass, insecure=True)
    if not api:
        print "Failed to connect to '%s'" % (url)
        sys.exit(1)

    data_center = api.datacenters.get(data_center_name)
    if not data_center:
        print "Couldn't find datacenter with name '%s'" % (data_center_name)
        sys.exit(1)

    storage_domains = data_center.storagedomains.list()
    if not any([sd.get_status().state == 'active' for sd in storage_domains]):
        print "Couldn't find an active storage domain " \
                "for datacenter with name '%s'" % (data_center_name)
        sys.exit(1)

    clusters = data_center.clusters.list()
    cluster_ids = [cluster.id for cluster in clusters]

    # Host must be up, and must be SPM
    hosts = filter(lambda host: host.cluster.id in cluster_ids, api.hosts.list())
    if not any([host.get_status().state == 'up' and
                host.spm.status.state == 'spm' for host in hosts]):
        print "Couldn't find an active SPM host for datacenter with name '%s'" % (data_center_name)
        sys.exit(1)

    print data_center.status.state
    sys.exit(0)


def parse_args():
    parser = OptionParser(description='Create a VM in oVirt from an existing VM Template')

    parser.add_option('--debug', action='store_true',
                      default=False, help='debug mode')

    parser.add_option('--api_host', default=None,
                      help='oVirt API IP Address/Hostname')

    parser.add_option(
        '--api_user', default=DEFAULT_API_USER,
        help='oVirt API Username, defaults to "%s"' % (DEFAULT_API_USER))

    parser.add_option('--api_pass', default=None, help='oVirt API Password')

    parser.add_option('--data_center', default=None, help='Datacenter name')

    (opts, args) = parser.parse_args()

    for optname in ["api_host", "api_pass", "api_user", "data_center"]:
        optvalue = getattr(opts, optname)
        if not optvalue:
            parser.print_help()
            parser.print_usage()
            print "Please re-run with an option specified for: '%s'" % (optname)
            sys.exit(1)

    return opts


def setup_logging(debug=False):
    if debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

if __name__ == "__main__":
    main()
