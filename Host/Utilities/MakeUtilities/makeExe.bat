cd ..\..\..
rem bzr version-info --python Host > .\Host\hostBzrVer.py
rem bzr version-info --python SrcCode > .\Host\srcBzrVer.py
bzr version-info --python > .\repoBzrVer.py
cd .\Host
rmdir /S /Q dist
rmdir /S /Q build
PicarroExeSetup.py py2exe
rem epydoc --html . -o ..\doc
cd Utilities\MakeUtilities
