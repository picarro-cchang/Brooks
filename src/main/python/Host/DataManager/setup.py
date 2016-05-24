from distutils.core import setup
import os
import py2exe
import zmq

os.environ["PATH"] = os.environ["PATH"] + os.path.pathsep + \
    os.path.split(zmq.__file__)[0]

exclusionList = []
inclusionList = ["zmq.core.*", "zmq.utils", "zmq.utils.jsonapi", "zmq.utils.strtypes"]
packageList = []
data_files = []
setup(console=['DataManagerToZmq.py', 'ListenToZmq.py'],
      options=dict(py2exe=dict(compressed=1,
                               optimize=1,
                   bundle_files=1,
                   excludes=exclusionList,
                   includes=inclusionList,
                   packages=packageList)),
      data_files=data_files,
      )