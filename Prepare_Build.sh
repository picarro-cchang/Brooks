#!/bin/bash
# Script use to prepare for build
# 1. Script will create version file so app can read it and show app version

if [ $# -lt 2 ] 
then
    echo -e "Invalid argument please pass atleast two arguments, third argument is optional.\n  1: build number (Like 1.0.0.0)\n  2: Git hash number\n  3: 1 if Internal build (Optional)"
    exit 1
fi

raw_version=$1
git_hash=$2
internal_build=${3:-0}

export PATH=/home/picarro/anaconda2/bin:$PATH
export PYTHONPATH=/home/picarro/git/host/src/main/python:$PYTHONPATH

git_directory=$(pwd)
project_name="I2000"


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

