"""
This module contains little utilities that handle OS specific tasks.
The idea is that code can call these utilities through a OS
agnostic API and the utility figures out the right thing to do
based upon its environment.
"""

import os, sys
import re

def fixpath(path, operatingsystem = sys.platform):
	"""
	fixpath
	Convert a Windows or Linux path to a format compatible
	with the current OS.

	Input:
	path (string) - A relative or absolute posix or Windows path
	operatingsystem (string) - The current host operating system.
	"win32" or "linux2". If not set in the argument, a system call
	is used to determine the OS at run time.

	Output:
	string - The modified path.

	Notes:
	05SEP2016 - Probably not the best solution as I'm new to Python.
	""" 

	# Make Windows style paths posix compliant.
	# If the path starts with C: assume we want the root
	# file system. If it's any other mapped drive, you'll
	# have to hand edit the input path since we can't
	# know where the mount point is.
	#
	if operatingsystem == "linux2":
		path = re.sub(r"(\\)+",'/', path)
		if path.startswith("C:"):
			path = path[2:]

	
	# Make posix path work on Windows.  If the path doesn't
	# start with ~ or .. we assume an absolute path on C:
	#
	if operatingsystem == "win32":
		path = path.replace('/','\\')
		if path.startswith("\\"):
			path = "C:" + path

	return path


def __path_test():

	# Relative paths test
	windowspath = r"..\dir\subdir\subsubdir"
	unixpath = "../dir/subdir/subsubdir"

	newpath = fixpath(unixpath, operatingsystem = 'win32')
	print("Unix in:", unixpath, "Windows out:", newpath)

	newpath = fixpath(windowspath, operatingsystem = 'linux2')
	print("Windows in:", windowspath, "Unix out:", newpath)

	# Absolute path test
	windowspath = r"C:\root\dir\subdir\subsubdir"
	unixpath = "/root/dir/subdir/subsubdir"

	newpath = fixpath(unixpath, operatingsystem = 'win32')
	print("Unix in:", unixpath, "Windows out:", newpath)

	newpath = fixpath(windowspath, operatingsystem = 'linux2')
	print("Windows in:", windowspath, "Unix out:", newpath)

	return


if __name__ == '__main__':
	__path_test()
