ZMQ for Python 2.5

8/12/2013: Tracy W. notes (from consultation with Sze)

ZMQ isn't supported for Python 2.5. Even though I found references on the internet that zmq 2.1.11 was
the last version that supported Python 2.5, I couldn't find any installers for it.

Files in this folder are the workaround Sze created for this problem. Install them somewhere that Python 2.5 can
find them, but DO NOT install them in the HostExe folder (because library.zip will clobber the existing library.zip).

How to re-create them:

1. Need to be running on a Python 2.7 system, with zmq installed
2. cd to Host\DataManager source folder
3. python setup.py py2exe
4. This builds standalone apps that can intercept and pass zmq messages. The files to distribute are in the
   DataManager\dist folder that is created.


I also archived these files in this network folder so we don't have to re-create them from scratch:

   S:\CRDS\CRD Engineering\Software\Python25\zmqForPython2.5

           