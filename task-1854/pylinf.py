"""
Usage - python pylinf.py -h
Output - A CSV file of the format (without newlines):
         <valid-after>,
         <min adv_bw>,
         <number of relays>,
         <linf>
rsync -arz --delete metrics.torproject.org::metrics-recent/relay-descriptors/consensuses in
"""

import sys
import math
import os
import pygeoip
import StringIO
import stem.descriptor

from optparse import OptionParser
from binascii import b2a_hex, a2b_base64, a2b_hex
from stem.descriptor.server_descriptor import RelayDescriptor, BridgeDescriptor

class Router:
    def __init__(self):
        self.prob = None
        self.bandwidth = None
        self.advertised_bw = None
        self.country = None
        self.as_no = None
        self.is_exit = None
        self.is_guard = None

    def add_router_info(self, values):
           hex_digest = b2a_hex(a2b_base64(values[2]+"="))
           self.advertised_bw = self.get_advertised_bw(hex_digest)
           ip = values[5]
           self.country = gi_db.country_code_by_addr(ip)
           self.as_no = self.get_as_details(ip)

    def add_weights(self, values):
           self.bandwidth = int(values[0].split('=')[1])

    def add_flags(self, values):
           if "Exit" in values and not "BadExit" in values:
               self.is_exit = True
           if "Guard" in values:
               self.is_guard = True

    def get_as_details(self, ip):
        try:
            value = as_db.org_by_addr(str(ip)).split()
            return value[0]
        except:
            return ""

    def get_advertised_bw(self, hex_digest):
        try:
            with open(options.server_desc+'/'+hex_digest) as f:
                data = f.read()

            desc_iter = stem.descriptor.server_descriptor.parse_file(StringIO.StringIO(data))
            desc_entries = list(desc_iter)
            desc = desc_entries[0]
            return min(desc.average_bandwidth, desc.burst_bandwidth, desc.observed_bandwidth)
        except:
            return 0

def parse_bw_weights(values):
    data = {}
    try:
        for value in values:
            key, value = value.split("=")
            data[key] = float(value) / 10000
        return data
    except:
        return None

def run(file_name):
    routers = []
    router = None
    result_string = []
    Wed, Wee, Wgd, Wgg = 1, 1, 1, 1
    # parse consensus
    with open(file_name, 'r') as f:
        for line in f.readlines():
            key = line.split()[0]
            values = line.split()[1:]
            if key =='r':
                router = Router()
                routers.append(router)
                router.add_router_info(values)
            elif key == 's':
                router.add_flags(values)
            elif key == 'w':
                router.add_weights(values)
            elif key == 'valid-after':
                valid_after = ' '.join(values)
            elif key == 'bandwidth-weights':
                data = parse_bw_weights(values)
                try:
                    Wed = data['Wed']
                    Wee = data['Wee']
                    Wgd = data['Wgd']
                    Wgg = data['Wgg']
                except:
                    pass

    if len(routers) <= 0:
        return

    # Find probability of each relay in pristine consensus
    total_bw = 0
    for router in routers:
        total_bw += router.bandwidth

    for router in routers:
        router.prob = float(router.bandwidth)/float(total_bw)

    # sort list of routers based on adv_bw
    routers.sort(key=lambda router: router.advertised_bw)

    omitted_routers = 0
    min_adv_bw = routers[0].advertised_bw

    while(omitted_routers<=len(routers)):
        total_bw = 0

        # this is the difference btw probability of choosing a relay in pristine
        # consensus and probability of choosing the same relay in the modified
        # consensus; prob_diff is the list of such differences for all relays
        prob_diff = []

        for router in routers:
            total_bw += router.bandwidth

        for router in routers:
            if router.bandwidth > 0:
                new_prob = float(router.bandwidth)/float(total_bw)
            else:
                new_prob = 0
            diff = abs(new_prob - router.prob)
            prob_diff.append(diff)

        result_string.append(','.join([valid_after,
                                      str(min_adv_bw),
                                      str(len(routers)-omitted_routers),
                                      str(max(prob_diff))]))

        # remove routers with min adv_bw
        for router in routers:
            if router.advertised_bw == min_adv_bw:
                omitted_routers += 1
                router.bandwidth = 0
            elif router.advertised_bw > min_adv_bw:
                min_adv_bw = router.advertised_bw
                break

    return '\n'.join(result_string)

def parse_args():
    usage = "Usage - python pyentropy.py [options]"
    parser = OptionParser(usage)

    parser.add_option("-g", "--geoip", dest="gi_db", default="GeoIP.dat",
                      help="Input GeoIP database")
    parser.add_option("-a", "--as", dest="as_db", default="GeoIPASNum.dat",
                      help="Input AS GeoIP database")
    parser.add_option("-s", "--server_desc", dest="server_desc",
                      default="data/relay-descriptors/server-descriptors/", help="Server descriptors directory")
    parser.add_option("-o", "--output", dest="output", default="entropy.csv",
                      help="Output filename")
    parser.add_option("-c", "--consensus", dest="consensus", default="in/consensus",
                      help="Input consensus dir")

    (options, args) = parser.parse_args()

    return options

if __name__ == "__main__":
    options = parse_args()
    gi_db = pygeoip.GeoIP(options.gi_db)
    as_db = pygeoip.GeoIP(options.as_db)

    with open(options.output, 'w') as f:
        for file_name in os.listdir(options.consensus):
            string = run(os.path.join(options.consensus, file_name))
            if string:
                f.write("%s\n" % (string))