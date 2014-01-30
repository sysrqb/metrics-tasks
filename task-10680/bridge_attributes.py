#!/usr/bin/python

import sys
import datetime
import os
import pprint
import csv
import argparse
from stem.descriptor import parse_file

class Bridge(object):
  """Encapsulates the attributes of a bridge

  Attributes:
    fingerprint: A string of 40 hex characters uniquely identifying
                 a bridge
    os: A string describing the operating system that the bridge
        is running on
    os_version: A string describing the version of the OS
    tor: A dict that contains the name and version of Tor
    contact: A string providing contact details (hopefully)
    nickname: A string that may not uniquely identify this bridge
    last_published: A datetime describing the last time the bridge
                    published a descriptor
    transports: A dict containing the types of supported pluggable
                transports
    extrainfo_published: A datetime describing the last extrainfo
                         document this bridge published
    bridge_ip_transports: A list or None describing the number of
                          connections this bridge received from
                          distinct transports
    descriptor: A string representing the hash of the bridge's
                descriptor, obtained from the networkstatus
    extrainfo: A string representing the hash of the bridge's
                extrainfo doc, obtained from the networkstatus
    running: A boolean describing the running status of the bridge
  """


  def __init__(self, fingerprint, nickname, published, digest, running=True):
    """Assign values from a descriptor, define the rest for later"""
    self.fingerprint = fingerprint
    self.os = ''
    self.os_version = ''
    self.tor = {}
    self.tor['name'] = 'Tor'
    self.tor['version'] = ''
    self.contact = ''
    self.nickname = nickname
    self.last_published = published
    self.transports = {}
    self.extrainfo_published = datetime.datetime.fromtimestamp(0)
    self.bridge_ip_transports = None
    self.desc_digest = digest
    self.ei_digest = ''
    self.running = running

  def set_descriptor_details(self, platform, os_version, tor_vers,
                             contact, ei_digest, tor_name='Tor'):
    """Set attributes from bridge descriptor"""
    self.os = platform
    self.os_version = os_version
    self.tor['name'] = tor_name
    self.tor['version'] = tor_vers
    self.contact = contact
    self.ei_digest = ei_digest

def unpadded_base64_to_base_16(encoded):
  """Convert an string without padding from base64 to base16
  
  Arg:
    encoded: A string in base 64 without '+' padding

  Returns:
    Base16 encoded string

  Raises:
    TypeError on failure
  """
  decoded = False
  padding = ''
  while not decoded:
    try:
      binstr = base64.b64decode(encoded + padding)
      b16str = base64.b16encode(binstr)
      decoded = True
    except TypeError:
      padding += '+'
      if len(padding) > 3:
        raise TypeError
    return b16str

def parse_networkstatus(fn_ns):
  """Parse networkstatus document

  Arg:
    fn_ns: A string providing the filename of the document

  Returns:
    A dict containing all running bridges indexed by their fingerprint
      and the publication date of the networkstatus document.
  """
  bridges = {}
  publication_date = None
  for bridge in parse_file(fn_ns):
    if not publication_date:
      publication_date = bridge.document.published
    if 'Running' in bridge.flags:
      bridges[bridge.fingerprint] = Bridge(bridge.fingerprint,
                                           bridge.nickname,
                                           bridge.published,
                                           bridge.digest)
  return bridges, publication_date

