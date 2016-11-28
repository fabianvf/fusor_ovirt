#! /usr/bin/env python

import logging
import sys
import time
from optparse import OptionParser

try:
    from ovirtsdk3x4.api import API
    from ovirtsdk3x4.xml import params
    from ovirtsdk3x4.infrastructure.errors import RequestError
except:
    print "Please re-run after you have installed 'ovirt-engine-sdk-python'"
    print "Example: easy_install ovirt-engine-sdk-python"
    sys.exit()


DEFAULT_API_USER = "admin@internal"


def parse_args():
    parser = OptionParser(description="Import CFME Template")

    parser.add_option("--debug", action="store_true",
                      default=False, help="debug mode")

    parser.add_option(
        '--api_user', default=DEFAULT_API_USER,
        help='oVirt API Username. Default: [%s]' % (DEFAULT_API_USER))

    parser.add_option("--api_host", default=None,
                      help="oVirt API IP Address/Hostname")

    parser.add_option('--api_pass', default=None, help='oVirt API Password')

    parser.add_option('--vm_template_name', default=None,
                      help='VM template name to import')

    parser.add_option('--export_domain_name', default="export",
                      help='export domain. Default: [export]')

    parser.add_option('--data_center_name', default="Default",
                      help='data_center name. Default: [Default]')

    parser.add_option('--cluster_name', default="Default",
                      help='cluster name. Default: [Default]')

    parser.add_option('--storage_domain_name', default="VMs",
                      help='storage domain. Default: [VMs]')

    (opts, args) = parser.parse_args()

    for optname in ["api_host", "api_pass", "vm_template_name"]:
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


def import_template(export_domain, vm_template_name, import_template_params, attempts=20):
    try:
        vm_templ = export_domain.templates.get(vm_template_name)
        vm_templ.import_template(import_template_params)
    except RequestError, e:
        if "Missing OVF file from VM" in e.detail and attempts > 0:
            print "Waiting to retry importing template...sleeping 30 seconds"
            time.sleep(30)
            return import_template(export_domain, vm_template_name,
                                   import_template_params, attempts=attempts-1)
        print e
        return False
    except Exception, e:
        print e
        return False
    return True

if __name__ == "__main__":
    opts = parse_args()
    debug = opts.debug
    setup_logging(debug)

    api_host = opts.api_host
    api_user = opts.api_user
    api_pass = opts.api_pass
    vm_template_name = opts.vm_template_name
    export_domain_name = opts.export_domain_name
    storage_domain_name = opts.storage_domain_name
    cluster_name = opts.cluster_name
    data_center_name = opts.data_center_name

    url = "https://%s/ovirt-engine/api" % (api_host)
    logging.debug("Connecting to oVirt API at: '%s' with user '%s'" % (api_host, api_user))

    api = API(url=url, username=api_user, password=api_pass, insecure=True)
    if not api:
        print "Failed to connect to '%s'" % (url)
        sys.exit(1)

    # imported_template_name = "zeus2_cfme-rhevm-5.3-47_%s" % (time.time())

    data_center = api.datacenters.get(data_center_name)
    export_domain = data_center.storagedomains.get(export_domain_name)
    if not export_domain:
        print "Unable to find export domain '%s'" % (export_domain_name)
        sys.exit(1)

    if export_domain.get_status().state != "active":
        print "Export domain '%s' is in unexpected state '%s'" % \
              (export_domain_name, export_domain.state)

        sys.exit(1)

    # Import appliance as a VM template
    export_domain = api.storagedomains.get(export_domain_name)

    if not export_domain:
        print "Unable to find export domain '%s'" % (export_domain_name)
        sys.exit(1)

    storage_domain = api.storagedomains.get(storage_domain_name)
    cluster = api.clusters.get(name=cluster_name)

    import_template_params = params.Action(storage_domain=storage_domain, cluster=cluster)
    if not import_template(export_domain, vm_template_name, import_template_params):
        print "Error importing template '%s' to export domain '%s'" % \
              (vm_template_name, export_domain_name)

        sys.exit(1)

    print 'Template was imported successfully'
    print 'Waiting for Template to reach "ok" status'
    while api.templates.get(vm_template_name).status.state != 'ok':
        time.sleep(1)
    sys.exit(0)
