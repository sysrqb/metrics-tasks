#!/usr/bin/python

import sys
import datetime
import os
import pprint
import csv
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

    def set_descriptor_details(self, platform, os_version, tor_name,
                                     tor_vers, contact):
      self.os = platform
      self.os_version = os_version
      self.tor['name'] = tor_name
      self.tor['version'] = tor_vers
      self.contact = contact

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

def find_most_recent_ns(list_of_files):
  """Search `list_of_files` for most recent ns"""
  newest = {'name': None, 'date': datetime.datetime.fromtimestamp(0)}
  for filename in list_of_files:
    with open(filename) as ns:
      for line in ns:
        if line.startswith("@type"):
	  next
	if line.startswith("published "):
	  date = line[10:].strip()
	  dt = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
          if dt > newest['date']:
            newest['name'] = filename
            newest['date'] = dt
	  break
  return newest['name']

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
  """Let's hope this follows the normal convention"""
  if platform:
    parsed = parse_platform_line(platform)
    tor = {}
    tor['version'] = parsed['tor_vers']
    tor['name'] = parsed['tor_name']
    return tor
  else:
    return None
 
def count_unique_os_types(bridges):
  """Count the distinct OS types and versions from `bridges`
  
  Args:
    bridges: A dict with fingerprint->bridge key-value mappings

  Returns:
    os_types: A dict mapping OS type to the number of occurrences
    os_version: A dict mapping OS version to the number of occurrences
  """

  os_types = {}
  os_versions = {}
  for bridge in bridges.values():
    os = bridge.os
    if os in os_types:
      os_types[os] += 1
    else:
      os_types[os] = 1
    version = bridge.os_version
    if os in os_versions:
      if version in os_versions[os]:
        os_versions[os][version] += 1
      else:
        os_versions[os][version] = 1
    else:
      os_versions[os] = {}
      os_versions[os][version] = 1
  return os_types, os_versions

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
  for bridge in bridges.values():
    index = "%s-%s" % (bridge.tor['version'],bridge.tor['name'])
    if index in versions:
      versions[index] += 1
    else:
      versions[index] = 1
  return versions

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
  print "writing csv to file. %d rows" % len(values)
  #csvfile.write("This is a test - %s" % str(len(values)))
  attribwriter = csv.DictWriter(csvfile, header)
  attribwriter.writeheader()
    #jkattribwriter.writerows(values)
  for row in values:
    attribwriter.writerow(row)
  csvfile.close()

def format_for_csv(date, platforms, versions, filename):
  """Format the args into a dict that can be passwd to write_to_csv"""

  #fields = "date,flag,country,version,platform,ec2bridge,relays,bridges"
  fields = ['date', 'flag', 'country', 'version', 'platform', 'ec2bridge', 'relays', 'bridges']
  list_of_values = []

  print "Platforms: %s" % platforms
  values = {}
  for vers in versions:
    if vers[:5] in values:
      print "Adding %s to version %s" % (str(versions[vers]), vers[:5])
      values[vers[:5]]['value'] += versions[vers]
    else:
      print "Adding %s to version %s" % (str(versions[vers]), vers[:5])
      values[vers[:5]] = {'field': 'version', 'value': versions[vers]}
  print "%r" % values
  for platform in platforms:
    if platform in values:
      print "Adding %s to platform %s" % (str(platforms[platform]), platform)
      values[platform]['value'] += platforms[platform]
    else:
      print "Adding %s to platform %s" % (str(platforms[platform]), platform)
      values[platform] = {'field': 'platform', 'value': platforms[platform]}
  print "%r" % values

  for value in values:
    csv_values = {}
    for field in fields:
      csv_values[field] = ''
    csv_values['date'] = date.strftime("%Y-%m-%d")
    csv_values[values[value]['field']] = value
    csv_values['bridges'] = values[value]['value']
    list_of_values.append(csv_values)

  print "%r" % list_of_values
  write_to_csv(fields, list_of_values, filename)

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