def parse_bridge_documents(bridges, fn_ns):
  bridges, publication_date = parse_networkstatus(fn_ns)
  print "Parsed %d routers from ns - %r" % (len(bridges), publication_date.isoformat(' '))

  descriptor_errors = 0
  ei_errors = 0
  for bridge in bridges.values():
    desc_path = os.path.join(fn_descriptors_path,
                             bridge.desc_digest.lower())
    if os.path.exists(desc_path) and os.path.isfile(desc_path):
      with open(desc_path, 'r') as fd_descriptors:
        parsed_desc = parse_file(fd_descriptors).next()
        if bridge.fingerprint == parsed_desc.fingerprint:
          if not parsed_desc.operating_system:
            operating_system = find_os_from_platform(parsed_desc.platform)
            if not operating_system:
	      operating_system = ['unspecified']
          else:
            operating_system = parsed_desc.operating_system.split()
          operating_sys = operating_system[0]
	  os_version = ''
          if len(operating_system) > 1:
            os_version = ' '.join(operating_system[1:])
          if not parsed_desc.tor_version:
            tor = find_tor_from_platform(parsed_desc.platform)
            if not tor:
	      tor_version = 'unspecified'
	      tor_name = 'unspecified'
	    else:
	      tor_version, tor_name = tor
          else:
            tor_version = parsed_desc.tor_version
            tor_name = get_tor_name_from_platform(parsed_desc.platform)
          contact = parsed_desc.contact
          ei_digest = parsed_desc.extra_info_digest
          bridge.set_descriptor_details(operating_sys, os_version,
                                        tor_version, contact, ei_digest,
                                        tor_name)
          if not bridge.ei_digest:
            print "Extra-info digest is None: %s" % desc_path
        else:
          print ("Fingerprint mismatch! %s vs %s" %
                (bridge.fingerprint, parsed_desc.fingerprint))
          descriptor_errors += 1
          del bridges[bridge.fingerprint]
          break
    else:
      print "Descriptor does not exist for %s" % bridge.desc_digest
      descriptor_errors += 1
      break
    if bridge.ei_digest:
      ei_path = os.path.join(fn_extrainfo_path, bridge.ei_digest.lower())
      if os.path.exists(ei_path) and os.path.isfile(ei_path):
        with open(ei_path, 'r') as fd_extrainfo:
          parsed_ei = parse_file(fd_extrainfo).next()
          bridge.transports = parsed_ei.transport
          bridge.extrainfo_published = parsed_ei.published
	  bridge.bridge_ip_transports = parsed_ei.ip_transports
      else:
        print ("Extra-info document does not exist for %s, specified in "
	      "%s" % (bridge.fingerprint, bridge.desc_digest))
        ei_errors += 1
  print ("%d errors during descriptor parsing, %d errors during "
        "extra-info parsing" % (descriptor_errors, ei_errors))
  return bridges

def find_publication_date_of_ns(fd_ns):
  """Return the publication date (as a datetime) or None"""
  for line in fd_ns:
    if line.startswith("@type"):
      next
    if line.startswith("published "):
      date = line[10:].strip()
      return datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
  return None


def find_most_recent_ns(ns_dir):
  """Search `list_of_files` for most recent ns"""
  newest = {'name': None, 'date': datetime.datetime.fromtimestamp(0)}
  list_of_files = os.listdir(ns_dir)
  for filename in list_of_files:
    absfilename = os.path.join(ns_dir, filename)
    with open(absfilename) as ns:
      for line in ns:
        dt = find_publication_date_of_ns(ns)
        if dt:
          if dt > newest['date']:
            newest['name'] = absfilename
            newest['date'] = dt
          break
  return newest

def parse_all_ns(ns_dir):
  """Return a list of dicts, containing filepath and pub date of ns"""
  nsinfo = {'name': None, 'date': None}
  all_ns = []
  list_of_files = os.listdir(ns_dir)
  for filename in list_of_files:
    absfilename = os.path.join(ns_dir, filename)
    with open(absfilename) as ns:
      for line in ns:
        dt = find_publication_date_of_ns(ns)
        nsinfo['name'] = absfilename
        nsinfo['date'] = dt
        all_ns.append(nsinfo)
        nsinfo = {'name': None, 'date': None}
        break
  return all_ns

def parse_platform_line(platform):
  """Let's hope this follows the normal convention"""
  breakdown = {}
  if platform:
    items = platform.split()
    if len(items) > 1:
      # node-Tor 0.0.53 on Linux x86_64
      if len(items) >= 4:
        breakdown['tor_name'] = items[0]
        breakdown['tor_vers'] = items[1]
        breakdown['os'] = items[3]
        breakdown['os_vers'] = ''
      if len(items) > 4:
        breakdown['os_vers'] = ' '.join(items[4:])
      return breakdown
  return None
 
def find_os_from_platform(platform):
  """Let's hope this follows the normal convention"""

  if platform:
    parsed = parse_platform_line(platform)
    operating_system = ' '.join([parsed['os'], parsed['os_vers']]).split()
    return operating_system
  else:
    return None
     
def find_tor_from_platform(platform):
  """Let's hope this follows the normal convention. Get version and name"""
  if platform:
    parsed = parse_platform_line(platform)
    return parsed['tor_vers'], parsed['tor_name']
  else:
    return None

def get_tor_name_from_platform(platform):
  """Return the name of the Tor impl provided on the platform line"""
  if platform:
    tor = find_tor_from_platform(platform)
    if tor:
      _, tor_name = tor
      return tor_name
  return 'unspecified'
 
