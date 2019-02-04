import os
import shutil

base_path = "/home/picarro/I2000/Log/Archive"
year = "1977"
dummy_file = "/var/log/syslog.1"

# Make a series of dated directories in the Archive folder.
# Put a simple text file in each directory so we have a fair
# test of the FileEraser's ability to delete directories
# that are not empty.
#
for month in xrange(1,2):
    for day in xrange(1,31):
        date_dir = "{}-{:0>2}-{:0>2}".format(year, month, day)
        rdf_dir = date_dir + "-RDF"
        full_path = os.path.join(base_path, date_dir)
        rdf_full_path = os.path.join(base_path, rdf_dir)
        os.makedirs(full_path, 0775)
        os.makedirs(rdf_full_path, 0775)
        shutil.copy(dummy_file, full_path)
        shutil.copy(dummy_file, rdf_full_path)

