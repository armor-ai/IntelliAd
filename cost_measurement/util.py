# Provide the metainfo of the studied app.
# -*- coding: utf-8 -*-
# __author__  = "Cuiyun Gao"
# __version__ = "1.0"
# __date__    ＝ "3/12/2018"

import os, subprocess

def getmetadata(apk_path, aapt_path):
	'''
	params:
	apk_path:  path of apk file
	aapt_path: execution path of aapt.exe, under Android install path:  e.g., Android\\sdk\\build-tools\\25.0.1\\aapt.exe
	'''
	aaptout = subprocess.check_output(['D:\\install\\Android\\sdk\\build-tools\\25.0.1\\aapt.exe', 'd', 'badging',  apk_path])
	data = {}
	data['uses-permission'] = []
	data['uses-feature'] = []
	data['uses-library'] = []
	data['launchable'] = []
	for line in aaptout.splitlines():
		line = line.decode()
		tokens = line.split("'")
		if line.startswith('package:'):
			data['name'] = tokens[1]
			data['versionCode'] = tokens[3]
			data['versionName'] = tokens[5]
		elif line.startswith('uses-permission'):
			data['uses-permission'].append(tokens[1])
		elif line.startswith('sdkVersion'):
			data['sdkVersion'] = tokens[1]
		elif line.startswith('targetSdkVersion'):
			data['targetSdkVersion'] = tokens[1]
		elif line.startswith('uses-feature'): # both required and not required
			data['uses-feature'].append(tokens[1])
		elif line.startswith('uses-library'): # both required and not required
			data['uses-library'].append(tokens[1])
		elif line.startswith('application:'):
			data['app-label'] = tokens[1]
			data['app-icon'] = tokens[3]
		elif line.startswith('launchable activity') or line.startswith('launchable-activity'):
			data['launchable'].append(dict(name=tokens[1],label=tokens[3], icon=tokens[5]))
	return data