def count_unique_os_types(bridges):
  """Count the distinct OS types and versions from `bridges`
  
  Args:
    bridges: A dict with fingerprint->bridge key-value mappings

  Returns:
    os_types: A dict mapping OS type to the number of occurrences
    os_version: A dict mapping OS version to the number of occurrences
  """

  opsys = {}
  opsys['os_types'] = {}
  opsys['os_versions'] = {}
  opsys['ec2_os_types'] = {}
  opsys['ec2_os_versions'] = {}
  for bridge in bridges.values():
    os = bridge.os
    if os in opsys['os_types']:
      opsys['os_types'][os] += 1
    else:
      opsys['os_types'][os] = 1
    version = bridge.os_version
    if os in opsys['os_versions']:
      if version in opsys['os_versions'][os]:
        opsys['os_versions'][os][version] += 1
      else:
        opsys['os_versions'][os][version] = 1
    else:
      opsys['os_versions'][os] = {}
      opsys['os_versions'][os][version] = 1

    if bridge.nickname.startswith('ec2bridger'):
      if os in opsys['ec2_os_types']:
        opsys['ec2_os_types'][os] += 1
      else:
        opsys['ec2_os_types'][os] = 1
      if os in opsys['ec2_os_versions']:
        if version in opsys['ec2_os_versions'][os]:
          opsys['ec2_os_versions'][os][version] += 1
        else:
          opsys['ec2_os_versions'][os][version] = 1
      else:
        opsys['ec2_os_versions'][os] = {}
        opsys['ec2_os_versions'][os][version] = 1
  return opsys

def count_transports(bridges):
  """Count the pluggable transports from `bridges`
  
  Args:
    bridges: A dict with fingerprint->bridge key-value mappings

  Returns:
    transports: A dict mapping transports to the number of occurrences
    os_version: A dict mapping OS version to the number of occurrences
                of each transport
  """

  transports = {}
  os_versions = {}
  for bridge in bridges.values():
    if not bridge.transports:
      continue
    os_type = bridge.os
    os_version = str(bridge.os_version)

    if os_type not in os_versions:
      os_versions[os_type] = {}
    if os_version not in os_versions[os_type]:
      os_versions[os_type][os_version] = {}

    for transport in set(bridge.transports):
      if transport in transports:
        transports[transport] += 1
      else:
        transports[transport] = 1

      if transport in os_versions[os_type][os_version]:
        os_versions[os_type][os_version][transport] += 1
      else:
        os_versions[os_type][os_version][transport] = 1
  return transports, os_versions

def count_extorports(bridges):
  """Try to count the number of configured ExtORPorts from `bridges`
  
  Args:
    bridges: A dict with fingerprint->bridge key-value mappings

  Returns:
    confed_extor: An int count of how many ExtOR ports are configured
    unconfed_extor: An int count of how many ExtOR ports are unconfigured
                    or misconfigured
    neither: An int count of how many bridges do not support the ExtOR port
  """

  confed_extor = unconfed_extor = neither = 0
  for bridge in bridges.values():
    if (bridge.transports and bridge.bridge_ip_transports and
       len(bridge.bridge_ip_transports) == 1):
      unconfed_extor += 1
    elif bridge.transports and bridge.bridge_ip_transports:
      confed_extor += 1
    else:
      neither += 1
  return confed_extor, unconfed_extor, neither

def count_contact_set(bridges):
  """Ccount the number of 'contact' lines from `bridges`
  
  Args:
    bridges: A dict with fingerprint->bridge key-value mappings

  Returns:
    contact: An int
  """

  contact = 0
  for bridge in bridges.values():
    if bridge.contact:
      contact += 1
  return contact

def count_by_tor_versions(bridges):
  """Ccount the number of distinct version of Tor from `bridges`
  
  Args:
    bridges: A dict with fingerprint->bridge key-value mappings

  Returns:
    versions: A dict mapping tor's name and version to a count
  """

  versions = {}
  ec2versions = {}
  for bridge in bridges.values():
    index = "%s-%s" % (bridge.tor['version'],bridge.tor['name'])
    if index in versions:
      versions[index] += 1
    else:
      versions[index] = 1
    if bridge.nickname.startswith('ec2bridger'):
      if index in ec2versions:
        ec2versions[index] += 1
      else:
        ec2versions[index] = 1
  return versions, ec2versions

def pretty_print_attributes(attributes):
  """Pretty print the attributes from `heading`"""
  for title, values in attributes.items():
    print title
    if values:
      pprint.pprint(values)