def usage(exe):
  """Print the helpful description"""
  helpful = ("syntax: %s [-a] <path/to/descriptors> "
            "<path/to/extra-info documents> <path/to/networkstatuses>"
            "\n\n"
            "  -a      Parse all files, the entire available history."
            "\n            only parses the most recent, by default."
	    % exe)
  print "%s" % helpful
  sys.exit()
      
    
if __name__ == "__main__":
  csv_filename = 'bridges.csv'
  parse_all = False
  current_dir = os.getcwd()
  exe = sys.argv[0]

  if len(sys.argv) == 4:
    fn_descriptors_dir = sys.argv[1]
    fn_extrainfo_dir = sys.argv[2]
    fn_networkstatus_dir = sys.argv[3]
  elif len(sys.argv) == 5:
    if sys.argv[1] == '-a':
      parse_all = True
    else:
      usage(exe)
    fn_descriptors_dir = sys.argv[2]
    fn_extrainfo_dir = sys.argv[3]
    fn_networkstatus_dir = sys.argv[4]
  else:
    usage(exe)

  fn_descriptors_path = os.path.abspath(fn_descriptors_dir)
  fn_extrainfo_path = os.path.abspath(fn_extrainfo_dir)
  fn_networkstatus_path = os.path.abspath(fn_networkstatus_dir)

  if not (os.path.exists(fn_descriptors_path) and
          os.path.isdir(fn_descriptors_path)):
    print ("%s is not a path to the directory of bridge descriptors" %
            fn_descriptors_path)
    usage(exe)
  if not (os.path.exists(fn_extrainfo_path) and
         os.path.isdir(fn_extrainfo_path)):
    print ("%s is not a path to the directory of bridge extra-info "
           "documents" % fn_extrainfo_path)
    usage(exe)
  if not (os.path.exists(fn_networkstatus_path) and
          os.path.isdir(fn_extrainfo_path)):
    print ("%s is not a path to the directory of networkstatus files "
           % fn_networkstatus_path)
    usage(exe)

  bridges = {}
  os.chdir(fn_networkstatus_path)
  publication_date = None
  if parse_all:
    all_bridges = parse_all_ns(fn_networkstatus_path)
  else:
    fn_ns = find_most_recent_ns(os.listdir(os.getcwd()))
    for bridge in parse_file(fn_ns):
      if not publication_date:
        publication_date = bridge.document.published
      if 'Running' in bridge.flags:
        bridges[bridge.fingerprint] = Bridge(bridge.fingerprint,
                                             bridge.nickname,
                                             bridge.published,
                                             bridge.digest)
    print "Parsed %d routers from ns" % len(bridges)

  os.chdir(fn_descriptors_path)
  descriptor_errors = 0
  ei_errors = 0
  for bridge in bridges.values():
    desc_path = os.path.join(fn_descriptors_path, bridge.desc_digest.lower())
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
          bridge.os = operating_system[0]
          if len(operating_system) > 1:
            bridge.os_version = ' '.join(operating_system[1:])
          if not parsed_desc.tor_version:
            bridge.tor = find_tor_from_platform(parsed_desc.platform)
            if not bridge.tor:
	      bridge.tor['version'] = 'unspecified'
	      bridge.tor['name'] = 'unspecified'
          else:
            bridge.tor['version'] = parsed_desc.tor_version
          bridge.contact = parsed_desc.contact
          bridge.ei_digest = parsed_desc.extra_info_digest
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
        print "Extra-info document does not exist for %s" % bridge.digest
        ei_errors += 1


  print ("%d errors during descriptor parsing, %d errors during "
        "extra-info parsing" % (descriptor_errors, ei_errors))
    
  print "%d bridges in total" % len(bridges)
  os_platforms, os_versions = count_unique_os_types(bridges)
  transports, by_os = count_transports(bridges)
  confed_extor, unconfed_extor, neither = count_extorports(bridges)
  contacts = count_contact_set(bridges)
  versions = count_by_tor_versions(bridges)

  #format_for_pretty_print(os_platforms, os_versions, transports, by_os,
  #                        confed_extor, unconfed_extor, neither,
  #                        contacts, versions)

  os.chdir(current_dir)
  format_for_csv(publication_date, os_platforms, versions, csv_filename)
