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
MB = 1024*1024
GB = 1024*MB


def parse_args():
    parser = OptionParser(description='Add a disk to an existing VM ID')

    parser.add_option(
        '--debug', action='store_true',
        default=False, help='debug mode')

    parser.add_option(
        '--api_host', default=None,
        help='oVirt API IP Address/Hostname')

    parser.add_option(
        '--api_user', default=DEFAULT_API_USER,
        help='oVirt API Username, defaults to "%s"' % (DEFAULT_API_USER))

    parser.add_option('--api_pass', default=None, help='oVirt API Password')

    parser.add_option('--vm_id', default=None,
                      help='ID of an existing VM to add a disk to')

    parser.add_option('--size_gb', default=None,
                      help='Size of disk to add in GB')

    parser.add_option('--storage_domain',
                      default=None, help='Name of storage domain')

    (opts, args) = parser.parse_args()

    for optname in ["api_host", "api_pass", "api_user", "vm_id", "size_gb", "storage_domain"]:
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


def add_disk_to_vm(api, vm_id, size_gb, storage_domain_name):
    def create_params():
        storage_domain = api.storagedomains.get(storage_domain_name)
        if not storage_domain:
            print "Unable to find storage domain '%s'" % (storage_domain_name)
            return None
        storage_domain_params = params.StorageDomains(storage_domain=[storage_domain])
        disk_params = params.Disk(
            storage_domains=storage_domain_params,
            size=size_gb*GB,
            status=None,
            interface='virtio',
            format='cow',
            sparse=True,
            bootable=False)
        return disk_params

    def issue_add_request(disk_params, attempts=10):
        try:
            vm = api.vms.get(id=vm_id)
            vm.disks.add(disk_params)
        except RequestError, e:
            if "Please try again in a few minutes" in e.detail and attempts > 0:
                print "Waiting to retry adding disk...sleeping 30 seconds"
                time.sleep(30)
                return issue_add_request(disk_params, attempts=attempts-1)
            print e
            return False
        except Exception, e:
            print e
            return False
        return True

    disk_params = create_params()
    return issue_add_request(disk_params)


if __name__ == "__main__":

    opts = parse_args()
    debug = opts.debug
    setup_logging(debug)

    api_host = opts.api_host
    api_user = opts.api_user
    api_pass = opts.api_pass

    vm_id = opts.vm_id
    size_gb = int(opts.size_gb)
    s_domain_name = opts.storage_domain

    url = "https://%s" % (api_host)
    logging.debug("Connecting to oVirt API at: '%s' with user '%s'" % (api_host, api_user))
    logging.debug("Will attempt to add a disk of size '%s' to VM ID '%s'" % (size_gb, vm_id))
    logging.debug("in storage domain '%s'" % (s_domain_name))

    api = API(url=url, username=api_user, password=api_pass, insecure=True)
    if not api:
        print "Failed to connect to '%s'" % (url)
        sys.exit(1)

    if not add_disk_to_vm(api, vm_id=vm_id, size_gb=size_gb, storage_domain_name=s_domain_name):
        print "Error adding disk of size '%s' to VM ID '%s'" % (size_gb, vm_id)
        sys.exit(1)
    print "A disk of '%s'GB has been added to VM ID '%s'" % (size_gb, vm_id)
    sys.exit(0)
