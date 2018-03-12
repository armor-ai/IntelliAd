# Measuring app costs based on RERAN.
# -*- coding: utf-8 -*-
# __author__  = "Cuiyun Gao"
# __version__ = "2.0"
# __date__    ＝ "3/12/2018"

import os, sys, subprocess
from util import getmetadata
import time, datetime
import psutil # kill process
import logging # to record time

def getadbcmd(args=None, device=None):
	'''excluding adb and device'''
	preargs = ["adb"]
	if device:
		device = device.strip()
		if device:
			preargs += ["-s", device]
	if not args:
		return preargs
	return preargs + args

'''
====================================================================
Execute reran to run the apk.
(1) Translate the recorded events;
(2) Open the apk to the home page;
(3) Start the measurement and replay the translated events.
params:
      apk: the apk to run
      record_pa: the events we have recorded using RERAN
====================================================================
'''
def execute_reran(apk, record_pa, MIN=None, LOW=None, NEW=None, MAX=None):
	# (1)
	# check translated file exist, if "yes", then remove
	check_parm = ['shell', '[ -f /data/local/tmp/translatedEvents.txt] && echo "yes" || echo "no"']
	exist_not = subprocess.check_output(getadbcmd(check_parm, device), stderr=subprocess.STDOUT)
	exist_return = exist_not.split(b"\r\r\n")[-2].decode("utf-8")
	if exist_return == "yes":
		rm_parm = ['shell', 'rm', '/data/local/tmp/translatedEvents.txt']
		subprocess.check_call(getadbcmd(rm_parm, device))
	# start translation,	time.sleep(2)
	# translate_parm = ['java', 'Translate', record_pa, translate_pa, "-t", str(MIN) + "," + str(LOW) + "," + str(NEW) + "," + str(MAX)]
	translate_parm = ['java', 'Translate', record_pa, translate_pa]
	subprocess.check_call(translate_parm)
	push_parm = ['push', translate_pa, '/data/local/tmp/translatedEvents.txt']
	subprocess.check_call(getadbcmd(push_parm, device))
	print("\nFinish translating and pushing the recorded events.")

	# (2)
	# start the apk main activity
	print("apk is " + os.path.abspath(apk))
	metainfo = getmetadata(os.path.abspath(apk), aapt_path)
	launchable = metainfo['launchable'][0] # Take the first of launchable list, usually only one included
	activity = '{}/{}'.format(metainfo['name'], launchable['name'])
	subprocess.check_call(getadbcmd(['shell', 'am', 'start', '-a', 'android.intent.action.MAIN', '-n', activity], device))
	print("\nFinish starting the apk's main activity.")
	pid_parm = ['shell', 'ps', '|', 'grep', metainfo['name']]
	output = subprocess.check_output(getadbcmd(pid_parm, device), stderr=subprocess.STDOUT)
	pid = str(output).split()[1]
	print("\nPid is %s" % pid)
	logging.warning("\nName of metainfo is %s" % metainfo['name'])


	# (3)
	# run the replay and measurement at the same time
	# get cpu frequency with pid, this is unchanged, so we can just obtain once
	# run parms in parallel
	# get tcpdump data, including packet numbers and data length
	dump_parm = 'adb -s ' + device + ' shell su -c "tcpdump -i any -p -l -v" >> '+ dump_pa + '&'
	# get top data, including CPU and RSS per second
	top_parm = 'adb -s ' + device + ' shell "top -d 1 | grep ' + metainfo['name'] + '" >> ' + top_pa + ' &'
	# get utime/stime, rss, num_thread
	stat_parm = 'adb -s ' + device + ' shell "while :; do cat /proc/' + str(pid) + '/stat" >> ' + stat_pa + '; sleep 1; done'
	# get cpu frequency
	cpufreq_parm = 'adb -s ' + device + ' shell "while :; do cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq" >> ' + cpufreq_pa + '; sleep 1; done'
	commands = [dump_parm, top_parm, stat_parm, cpufreq_parm]
	processes = [subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True) for cmd in commands]
	start_time = time.time()
	print("\nFinish starting the measurement.")
	time.sleep(10)
	# replay the events
	replay_parm = 'adb -s' + device + ' shell /data/local/tmp/replay /data/local/tmp/translatedEvents.txt'
	replay_pro = subprocess.Popen(replay_parm, stdout=subprocess.PIPE, shell=True)
	
	# kill all the measurement when replay finished
	stdout, stderr = replay_pro.communicate()
	flag = replay_pro.returncode
	print("Returncode of process[0] is ", flag)

	for idx, pro in enumerate(processes):
		process = psutil.Process(pro.pid)
		for proc in process.children(recursive=True):
			proc.kill()
		try:
			process.kill()
		except psutil.NoSuchProcess:
			continue

	print("Finish measurement and killing all the processes.")
	logging.info("%sth measurement used %s seconds." % (count, (time.time()-start_time)))


# ========================================================
# Install apk.
# ========================================================
def install(apk_path):
	install_cmd = getadbcmd(["install", apk_path], device)
	subprocess.check_output(install_cmd, stderr=subprocess.STDOUT)

def main(apk_path):
	'''Main process for each apk
	   (1) install the apk on mobile phones;
	   (2) conduct the RERAN and start measurement automatically.'''
	install(apk_path)
	print("finish installing apk.")
	execute_reran(apk_path, record_pa)



if __name__ == "__main__":
	'''
	params:
	apk_name:  name of apk for measurement.
	device:  device_id of your mobile phones, 16-bit number
	apk_path:  path of your apk for measurement
	count:  measurement times. Usually, we take the average measurement results for analysis.
	fsave_path:  path to save the measurement results
	aapt_path: execution path of aapt.exe, under Android install path:  e.g., Android\\sdk\\build-tools\\25.0.1\\aapt.exe
	'''
	apk_name = sys.argv[1]
	device = sys.argv[2]
	apk_path = sys.argv[3]
	count = str(sys.argv[4])
	fsave_path = sys.argv[5]
	aapt_path = sys.argv[6]

	# setting of interval, low should be less than max
	# MIN = 3
	# LOW = 15  
	# NEW = 35
	# MAX = 35
	print("apk_name is ", apk_name)


	# ===============================================
	# define file paths
	# "count" is used to record the measurement times
	# ===============================================
	fsave_path = os.path.abspath(os.path.join(fsave_path, apk_name.strip(".apk")))
	if not os.path.exists(fsave_path):
		os.mkdirs(fsave_path)
	print("fsave_path is ", fsave_path)
	record_pa = os.path.join(fsave_path, "events.txt")
	translate_pa = os.path.join(fsave_path, "events_translate.txt")

	# check whether the test person files exist, and if not, create the person file

	dump_pa    = os.path.join(fsave_path, count + "_dns_log" + ".cap")
	top_pa     = os.path.join(fsave_path, count + "_top" + ".txt")
	stat_pa    = os.path.join(fsave_path, count + "_stat" + ".txt")
	cpufreq_pa = os.path.join(fsave_path, count + "_cpufreq" + ".txt")
	log_pa     = os.path.join(fsave_path, "time.log")
	logging.basicConfig(filename=log_pa,level=logging.DEBUG)

	# ===============================================
	# start executing the main function
	# ===============================================
	main(apk_path)