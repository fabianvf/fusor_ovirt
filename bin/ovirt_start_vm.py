#! /usr/bin/env python

import logging
import sys
import time
from optparse import OptionParser

try:
    from ovirtsdk3x4.api import API
    from ovirtsdk3x4.infrastructure.errors import RequestError
except:
    print "Please re-run after you have installed 'ovirt-engine-sdk-python'"
    print "Example: easy_install ovirt-engine-sdk-python"
    sys.exit()


DEFAULT_API_USER = "admin@internal"


def parse_args():
    parser = OptionParser(description='Get the IP of a running VM')

    parser.add_option('--debug', action='store_true', default=False,
                      help='debug mode')

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


def start_vm(api, vm_id):
    vm = api.vms.get(id=vm_id)
    if vm.status.state == "up":
        logging.info("VM id '%s' was already up" % (vm_id))
        return True

    vm_started = False
    max_count = 30
    for x in range(0, max_count):
        logging.debug("VM id '%s', state: '%s'" % (vm_id, vm.status.state))
        try:
            vm.start()
            vm_started = True
            logging.info("VM ID '%s' started" % (vm_id))
            break
        except RequestError, e:
            logging.info(e)
            logging.info("Will retry, %s/%s" % (x, max_count))
            time.sleep(10)
            continue
    return vm_started


def wait_for_vm_up(api, vm_id):
    vm_is_up = False
    max_tries = 120
    wait_secs = 10
    for count in range(0, max_tries):
        vm_state = api.vms.get(id=vm_id).status.state
        if vm_state == 'up':
            logging.info("VM ID '%s' is up" % (vm_id))
            vm_is_up = True
            break
        logging.info("Waiting %s seconds for VM '%s' to come up, current state '%s'  (%s/%s)" %
                     (wait_secs, vm_id, vm_state, count, max_tries))
        time.sleep(wait_secs)

    return vm_is_up

if __name__ == "__main__":

    opts = parse_args()
    debug = opts.debug
    setup_logging(debug)

    api_host = opts.api_host
    api_user = opts.api_user
    api_pass = opts.api_pass
    vm_id = opts.vm_id

    url = "https://%s" % (api_host)

    api = API(url=url, username=api_user, password=api_pass, insecure=True)
    if not api:
        print "Failed to connect to '%s'" % (url)
        sys.exit(1)

    if not start_vm(api, vm_id):
        logging.error("Failed to start VM '%s'" % (vm_id))
        sys.exit(1)
    if not wait_for_vm_up(api, vm_id):
        logging.error("Failed to see VM '%s' come up within timeout" % (vm_id))
        sys.exit()
    print "Success"
    sys.exit(0)
