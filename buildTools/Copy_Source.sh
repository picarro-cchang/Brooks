#!/bin/bash
# Script to Copy all required files to target directory for debian package

if [ $# -lt 2 ] 
then
    echo -e "Invalid argument please pass three arguments,\n  1: Build number (Like 1.0.0.0)\n  2: Project name (Like I2000)\n"
    exit 1
fi

raw_version=$1
project_name=$2
dist_foldername=${project_name}_${raw_version}
git_directory=$(pwd)
git_directory="$(dirname $git_directory)"
dir_source_main_python="$git_directory/src/main/python"
target_directory="$git_directory/target/dist/${dist_foldername}"

# lets start with fresh copy by deleting old files and folder if present
if [ -d "$target_directory" ]
then
  rm -rf $target_directory
fi

if ! mkdir -p $target_directory 
  then
  echo "******************Can not able to create directory $target_directory*********************"
  exit 1
fi


includeFolderList[0]="Host/AlarmSystem"
includeFolderList[1]="Host/Archiver"
includeFolderList[2]="Host/Common"
includeFolderList[3]="Host/CommandInterface"
includeFolderList[4]="Host/DataLogger"
includeFolderList[5]="Host/DataManager"
includeFolderList[6]="Host/Driver"
includeFolderList[7]="Host/ElectricalInterface"
includeFolderList[8]="Host/EventManager"
includeFolderList[9]="Host/Fitter"
includeFolderList[10]="Host/InstMgr"
includeFolderList[11]="Host/MeasSystem"
includeFolderList[12]="Host/RDFrequencyConverter"
includeFolderList[13]="Host/rdReprocessor"
includeFolderList[14]="Host/PeriphIntrf"
includeFolderList[15]="Host/SampleManager"
includeFolderList[16]="Host/SpectrumCollector"
includeFolderList[17]="Host/Supervisor"
includeFolderList[18]="Host/ValveSequencer"
includeFolderList[19]="Host/FileEraser"

source_list=()
# Lets get all .so files generated dring cythonization, init, setup and gui
for includeFolder in "${includeFolderList[@]}"
do
  working_Path=$dir_source_main_python/$includeFolder
  dirs=( $(find $working_Path -maxdepth 1 -type f -name "*.py") )
  for file_in_dir in ${dirs[*]}
  do
    if [[ $file_in_dir =~ "__init__.py" ]] || [[ $file_in_dir =~ "setup.py" ]] || [[ $file_in_dir =~ "EventManagerGUI.py" ]] || [[ $file_in_dir =~ "GuiTools.py" ]] || [[ $file_in_dir =~ "GuiWidgets.py" ]] || [[ $file_in_dir =~ "ValveSequencerSimulator.py" ]] || [[ $file_in_dir =~ "SupervisorTests.py" ]] 
    then
      source_list+=($file_in_dir)
    else
      source_list+=("${file_in_dir::-2}so")
    fi
  done
done

# We also need dsp, usb, fitter utils and FPGA compiled code
# lets get all compiled files for the same
includeFileList=("Host/__init__.py" "Host/Utilities/__init__.py" "Firmware/CypressUSB/analyzer/analyzerUsb.hex" "Firmware/DSP/src/Debug/dspMain.hex" "Firmware/MyHDL/Spartan3/top_io_map.bit" "Firmware/Lattice/sgdbr_bitmap_90060B.bin" "Host/Fitter/fitutils.so" "Host/Fitter/cluster_analyzer.so")
for file_in_dir in ${includeFileList[*]}
do
  source_list+=($dir_source_main_python/$file_in_dir)
done

# We need some more files which are not compiled
# lets go one by one each folder and get all required file paths
nonCythonizeIncludeIconFolderList[0]="Assets/icons/*.ico"
nonCythonizeIncludeIconFolderList[1]="Host/autogen/*.py"
nonCythonizeIncludeIconFolderList[2]="Host/DriverSimulator/*.py"
nonCythonizeIncludeIconFolderList[3]="Host/Controller/*.py"
nonCythonizeIncludeIconFolderList[4]="Host/Coordinator/*.py"
nonCythonizeIncludeIconFolderList[5]="Host/MfgUtilities/*.py"
nonCythonizeIncludeIconFolderList[6]="Host/pydCaller/*.*"
nonCythonizeIncludeIconFolderList[7]="Host/QuickGui/*.*"
nonCythonizeIncludeIconFolderList[8]="Host/WebServer/*.*"
nonCythonizeIncludeIconFolderList[9]="Host/Utilities/BuildHelper/*.py"
nonCythonizeIncludeIconFolderList[10]="Host/Utilities/ConfigManager/*.py"
nonCythonizeIncludeIconFolderList[11]="Host/Utilities/CoordinatorLauncher/*.py"
nonCythonizeIncludeIconFolderList[12]="Host/Utilities/DataRecal/*.py"
nonCythonizeIncludeIconFolderList[13]="Host/Utilities/FlowController/*.py"
nonCythonizeIncludeIconFolderList[14]="Host/Utilities/H2O2ValidationWizard/*.*"
nonCythonizeIncludeIconFolderList[15]="Host/Utilities/InstrEEPROMAccess/*.py"
nonCythonizeIncludeIconFolderList[16]="Host/Utilities/IntegrationTool/*.py"
nonCythonizeIncludeIconFolderList[17]="Host/Utilities/ModbusServer/*.py"
nonCythonizeIncludeIconFolderList[18]="Host/Utilities/RestartSupervisor/*.py"
nonCythonizeIncludeIconFolderList[19]="Host/Utilities/SetupTool/*.py"
nonCythonizeIncludeIconFolderList[20]="Host/Utilities/SupervisorLauncher/*.py"
nonCythonizeIncludeIconFolderList[21]="Host/Utilities/Four220/*.*"
nonCythonizeIncludeIconFolderList[22]="Host/Utilities/UserAdmin/*.*"
nonCythonizeIncludeIconFolderList[23]="AddOns/DatViewer/*.py"
nonCythonizeIncludeIconFolderList[24]="AddOns/DatViewer/Scripts/*.py"
nonCythonizeIncludeIconFolderList[25]="AddOns/DatViewer/tzlocal/*.py"
nonCythonizeIncludeIconFolderList[26]="AddOns/DatViewer/Manual/*.*"
nonCythonizeIncludeIconFolderList[27]="AddOns/DatViewer/Manual/_images/*.*"
nonCythonizeIncludeIconFolderList[28]="AddOns/DatViewer/Manual/_sources/*.*"
nonCythonizeIncludeIconFolderList[29]="AddOns/DatViewer/Manual/_static/*.*"
nonCythonizeIncludeIconFolderList[30]="Host/CalibrationValidationManager/*.py"
nonCythonizeIncludeIconFolderList[31]="Host/Utilities/SelfCalibration/*.*"
nonCythonizeIncludeIconFolderList[32]="Host/Utilities/FieldLaserCal/*.*"
#Take cares of file name with spaces
IFS=$'\n'  

for includeFolder in "${nonCythonizeIncludeIconFolderList[@]}"
do
  working_Path=$dir_source_main_python/$includeFolder
  dirs=( $(find $working_Path) )
  for file_in_dir in ${dirs[*]}
  do
    source_list+=($file_in_dir)
 done
done

# now we have all required file information, lets start copying one by one all files to target directory with folder structure
for file_in_list in ${source_list[*]}
do
    relative_path=( $(python -c "import os.path; print os.path.relpath('$file_in_list','$dir_source_main_python')") )
    dist_file_path=$target_directory/$relative_path
    dist_file_folder_path=( $(python -c "import os.path; print os.path.dirname('$dist_file_path')") )
    if [ ! -d "$dist_file_folder_path" ]
    then
      if ! mkdir -p $dist_file_folder_path 
        then
        echo "******************Can not able to create directory $dist_file_folder_path*********************"
        exit 1
      fi
    fi
    if ! cp -v $file_in_list $dist_file_folder_path 
    then
      echo "******************Can not copy file $file_in_list to $dist_file_folder_path*********************"
      exit 1
    fi
done
IFS="$OIFS"
