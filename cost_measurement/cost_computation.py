# Compute and analyze the results of cost_measurement.py
# Use correlation analysis and other methods to compute the relations between user complaints and costs
# -*- coding: utf-8 -*-
# __author__  = "Cuiyun Gao"
# __version__ = "2.0"
# __date__    ＝ "3/12/2018"


import os, sys
import json
import numpy as np
from datetime import datetime
from get_stat import stat
from sklearn import linear_model
from pcapng import FileScanner


# VARIABLES
count_num  = 3 # measurement times
beta_l     = 1.2 # coefficient for low packet rate
beta_h     = 0.8 # coefficient for high packet rate
threshold  = 25 # threshold for differenciate two packet rates
base_l     = 238.7 # noise for low packet rate
base_h     = 247.0 # noise for high packet rate



class analyzeCost:
	"""docstring for analyzeCost"""
	def __init__(self):
		self.costs = {}
		self.costs["data_time"]     = []  # the time when data collected
		self.costs["data_bytes"]    = 0
		self.costs["packet_num"]    = 0
		self.costs["packet_rate"]   = 0.0
		self.costs["cpu"]           = []
		self.costs["cpu_ave"]       = None
		self.costs["rss"]           = []
		self.costs["rss_ave"]       = None
		self.costs["us_ratio"]      = []
		self.costs["thread_num"]    = []
		self.costs["freq"]          = []
		self.costs["freq_ave"]      = None
		self.costs["battery_ave"]   = None

	def read_dns(self, f_dns):
		fr_dns = open(f_dns).read().splitlines()
		for idx, lines in enumerate(fr_dns):
			line = lines.split()
			if line:
				try:
					self.costs["data_time"].append(datetime.strptime(line[0], "%H:%M:%S.%f"))
				except ValueError:
					continue
				self.costs["packet_num"] += 1
				try:
					self.costs["data_bytes"] += int(line[-1].strip(")"))
				except ValueError:
					continue
		try:
			start_time = self.costs["data_time"][0]
		except IndexError:
			print(f_dns)
		end_time   = self.costs["data_time"][-1]
		self.costs["packet_rate"] = float(self.costs["packet_num"])/((end_time - start_time).total_seconds())
		# print("Len of data time is %d." % len(self.costs["data_time"]))
		# print("Time duration is %s." % ((end_time - start_time).total_seconds()))
		# print("Rate of packet is %d." % self.costs["packet_rate"])



	def read_top(self, f_top):
		fr_top = open(f_top).read().splitlines()
		for idx, lines in enumerate(fr_top):
			line = lines.split()
			try:
				self.costs["cpu"].append(int(line[2].strip('%')))
				self.costs["rss"].append(int(line[6].strip('K')))
			except IndexError:
				continue
		self.costs["rss_ave"] = np.mean(self.costs["rss"])

	def read_stat(self, f_stat):
		fr_stat = open(f_stat).read().splitlines()
		for idx, lines in enumerate(fr_stat):
			try:
				line = stat(lines)
				self.costs["us_ratio"].append(int(line['utime'])+int(line['stime']))
				self.costs["thread_num"].append(int(line['num_threads']))
			except IndexError:
				continue

	def read_freq(self, f_cpufreq):
		fr_freq = open(f_cpufreq).read().splitlines()
		for idx, lines in enumerate(fr_freq):
			try:
				self.costs["freq"].append(int(lines)/1000)
			except ValueError:
				continue

	def battery(self):
		self.costs["cpu_ave"]  = np.mean(self.costs["cpu"])
		self.costs["freq_ave"] = np.mean(self.costs["freq"])
		b_freq, b_idle         = self.train(self.costs["freq_ave"])
		if self.costs["packet_rate"] > threshold:
			b_packet    = beta_h
			base_packet = base_h
		else:
			b_packet    = beta_l
			base_packet = base_l
		# print('cpu consumption is ' + str((self.costs['cpu_ave']*b_freq*0.01 + b_idle)))
		# print('traffic consumption is ' + str((b_packet * self.costs['packet_rate'] + base_packet)))
		self.costs["battery_ave"] = ((self.costs['cpu_ave']*b_freq*0.01 + b_idle) + (b_packet * self.costs['packet_rate'] + base_packet))
		return self.costs

	# train to get the parameters for computing battery
	def train(self, freq):
		X    = [[245.0], [384.0], [460.8], [499.2], [576.0], [614.4], [652.8], [691.2], [768.0], [806.4], [844.8], [998.4]]
		y1   = [201.0, 257.2, 286.0, 303.7, 332.7, 356.3, 378.4, 400.3, 443.4, 470.7, 493.1, 559.5]
		clf1 = linear_model.BayesianRidge()
		clf1.fit(X,y1)
		y2   = [35.1, 39.5, 35.2, 36.5, 39.5, 38.5, 36.7, 39.6, 40.2, 38.4, 43.5, 45.6]
		clf2 = linear_model.BayesianRidge()
		clf2.fit(X, y2)
		beta_freq = clf1.predict([[freq]])
		beta_idle = clf2.predict([[freq]])
		return beta_freq[0], beta_idle[0]


