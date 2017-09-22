#!/bin/bash
# Script to compile and generate Analyzer code for DSP, FPGA, FitUtils, DatVeiwer and FastLomb

git_directory=$(pwd)
dir_source_main_python="$git_directory/src/main/python"

#Compile source for XML
echo -e "\n***********************Compiling Source For XML******************"
firmware_XML_path="$dir_source_main_python/Firmware/xml"
echo "Running: cd $firmware_XML_path"
cd $firmware_XML_path
echo "Running: python xmldom1.py"
if python xmldom1.py
then
  echo "******************Compiling Source For XML Done*********************"
else
  echo "*****************Compiling Source For XML failed********************"
  exit 1
fi


#Compile FitUtils
echo -e "\n************************Compiling FitUtils***********************"
fitter_path="$dir_source_main_python/Host/Fitter"
echo "Running: cd $fitter_path"
cd $fitter_path
if [ -f fitutils.so ]; then rm fitutils.so; fi
echo "Running: f2py -c -m fitutils fitutils.f"
if f2py -c -m fitutils fitutils.f
then
  echo "***********************FitUtils Compilation Successful**************"
else
  echo "******************FitUtils Compilation Error. Stopping build********"
  exit 1
fi

#Compile Cluster Analyzer
echo -e "\n************************Compiling Cluster Analyzer***************"
echo "Running: cd $fitter_path"
cd $fitter_path
if [ -f cluster_analyzer.so ]; then rm cluster_analyzer.so; fi
echo "Running: python setup.py build_src build_ext --inplace"
if python setup.py build_src build_ext --inplace
then
  echo "***********************Cluster Analyzer Compilation Successful******"
else
  echo "************Cluster Analyzer Compilation Error. Stopping build******"
  exit 1
fi
echo "Running: rm cluster_analyzermodule.c"
rm cluster_analyzermodule.c
echo "Running: -rf build"
rm -rf build

#Compile FastLomb
echo -e "\n************************Compiling FastLomb***********************"
SuperBuildStation_path="$dir_source_main_python/Host/Utilities/SuperBuildStation"
echo "Running: cd $SuperBuildStation_path"
cd $SuperBuildStation_path
if [ -f fastLomb.so ]; then rm fastLomb.so; fi
echo "Running: python setup.py build_src build_ext --inplace"
if python setup.py build_src build_ext --inplace
then
  echo "***********************FastLomb Compilation Successful**************"
else
  echo "************FastLomb Compilation Error. Stopping build**************"
  exit 1
fi
echo "Running: rm fastLombmodule.c"
rm fastLombmodule.c
echo "Running: rm -rf build"
rm -rf build

#Compile DatViewer
echo -e "\n************************Compiling DatVeiwer***********************"
DatViwer_path="$dir_source_main_python/AddOns/DatViewer"
echo "Running: cd $DatViwer_path"
cd $DatViwer_path
echo "Running: python -m py_compile DatViewer.py DateRangeSelectorFrame.py Analysis.py FileOperations.py timestamp.py CustomConfigObj.py"
if python -m py_compile DatViewer.py DateRangeSelectorFrame.py Analysis.py FileOperations.py timestamp.py CustomConfigObj.py
then
  echo "***********************DatVeiwer Compilation Successful**************"
else
  echo "************DatVeiwer Compilation Error. Stopping build**************"
  exit 1
fi