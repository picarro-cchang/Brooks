#!/usr/bin/python

import bz2
import cPickle
import json
import pymongo
import os
import re

dirName = '/usr/local/picarro/p3SurveyorRpt/ReportGen';

logFile = os.path.join(dirName,'stage','ReportGen.log')
with open(logFile,'r') as fp:
	for x in fp:
		if x.startswith('start:'):
			startJob = json.loads(x[7:])
			print startJob['instructions_type'] 
		if x.startswith('success:'):
			pass
		if x.startswith('fail:'):
			pass
		if x.startswith('/* RESTARTING'):
			pass
		if not x.strip():
			pass
