import sys
from datetime import datetime, timedelta

from stem.descriptor.networkstatus import NetworkStatusDocumentV3

# http://stackoverflow.com/questions/82831/how-do-i-check-if-a-file-exists-using-python
def file_check(file_path):
	try:
		with open(file_path) as f:
			return True
	except IOError:
		return False

def filepath_from_time(cur_datetime):
	consensus_path = 'consensuses-'
	consensus_path += cur_datetime.strftime('%Y-%m')
	consensus_path += '/'
	consensus_path += cur_datetime.strftime('%d')
	consensus_path += '/'
	consensus_path += cur_datetime.strftime('%Y-%m-%d-%H-%M-%S')
	consensus_path += '-consensus'

	return consensus_path

def filename_from_time(cur_datetime):
	consensus_filename = cur_datetime.strftime('%Y-%m-%d-%H-%M-%S')
	consensus_filename += '-consensus'

	return consensus_filename

time_interval = timedelta(0, 60*60) # one hour

# base consensuses for examination
initial_time_info_bound = datetime(2012, 1, 1) # inclusive
final_time_info_bound = datetime(2013, 1, 1) # exclusive

router_data = {}

# data range for consensuses
initial_time_data_bound = datetime(2011, 12, 1) # inclusive
final_time_data_bound = datetime(2013, 1, 1) # exclusive

# load information
cur_datetime = initial_time_data_bound - time_interval
while cur_datetime < final_time_data_bound - time_interval:
	cur_datetime += time_interval

	cur_filepath = filepath_from_time(cur_datetime)
	cur_filename = filename_from_time(cur_datetime)	

	if file_check(cur_filepath) == True:
		consensus_file = open(cur_filepath, 'r')
		consensus_file.readline()
		consensus = NetworkStatusDocumentV3(consensus_file.read())
		consensus_file.close()

		routers = {}
		for router in consensus.routers:
			routers[router.fingerprint] = router.bandwidth

		router_data[cur_filename] = routers

# interval multipliers
time_interval_list = [1,2,3,4,5,6,12,24,36,48,72,96,120,144,168] # hours

# iterate over base consensuses
cur_datetime = initial_time_info_bound - time_interval
while cur_datetime < final_time_info_bound - time_interval:
	cur_datetime += time_interval

	cur_filepath = filepath_from_time(cur_datetime) # current
	cur_filename = filename_from_time(cur_datetime) # current	

	if file_check(cur_filepath) == True:
		base_routers = router_data[cur_filename]
		base_router_count = 0
		base_router_bandwidth = 0
		for fingerprint in router_data[cur_filename].keys():
			base_router_count += 1
			base_router_bandwidth += router_data[cur_filename][fingerprint]

		for comparison_time_interval_multiplier in time_interval_list:
			comparison_time_interval = timedelta(0, comparison_time_interval_multiplier*60*60)
			comparison_datetime = cur_datetime - comparison_time_interval

			comparison_filepath = filepath_from_time(comparison_datetime) # comparison
			comparison_filename = filename_from_time(comparison_datetime) # comparison

			if file_check(comparison_filepath) == True:
				comparison_router_count = 0
				comparison_router_bandwidth = 0
				comparison_router_overlap_bandwidth = 0
				base_router_overlap_bandwidth = 0
				comparison_router_overlap_count = 0
		
				for fingerprint in router_data[comparison_filename].keys():
					comparison_router_count += 1
					comparison_router_bandwidth += router_data[comparison_filename][fingerprint]

					if fingerprint in base_routers:
						base_router_overlap_bandwidth += base_routers[fingerprint]
						comparison_router_overlap_count += 1
						comparison_router_overlap_bandwidth += router_data[comparison_filename][fingerprint]

				frac_relays = float(comparison_router_overlap_count)/float(base_router_count)
				frac_cw = float(base_router_overlap_bandwidth)/float(base_router_bandwidth)

				print '%s,%d,%f,%f,%d,%d,%s' % (cur_filename, comparison_time_interval_multiplier, frac_relays, frac_cw, cur_datetime.month, cur_datetime.day, cur_datetime.strftime('%w'))

