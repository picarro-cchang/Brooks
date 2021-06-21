#!/bin/bash
#
#
include_config=${1:-true}
include_installer_signature${2:-true}
git_hash=`git rev-parse HEAD`
git_hash_short=${git_hash:0:8}
# Build the Debian package locally using the same
# steps run by the TeamCity build agent.
#
#cd /home/picarro/git/host
./Prepare_Build.sh 1.3.999.920 GENERIC $git_hash_short I2000
./Compile_Dependency.sh
./Cythonize_Source.sh
./Copy_Source.sh 1.3.999.920 I2000
./Make_Installer.sh 1.3.999.920 GENERIC $git_hash_short I2000 $include_config $include_installer_signature

# Install the package locally and run it to make
# sure all the necessary files are in place and
# the paths in the ini files need to start are
# set right.
#sudo dpkg -i target/Installers/I2000_1.2.3.5/I2000_NDDS_H2O2_1.2.3.5_abcd1234.deb
#cd /home/picarro/bin
#./launchBinSimulation.sh

