#!/bin/bash

# Parse shell script arguments.
#
# -d    Run the code with the rpdb2 debugger enabled
#
getopt --test > /dev/null
if [[ $? != 4 ]]; then
    echo "getopt not installed"
    exit 1
fi
SHORT=d::
LONG=debug
PARSED=`getopt --options d:: --longoptions $LONG --name "$0" -- "$@"`
DEBUG=false
if [[ $? != 0 ]]; then
    exit 2
fi
eval set -- "$PARSED"
while true; do
    case "$1" in
        -d|--debug)
            echo "debug mode"
            DEBUG=true
            shift
            break
            ;;
        # handle the missing or unknow opt
        *)
            echo "unknow opt"
            break
            ;;
    esac
done

# Set the version of python to use. The preference is to use
# a packaged environment like Anaconda so that you have better
# control over the package versions.
PYTHON=$HOME/anaconda2/bin/python2.7
OPT=-O

# Define the top level of the AppConfig, InstrConfig, CommonConfig
# directories for the desired analyzer type.
#CONFIGDIR=$HOME/git/host/src/main/python
CONFIGDIR=$HOME/git/host/Config/AMADS

# Top level directory for all *.py files
PYDIR=$HOME/git/host/src/main/python/Host

# In virtual analyzer mode, the Supervisor creates the rdReprocessor
# in place of the Driver.  This ini tells the Supervisor how to
# create the rdReprocessor and where to find the *.h5 ringdown files.
RDINI=$PYDIR/Utilities/VirtualAnalyzer/rdReprocessor.ini

# The Supervisor ini tells the Supervisor how to start all the other
# processes needed to reprocess the ringdown file as if this were a
# live analyzer.
SUPINI=$CONFIGDIR/AppConfig/Config/Supervisor/supervisorEXE_AMADS_LCT.ini

# Start the Supervisor in virtual analyzer mode.
# cd'ing to the Supervisor directory is needed as there are still ini
# files that have relative paths that assume the code is started in
# that directory.
cd $PYDIR/Supervisor
#$PYTHON $OPT $PYDIR/Supervisor/Supervisor.py --vi $RDINI -c $SUPINI
#rpdb2 --debugee $PYDIR/Supervisor/Supervisor.py --vi $RDINI -c $SUPINI

if [ "$DEBUG" = true ]; then
    rpdb2 --debugee $PYDIR/Supervisor/Supervisor.py --vi $RDINI -c $SUPINI
else
    $PYTHON $OPT $PYDIR/Supervisor/Supervisor.py --vi $RDINI -c $SUPINI
fi
