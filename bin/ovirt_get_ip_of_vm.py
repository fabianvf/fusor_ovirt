#! /usr/bin/env python

import logging
import sys
import time
from optparse import OptionParser

try:
    from ovirtsdk3x4.api import API
except:
    print "Please re-run after you have installed 'ovirt-engine-sdk-python'"
    print "Example: easy_install ovirt-engine-sdk-python"
    sys.exit()


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
    vm_id = opts.vm_id

    url = "https://%s/ovirt-engine/api" % (api_host)

    api = API(url=url, username=api_user, password=api_pass, insecure=True)
    if not api:
        print "Failed to connect to '%s'" % (url)
        sys.exit(1)

    ip = get_ip(api, vm_id)
    if not ip:
        sys.exit(1)
    print ip
    sys.exit(0)


def parse_args():
    parser = OptionParser(description='Get the IP of a running VM')

    parser.add_option('--debug', action='store_true',
                      default=False, help='debug mode')

    parser.add_option('--api_host', default=None,
                      help='oVirt API IP Address/Hostname')

    parser.add_option(
        '--api_user', default=DEFAULT_API_USER,
        help='oVirt API Username, defaults to "%s"' % (DEFAULT_API_USER))

    parser.add_option('--api_pass', default=None, help='oVirt API Password')

    parser.add_option('--vm_id', default=None,
                      help='ID of an existing VM to add a disk to')

    (opts, args) = parser.parse_args()

    for optname in ["api_host", "api_pass", "api_user", "vm_id"]:
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


def get_ip(api, vm_id):
    def __get_ip():
        vm = api.vms.get(id=vm_id)
        info = vm.get_guest_info()
        try:
            return info.get_ips().get_ip()[0].get_address()
        except:
            return None

    # Wait till IP is available
    max_tries = 60
    wait_secs = 5
    for count in range(0, max_tries):
        ip = __get_ip()
        if not ip:
            logging.debug("Waiting %s seconds for IP to become available of VM ID '%s' (%s/%s)" %
                          (wait_secs, vm_id, count, max_tries))
            time.sleep(wait_secs)
        else:
            return ip
    return None

if __name__ == "__main__":
    main()
