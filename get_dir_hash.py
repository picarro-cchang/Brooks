from hashlib import sha1
import os
import sys
from configobj import ConfigObj

def get_dir_hash(root):
    s = sha1()
    ini = None
    hash_ok = False
    for path, dirs, files in os.walk(root):
        dirs.sort()
        for f in files:
            fname = os.path.join(path, f)
            relname = fname[len(root)+1:]
            if relname.lower() == "version.ini":
                ini = ConfigObj(fname)
                continue
            s.update(relname)
            with open(fname,"rb") as f1:
                while True:
                    # Read file in as little chunks
                    buf = f1.read(4096)
                    if not buf : break
                    s.update(buf)
    result = s.hexdigest()
    if ini:
        if 'Version' in ini and 'dir_hash' in ini['Version']:
            hash_ok =  (ini['Version']['dir_hash'] == result)
    return result, hash_ok

if __name__ == "__main__":
    dir_hash, hash_ok = get_dir_hash(sys.argv[1])
    if hash_ok:
        print "Directory hash verified."
    else:
        print "Directory hash not found or invalid."
        print "Computed value: %s" % dir_hash
    
