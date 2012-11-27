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
import tarfile
import pickle
import StringIO
import stem.descriptor.server_descriptor as server_descriptor

from optparse import OptionParser
from binascii import b2a_hex, a2b_base64, a2b_hex

descriptors = {}

class Router:
    def __init__(self):
        self.prob = None
        self.bandwidth = None
        self.advertised_bw = None
        self.hex_digest = None
        self.is_exit = None
        self.is_guard = None

    def add_router_info(self, values):
           self.hex_digest = b2a_hex(a2b_base64(values[2]+"="))
           self.advertised_bw = self.get_advertised_bw(self.hex_digest)
           ip = values[5]

    def add_weights(self, values):
           self.bandwidth = int(values[0].split('=')[1])

    def add_flags(self, values):
           if "Exit" in values and not "BadExit" in values:
               self.is_exit = True
           if "Guard" in values:
               self.is_guard = True

    def get_advertised_bw(self, hex_digest):
        try:
            return descriptors[self.hex_digest.upper()]
        except: return 0

def parse_bw_weights(values):
    data = {}
    try:
        for value in values:
            key, value = value.split("=")
            data[key] = float(value) / 10000
        return data
    except:
        return None

def load_server_desc(tar_file_path):
    """
    tar_file_path -> 'string' or 'list'
    represents path{s} to tar file{s}
    """
    global descriptors

    if type(tar_file_path) == str: tar_file_path = [tar_file_path]

    for file_path in tar_file_path:
        tar_fh = tarfile.open(file_path)
        for member in tar_fh:
            if not member.isfile():
                continue

            tar_file_data=tar_fh.extractfile(member)
            data=tar_file_data.read()


            desc_iter = server_descriptor.parse_file(StringIO.StringIO(data), validate=False)
            desc_entries = list(desc_iter)
            desc = desc_entries[0]

            # currently we require only advertised_bw
            descriptors[desc.digest()] = min(desc.average_bandwidth,
                                             desc.burst_bandwidth,
                                             desc.observed_bandwidth)

        tar_fh.close()

def run(data):
    """ Return tuple of two strings, one string containing linf values for
        all possible advertised bandwidth cutoffs, and one containing
        probability distributions for predefined cutoffs. """
    routers = []
    router = None
    linf_string, prob_string = [], []
    Wed, Wee, Wgd, Wgg = 1, 1, 1, 1

    # parse consensus
    for line in data.split("\n"):
        try:
            key = line.split()[0]
            values = line.split()[1:]
        except:
            continue
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

    cutoffs = [10240, 20480, 51200, 102400, 204800, 512000, 1048576]

    while(omitted_routers<len(routers)):
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

        linf_string.append(','.join([valid_after,
                                      str(min_adv_bw),
                                      str(len(routers)-omitted_routers),
                                      str(max(prob_diff))]))

        while len(cutoffs) > 0 and min_adv_bw >= cutoffs[0]:
            prev_prob, cumulated_prob = 0.0, 0.0
            prev_advertised_bw = 0
            for router in routers:
                if router.advertised_bw > cutoffs[0] and \
                        prev_advertised_bw != router.advertised_bw:
                    prob_string.append(','.join([valid_after,
                                                 str(cutoffs[0]),
                                                 str(prev_advertised_bw),
                                                 str(cumulated_prob),
                                                 str(prev_prob)]))
                prev_advertised_bw = router.advertised_bw
                prev_prob = float(router.bandwidth)/float(total_bw)
                cumulated_prob += prev_prob
            prob_string.append(','.join([valid_after,
                                         str(cutoffs[0]),
                                         str(prev_advertised_bw),
                                         str(cumulated_prob),
                                         str(prev_prob)]))
            cutoffs.pop(0)

        # remove routers with min adv_bw
        for router in routers:
            if router.advertised_bw == min_adv_bw:
                omitted_routers += 1
                router.bandwidth = 0
            elif router.advertised_bw > min_adv_bw:
                min_adv_bw = router.advertised_bw
                break

    return ('\n'.join(linf_string), '\n'.join(prob_string))

def parse_args():
    usage = "Usage - python pyentropy.py [options]"
    parser = OptionParser(usage)

    parser.add_option("-s", "--server_desc", dest="server_desc",
                      default=False, help="Server descriptors directory")
    parser.add_option("-l", "--linf-output", dest="linf", default="linf.csv",
                      help="linf output filename")
    parser.add_option("-r", "--prob-output", dest="prob", default="prob.csv",
                      help="Probabilities output filename")
    parser.add_option("-c", "--consensus", dest="consensus", default="in/consensus",
                      help="Input consensus dir")
    parser.add_option("-p", "--pickled_data", dest="pickled_data", default=False,
                      help="Input pickled file")

    (options, args) = parser.parse_args()

    return options

if __name__ == "__main__":
    options = parse_args()

    server_desc_files = []
    global descriptors

    if options.pickled_data:
        with open('data.pkl', 'rb') as pkl_input:
            descriptors = pickle.load(pkl_input)

    if options.server_desc:
        # load all server descs into memeory
        for file_name in os.listdir(options.server_desc):
            server_desc_files.append(os.path.join(options.server_desc, file_name))
        load_server_desc(server_desc_files)
        with open('data.pkl', 'wb') as output:
            pickle.dump(descriptors, output)

    linf_fh = open(options.linf, 'w')
    prob_fh = open(options.prob, 'w')
    for file_name in os.listdir(options.consensus):
        file_path = os.path.join(options.consensus, file_name)
        tar_fh = tarfile.open(file_path)
        for member in tar_fh:
            if not member.isfile():
                continue
            tar_file_data=tar_fh.extractfile(member)
            data=tar_file_data.read()
            (linf_string, prob_string) = run(data)
            if linf_string:
                linf_fh.write("%s\n" % (linf_string))
            if prob_string:
                prob_fh.write("%s\n" % (prob_string))
        tar_fh.close()
    linf_fh.close()
    prob_fh.close()
