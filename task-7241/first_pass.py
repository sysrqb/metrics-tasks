# calculate frac_relays, frac_cw to compare consensus documents over time

# let Y be the base document and X be some hours before the base document
# frac_relays = count(intersection(Y, X)) / count(Y)
# frac_cw = sum(cw(Y) over intersection(Y,X)) / sum(cw(Y)) 

import os
from datetime import datetime, timedelta
from stem.descriptor import parse_file

# generate expected consensus filepath from time
def filepath_from_time(cur_datetime):
	return os.path.join(
		'consensuses-%s' % cur_datetime.strftime('%Y-%m'),
		cur_datetime.strftime('%d'),
		'%s-consensus' % cur_datetime.strftime('%Y-%m-%d-%H-%M-%S'),
	)

# router bw storage by fingerprint
router_data = {}

# unit time interval
time_interval = timedelta(0, 60*60) # one hour

# interval multipliers for analysis: 1 hour to 7 days
time_interval_list = [1,2,3,4,5,6,12,24,36,48,72,96,120,144,168] # hours

# base consensuses for examination
initial_time_info_bound = datetime(2012, 1, 1) # inclusive
final_time_info_bound = datetime(2013, 1, 1) # exclusive

# data range for consensuses
initial_time_data_bound = datetime(2011, 12, 1) # inclusive
final_time_data_bound = datetime(2013, 1, 1) # exclusive

# load information
cur_datetime = initial_time_data_bound
while cur_datetime < final_time_data_bound:
	cur_filepath = filepath_from_time(cur_datetime)
	cur_filename = os.path.basename(cur_filepath)	

	try:
		with open(cur_filepath) as consensus_file:
			router_data[cur_filename] = dict([(r.fingerprint, r.bandwidth) 
				for r in parse_file(consensus_file)])
	except IOError:
		pass # file does not exist (possible situation) and iterate

	# next file to read
	cur_datetime += time_interval

# iterate over base consensuses for frac_relays, frac_cw
cur_datetime = initial_time_info_bound
while cur_datetime < final_time_info_bound:
	cur_filepath = filepath_from_time(cur_datetime) # current
	cur_filename = os.path.basename(cur_filepath) # current	

	# find base data, if data exists
	if cur_filename in router_data:
		base_routers = router_data[cur_filename]
		base_router_count = len(router_data[cur_filename])
		base_router_bw = sum(router_data[cur_filename].values())

		# for each analysis analysis interval, find comparison locator
		for time_interval_multiplier in time_interval_list:
			comp_time_interval = time_interval_multiplier*time_interval
			comp_datetime = cur_datetime - comp_time_interval

			comp_filepath = filepath_from_time(comp_datetime) # comp
			comp_filename = os.path.basename(comp_filepath) # comp

			# find comparison data, if data exists
			if comp_filename in router_data:
				router_overlap_count = 0
				base_router_overlap_bw = 0
		
				# determine intersection(Y,X) and sum cw over intersection(Y,X)
				for fingerprint in router_data[comp_filename]:
					if fingerprint in base_routers:
						router_overlap_count += 1
						base_router_overlap_bw += base_routers[fingerprint]

				# determine ratios
				frac_relays = float(router_overlap_count)/float(base_router_count)
				frac_cw = float(base_router_overlap_bw)/float(base_router_bw)

				# output
				print '%s,%d,%f,%f,%d,%d,%s' % (cur_filename, time_interval_multiplier, 
					frac_relays, frac_cw, cur_datetime.month, cur_datetime.day, 
					cur_datetime.strftime('%w'))

	# next base consensus		
	cur_datetime += time_interval

