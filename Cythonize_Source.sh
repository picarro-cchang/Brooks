#!/bin/bash
# Script will go to below folder list (includeFolderList vriable) to Cythonize I2000 Analyzer code

git_directory=$(pwd)
dir_source_main_python="$git_directory/src/main/python"
echo $dir_source_main_python

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

for includeFolder in "${includeFolderList[@]}"
do
  working_Path=$dir_source_main_python/$includeFolder
  # we need to Cythonize python files from all above folder ecluding init, gui, setup and simulator files
  # so lets find all intrested files and cleate list of all files
  dirs=( $(find $working_Path -maxdepth 1 -type f -name "*.py" ! -name "__init__.py" ! -name "setup.py" ! -name "EventManagerGUI.py" ! -name "GuiTools.py" ! -name "GuiWidgets.py" ! -name "ValveSequencerSimulator.py") )
  
  #Now lets go over each file and one by one Cythonize intrested files
  for file_in_dir in ${dirs[*]}
  do
    # Cythonize file in place
    # also create build folder containing all .o object files of files
    if ! python "$git_directory/bldsup/setupForCython.py" build_ext --inplace --filename=$file_in_dir
    then
      echo "Error during Cythonizing file $file_in_dir"
      exit 1
    fi
    
    # During Cythonize process below two steps executes
    # 1) A .pyx file is compiled by Cython to a .c file.
    # 2) The .c file is compiled by a C compiler to a .so file 
    # after Cythonize is done we dont need .c files as it was intermediate path 
    # So lets delete all intermediate generated files
    c_File_Location="${file_in_dir::-2}c"
    if [ -f "$c_File_Location" ]
    then
      echo "Deleting file $c_File_Location"
      rm $c_File_Location
    fi
  done
done

rm -R build