def write_to_csv(header, values, filename):
  """Create or append to `filename` `values` in csv-format

  Args:
    header: A string that defines the title of the fields
    values: A list of dicts that contain values for each field
    filename: A string that states the file to create or open
  """

  #with open(filename, 'wb') as csvfile:
  csvfile = open(filename, 'ab')
  #print "writing csv to file. %d rows" % len(values)
  #csvfile.write("This is a test - %s" % str(len(values)))
  attribwriter = csv.DictWriter(csvfile, header)
  attribwriter.writeheader()
    #jkattribwriter.writerows(values)
  for row in values:
    attribwriter.writerow(row)
  csvfile.close()

def format_for_csv(date, opsys, ec2opsys, versions, ec2versions, filename):
  """Format the args into a dict that can be passwd to write_to_csv"""

  #fields = "date,flag,country,version,platform,ec2bridge,relays,bridges"
  fields = ['date', 'flag', 'country', 'version', 'platform', 'ec2bridge', 'relays', 'bridges']
  list_of_values = []

  #print "Platforms: %s" % opsys
  values = {}
  ec2values = {}
  for vers in versions:
    if vers[:5] in values:
      #print "Adding %s to version %s" % (str(versions[vers]), vers[:5])
      values[vers[:5]]['value'] += versions[vers]
    else:
      #print "Adding %s to version %s" % (str(versions[vers]), vers[:5])
      values[vers[:5]] = {'field': 'version', 'value': versions[vers]}
  for vers in ec2versions:
    if vers[:5] in ec2values:
      #print "Adding %s to version %s" % (str(ec2versions[vers]), vers[:5])
      ec2values[vers[:5]]['value'] += ec2versions[vers]
    else:
      #print "Adding %s to version %s" % (str(ec2versions[vers]), vers[:5])
      ec2values[vers[:5]] = {'field': 'version', 'value': ec2versions[vers]}
  #print "%r" % values
  for platform in opsys:
    if platform in values:
      #print "Adding %s to platform %s" % (str(opsys[platform]), platform)
      values[platform]['value'] += opsys[platform]
    else:
      #print "Adding %s to platform %s" % (str(opsys[platform]), platform)
      values[platform] = {'field': 'platform', 'value': opsys[platform]}
  for platform in ec2opsys:
    if platform in ec2values:
      #print "Adding %s to ec2 platform %s" % (str(ec2opsys[platform]), platform)
      ec2values[platform]['value'] += ec2opsys[platform]
    else:
      #print "Adding %s to ec2 platform %s" % (str(ec2opsys[platform]), platform)
      ec2values[platform] = {'field': 'platform', 'value': ec2opsys[platform]}

  #print "%r" % values

  for value in values:
    csv_values = {}
    for field in fields:
      csv_values[field] = ''
    csv_values['date'] = date.strftime("%Y-%m-%d")
    csv_values[values[value]['field']] = value
    csv_values['bridges'] = values[value]['value']
    if value in ec2values:
      csv_values['ec2bridge'] = ec2values[value]['value']
    list_of_values.append(csv_values)
  # Grab everything else we missed
  for value in ec2values:
    csv_values = {}
    if value not in values:
      for field in fields:
        csv_values[field] = ''
      csv_values['date'] = date.strftime("%Y-%m-%d")
      csv_values[ec2values[value]['field']] = value
      csv_values['bridges'] = ec2values[value]['value']
      list_of_values.append(csv_values)

  #print "%r" % list_of_values
  write_to_csv(fields, list_of_values, filename)

def get_metrics_csv(bridges, publication_date, csv_filename):
  """Get values and output csv file"""
  opsys = count_unique_os_types(bridges)
  transports, by_os = count_transports(bridges)
  confed_extor, unconfed_extor, neither = count_extorports(bridges)
  contacts = count_contact_set(bridges)
  versions, ec2versions = count_by_tor_versions(bridges)

  format_for_csv(publication_date, opsys['os_types'], opsys['ec2_os_types'], versions, ec2versions, csv_filename)

def format_for_pretty_print(os, os_versions, transports, transportsbyos,
                            confed_extor, unconfed_extor, unavail_extor,
                            contacts, tor_versions):

  attributes = {}
  attributes["\nBridges by OS Version:"] = os_versions
  attributes["\nTransports by type:"] = transports
  attributes[ "\nTransports by OS type:"] = by_os
  attributes[
          ("\nExtORPorts: Configured: %d, Unconfigured: %d, "
           "Unavailable: %d" %
           (confed_extor, unconfed_extor, neither))] = None
  attributes["\nBridges with contacts info: %d" % contacts] = None
  attributes["\nBridges by Tor versions:"] = versions

  #pretty_print_attributes(attributes)