def compute_cost():
	costs_dic = {} # all the costs for all the apps
	issues = ["memory", "cpu", "packet", "data", "battery"]

	pack_name  = open(time_log_path).readlines()[1].split()[-1]

	# INITIALIZE VARIABLES "costs_dic"
	if pack_name not in costs_dic:
		costs_dic[pack_name] = {}
		for issue in issues:
			costs_dic[pack_name][issue] = {}
			for idx in range(1, count_num+1):
				costs_dic[pack_name][issue][idx] = {}

	# read data from files
	for count in range(1, count_num+1):
		ad_f_dns     = os.path.join(ad_path, str(count) + "_dns_log.cap")
		ad_f_top     = os.path.join(ad_path, str(count) + "_top.txt")
		ad_f_stat    = os.path.join(ad_path, str(count) + "_stat.txt")
		ad_f_cpufreq = os.path.join(ad_path, str(count) + "_cpufreq.txt")
		noad_f_dns   = os.path.join(no_ad_path, str(count) + "_dns_log.cap")
		noad_f_top   = os.path.join(no_ad_path, str(count) + "_top.txt")
		noad_f_stat  = os.path.join(no_ad_path, str(count) + "_stat.txt")
		noad_f_cpufreq = os.path.join(no_ad_path, str(count) + "_cpufreq.txt")

		# compute the costs for with ads
		ad_costs  = analyzeCost()
		ad_costs.read_dns(ad_f_dns)
		ad_costs.read_top(ad_f_top)
		ad_costs.read_stat(ad_f_stat)
		ad_costs.read_freq(ad_f_cpufreq)
		ad_dic = ad_costs.battery()

		# oompute the costs for without ads
		noad_costs = analyzeCost()
		noad_costs.read_dns(noad_f_dns)
		noad_costs.read_top(noad_f_top)
		noad_costs.read_stat(noad_f_stat)
		noad_costs.read_freq(noad_f_cpufreq)
		noad_dic = noad_costs.battery()

		# save to "costs_dic" VARIABLE
		costs_dic[pack_name]["memory"][count]["ad"]   = ad_dic["rss_ave"]
		costs_dic[pack_name]["memory"][count]["noad"] = noad_dic["rss_ave"]
		costs_dic[pack_name]["cpu"][count]["ad"]      = ad_dic["cpu_ave"]
		costs_dic[pack_name]["cpu"][count]["noad"]    = noad_dic["cpu_ave"]
		costs_dic[pack_name]["packet"][count]["ad"]   = ad_dic["packet_num"]
		costs_dic[pack_name]["packet"][count]["noad"] = noad_dic["packet_num"]
		costs_dic[pack_name]["data"][count]["ad"]     = ad_dic["data_bytes"]
		costs_dic[pack_name]["data"][count]["noad"]   = noad_dic["data_bytes"]
		costs_dic[pack_name]["battery"][count]["ad"]  = ad_dic["battery_ave"]
		costs_dic[pack_name]["battery"][count]["noad"]= noad_dic["battery_ave"]
		print("Ad costs for %s the %dth measurement is:" % (apk, count))
		print("Memory:  %d(ad)      %d(noad)." % (ad_dic["rss_ave"], noad_dic["rss_ave"]))
		print("CPU:     %.2f(ad)      %.2f(noad)." % (ad_dic["cpu_ave"], noad_dic["cpu_ave"]))
		print("Packet:  %d(ad)      %d(noad)." % (ad_dic["packet_num"], noad_dic["packet_num"]))
		print("Data:    %d(ad)      %d(noad)." % (ad_dic["data_bytes"], noad_dic["data_bytes"]))
		print("Battery: %d(ad)      %d(noad)." % (ad_dic["battery_ave"], noad_dic["battery_ave"]))
	return costs_dic

if __name__ == "__main__":
	ad_path = sys.argv[1]
	no_ad_path = sys.argv[2]
	time_log_path = sys.argv[3]
	costs_dic = compute_cost()
	result_dir = os.path.join("..", "results")
	if not os.path.exists(result_dir):
		os.makedirs(result_dir)
	with open(os.path.join(result_dir, "cost_dict_new.json"), "w") as fw:
		json.dump(costs_dic, fw)