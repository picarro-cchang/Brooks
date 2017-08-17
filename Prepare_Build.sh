#!/bin/bash
# Script use to prepare for build
# 1. Script will create version file so app can read it and show app version

if [ $# -lt 2 ] 
then
    echo -e "Invalid argument please pass atleast three arguments, forth argument is optional.\n  1: build number (Like 1.0.0.0)\n  2: installer type (Like NDDS)\n  3: Git hash number\n  4: 1 if Internal build (Optional)"
    exit 1
fi

raw_version=$1
installer_type=$2
git_hash=$3
internal_build=${4:-0}

export PATH=/home/picarro/anaconda2/bin:$PATH
export PYTHONPATH=/home/picarro/git/host/src/main/python:$PYTHONPATH

git_directory=$(pwd)
build_helper_file_path=$git_directory/src/main/python/Host/Utilities/BuildHelper/BuildInfo.py
project_name="i2000"
dist_foldername=${project_name}_${raw_version}
dist_directory="$git_directory/target/dist/${dist_foldername}"

if [ $internal_build == 1 ]
then
  version_file_path=$git_directory/src/main/python/Host/build_version.py
  build_type='INTERNAL'
else
  version_file_path=$git_directory/src/main/python/Host/Common/release_version.py
  build_type=''
fi

# make version file
cat <<EOM > "$version_file_path"
 # autogenerated by PyBuilder

def versionString():
    return 'i2000-${raw_version} (${git_hash})'

def versionNumString():
    return '$raw_version'

def buildType():
    # Empty string indicates official release
    return '$build_type'
EOM

current_time=$(date +%s.%6N)
# create build helper file
cat <<EOM > "$build_helper_file_path"
# Auto generated by PyBuilder
buildTime = $current_time
buildTypes = ['$installer_type']
buildFolder = '$dist_directory'
EOM