def handle_options(argv):
  """Handle the command line arguments"""
  parser = argparse.ArgumentParser(description="Obtain bridge metrics")
  parser.add_argument('-d', '--desc', help='The directory that contains bridge descriptors')
  parser.add_argument('-e', '--ei', help='The directory that contains bridge extra-info documents')
  parser.add_argument('-n', '--ns', help='The directory that contains bridge networkstatus documents')
  parser.add_argument('-s', '--nsfile', help='The file path to a specific bridge networkstatus document')
  parser.add_argument('-o', '--output', help='The directory where the output is saved')
  parser.add_argument('-O', '--output-name', help='The filename where the output is saved')
  parser.add_argument('-a', '--parse-all', help='Parse all documents, not only the most recent', action='store_true')

  args = parser.parse_args()
  return args.desc, args.ei, args.ns, args.nsfile, args.output, args.output_name, args.parse_all, parser.print_help

if __name__ == "__main__":
  csv_filename = 'bridges.csv'
  current_dir = os.getcwd()
  exe = sys.argv[0]
  fn_descriptors_path = None
  fn_extrainfo_path = None
  fn_networkstatus_path = None

  (fn_descriptors_dir,
  fn_extrainfo_dir,
  fn_networkstatus_dir,
  fn_networkstatus_file,
  fn_output_dir,
  fn_output_file,
  parse_all,
  usage) = handle_options(sys.argv)

  if fn_descriptors_dir:
    fn_descriptors_path = os.path.abspath(fn_descriptors_dir)
    if not (os.path.exists(fn_descriptors_path) and
            os.path.isdir(fn_descriptors_path)):
      print ("\nFatal Error: %s is not a path to a directory of bridge "
             "descriptors.\n" % fn_descriptors_path)
      usage()
      sys.exit()
  if fn_extrainfo_dir:
    fn_extrainfo_path = os.path.abspath(fn_extrainfo_dir)
    if not (os.path.exists(fn_extrainfo_path) and
           os.path.isdir(fn_extrainfo_path)):
      print ("\nFatal Error: %s is not a path to a directory of bridge "
             "extra-info documents.\n" % fn_extrainfo_path)
      usage()
      sys.exit()
  if fn_networkstatus_dir:
    fn_networkstatus_path = os.path.abspath(fn_networkstatus_dir)
    if not (os.path.exists(fn_networkstatus_path) and
            os.path.isdir(fn_networkstatus_path)):
      print ("\nFatal Error: %s is not a path to a directory of "
             "networkstatus files.\n"
             % fn_networkstatus_path)
      usage()
      sys.exit()
  elif fn_networkstatus_file:
    fn_networkstatus_path = os.path.abspath(fn_networkstatus_file)
    if not (os.path.exists(fn_networkstatus_path) and
            os.path.isfile(fn_networkstatus_path)):
      print ("\nFatal Error: %s is not a networkstatus file.\n"
             % fn_networkstatus_file)
      usage()
      sys.exit()
  else:
    print ("\nFatal Error: Please either specify a path to a specific "
           "file or a directory of networkstatus documents.\n")
    usage()
    sys.exit()
    
  if fn_output_dir:
    fn_output_path = os.path.abspath(fn_output_dir)
  else:
    fn_output_path = os.getcwd()

  if fn_output_file:
    csv_filename = fn_output_file

  bridges = {}
  os.chdir(fn_output_path)
  publication_date = None
  all_ns = []
  if parse_all:
    print "Parsing all networkstatus documents"
    all_ns = parse_all_ns(fn_networkstatus_path)
  elif fn_networkstatus_file:
    fn_ns = {'name': fn_networkstatus_file, 'date': None}
    with open(fn_networkstatus_file, 'r') as fd_ns:
      fn_ns['date'] = find_publication_date_of_ns(fd_ns)
    if not fn_ns['date']:
      print "Error: Networkstatus document does not contain a publication date!"
      sys.exit()
    all_ns.append(fn_ns)
  else: 
    fn_ns = find_most_recent_ns(fn_networkstatus_path)
    all_ns.append(fn_ns)

  for fn_ns in all_ns:
    bridges = parse_bridge_documents(bridges, fn_ns['name'])
    publication_date = fn_ns['date']

    get_metrics_csv(bridges, publication_date, csv_filename)
