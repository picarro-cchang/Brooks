#!/bin/bash
# Script to make debian package

if [ $# -lt 4 ] 
then
    echo -e "Invalid argument please pass three arguments,\n  1: Build number (Like 1.0.0.0)\n  2: Installer type (Like NDDS)\n  3: Git hash number\n  4: Project name (Like I2000)"
    exit 1
fi

raw_version=$1
installer_type=$2
git_hash=$3
project_name=$4
include_config=${5:-true}
include_installer_signature=${6:-true}
git_directory=$(pwd)
git_directory="$(dirname $git_directory)"
version_file_path=$git_directory/buildTools/versions/${project_name,,}_types.json
dir_source_main_python="$git_directory/src/main/python"
dist_foldername=${project_name}_${raw_version}
dist_directory="$git_directory/target/dist/${dist_foldername}"
config_directory="$git_directory/Config"
git_common_config_directory="$config_directory/CommonConfig"
debian_directory="$dist_directory/DEBIAN"
resource_directory="$git_directory/target/Installers/${dist_foldername}"
git_instr_config_directory="$config_directory/$installer_type/InstrConfig"
git_app_config_directory="$config_directory/$installer_type/AppConfig"
git_signature_file="$config_directory/$installer_type/installerSignature.txt"
git_bin_config_directory="$config_directory/$installer_type/bin"

dist_dir_home="$dist_directory/home"
dist_dir_new="$dist_directory/home/picarro/${project_name}"
dist_instr_config_directory="$dist_dir_new/InstrConfig"
dist_common_config_directory="$dist_dir_new/CommonConfig"
dist_app_config_directory="$dist_dir_new/AppConfig"
dist_bin_config_directory="$dist_directory/home/picarro/bin"

pth_file_dir="$dist_dir_home/picarro/anaconda2/lib/python2.7/site-packages"

# dpkg does not allow '_', '+' or '.' as part of package name of control file
# so lets replace all of them with '-' for project type like SADS_PFV, SADS_DCRDS
# AMADS_PFV and AMADS_DCRDS
installer_type_without_underscore=${installer_type//[_+.]/-}

#lets read species information from version/*_types.json file
species=( $(cat $version_file_path | python -c 'import json,sys;obj=json.load(sys.stdin);print obj["buildTypes"]["'$installer_type'"]["species"];') )
if [ $? != 0 ]
then
  echo -e "\n*****************Error while readying $version_file_path file ***********************************"
  exit 1
fi

# lets start clean installer by deleting any old directory and files if present
if [ -d "$dist_dir_home" ]
then
  rm -R $dist_dir_home
fi

# create the desired directory tree: home/picarro/I2000
dist_directory_temp="${dist_directory}_temp"
if ! mv $dist_directory $dist_directory_temp
then
  echo -e "\n***********Error during moving directory $dist_directory to $dist_directory_temp******************"
  exit 1
fi

if ! mkdir -p "$dist_directory/home/picarro"
then
  echo -e "\n***********Error during creating directory "$dist_directory/home/picarro"*************************"
  exit 1
fi

if ! mv $dist_directory_temp $dist_dir_new
then
  echo -e "\n***********Error during moving directory $dist_directory_temp to $dist_dir_new********************"
  exit 1
fi


# copy commonconfig
if [ $include_config == "true" ]
  then
    if [ -d "$dist_common_config_directory" ]
      then
      rm -rf $dist_common_config_directory
  fi

  if ! cp -R "$git_common_config_directory/." $dist_common_config_directory
    then
      echo -e "\n****Error during copying files from $git_common_config_directory to $dist_common_config_directory*"
      exit 1
  fi
fi

# create python path file
#mkdir -p $pth_file_dir

#printf '/home/picarro/I2000' >> "$pth_file_dir/Picarro.pth"

if [ ! -d "$debian_directory" ]
then
  mkdir -p $debian_directory
fi

cp "$git_directory/buildTools/preinst" $debian_directory
cp "$git_directory/buildTools/postinst" $debian_directory
chmod 755 "$debian_directory/preinst"
chmod 755 "$debian_directory/postinst"

# make installer directory
if [ ! -d "$resource_directory" ]
then
  mkdir -p $resource_directory
fi

# copy config files
if [ $include_config == "true" ]
then
  if [ -d "$dist_instr_config_directory" ]
  then
    rm -rf $dist_instr_config_directory
  fi

  cp -R "$git_instr_config_directory/." $dist_instr_config_directory

  if [ -d "$dist_app_config_directory" ]
  then
    rm -rf $dist_app_config_directory
  fi

  cp -R "$git_app_config_directory/." $dist_app_config_directory

  if [ -d "$dist_bin_config_directory" ]
  then
    rm -rf $dist_bin_config_directory
  fi
fi

if [ $include_installer_signature == "true" ]
then
  cp $git_signature_file $dist_dir_new
  cp -R "$git_bin_config_directory/." $dist_bin_config_directory
  chmod -R 755 $dist_bin_config_directory
fi

# make control file
cat <<EOM > "$debian_directory/control"
Package: $project_name-$installer_type_without_underscore
Version: $raw_version
Section: science
Priority: required
Architecture: amd64
Depends: 
Maintainer: Picarro instrument software team
Description: Picarro Host Software for Semiconductor Industry 
 $installer_type Analyzer
 Version: $raw_version
EOM

echo $dist_directory
if ! dpkg-deb --build $dist_directory
then
  echo -e "\n***********************Error during creating debian package******************"
  exit 1
fi

# move package to installer folder
mv "$dist_directory.deb" "$resource_directory/${project_name}_${installer_type}_${species}_${raw_version}_${git_hash}.deb"


