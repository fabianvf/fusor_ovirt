#! /usr/bin/env python

import logging
import sys
from optparse import OptionParser

try:
    from ovirtsdk3x4.api import API
    from ovirtsdk3x4.xml import params
except:
    print "Please re-run after you have installed 'ovirt-engine-sdk-python'"
    print "Example: easy_install ovirt-engine-sdk-python"
    sys.exit()


DEFAULT_API_USER = "admin@internal"


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

    parser.add_option('--vm_template_name', default=None,
                      help='VM template name to create VM from')

    parser.add_option('--cluster_name', default=None,
                      help='Cluster name to create VM in')

    parser.add_option('--vm_name', default=None, help='VM name to be created')

    (opts, args) = parser.parse_args()

    for optname in ["api_host", "api_pass", "api_user",
                    "vm_template_name", "cluster_name", "vm_name"]:
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


def create_vm_from_template(api, vm_name, cluster, template):
    vm_params = params.VM(name=vm_name, cluster=cluster, template=template)
    return api.vms.add(vm_params)

if __name__ == "__main__":

    opts = parse_args()
    debug = opts.debug
    setup_logging(debug)

    api_host = opts.api_host
    api_user = opts.api_user
    api_pass = opts.api_pass
    vm_template_name = opts.vm_template_name
    cluster_name = opts.cluster_name
    vm_name = opts.vm_name

    url = "https://%s" % (api_host)
    logging.debug("Connecting to oVirt API at: '%s' with user '%s'" % (api_host, api_user))
    logging.debug("Will attempt to create a VM named '%s'" % (vm_name))
    logging.debug("in cluster '%s'" % (cluster_name))
    logging.debug("from template '%s'" % (vm_template_name))

    api = API(url=url, username=api_user, password=api_pass, insecure=True)
    if not api:
        print "Failed to connect to '%s'" % (url)
        sys.exit(1)

    template = api.templates.get(vm_template_name)
    if not template:
        print "Couldn't find template with name '%s'" % (vm_template_name)
        sys.exit(1)

    cluster = api.clusters.get(cluster_name)
    if not cluster:
        print "Couldn't find cluster with name '%s'" % (cluster_name)
        sys.exit(1)

    vm = create_vm_from_template(api, vm_name=vm_name, cluster=cluster, template=template)
    if not vm:
        print "Unable to create VM from template '%s'" % (vm_template_name)
        sys.exit(1)

    vm_id = vm.id
    logging.debug("VM '%s' with ID: '%s' has been created." % (vm.name, vm.id))

    print vm_id
    sys.exit(0)
