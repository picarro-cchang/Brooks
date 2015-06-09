import glob
import os
import re
import shutil
import sys

re3 = re.compile("(\s*import\s+)((\w*)(\s*,\s*(\w*))+)")
def analyze_multi(filename, mod_names, pkg_path):
    init = True
    dir_name = os.path.dirname(filename)
    result = []
    with file(filename,"r") as fp:
        for ln, line in enumerate(fp):
            match3 = re3.match(line)
            if match3:
                if init:
                    print filename
                    init = False
                print "  %4d: %s" % (ln+1, line.rstrip())
                for mod in match3.group(2).split(','):
                    print "  %4d: %s%s" % (ln+1, match3.group(1), mod.strip())
                    result.append("%s%s" % (match3.group(1), mod.strip()))
            else:
                result.append("%s" % line.rstrip())
    return "\n".join(result)
    
if __name__ == "__main__":
    for root, dirs,files in os.walk(r'src\Host'):
        py_files = glob.glob(os.path.join(root,"*.py"))
        mod_names = [os.path.split(fname)[-1][:-3] for fname in py_files]
        pkg_path = ".".join(root.split(os.path.sep)[:])
        for name in files:
            if name.endswith('py'):
                py_file = os.path.join(root, name)
                with file("temp.py", "w") as fp:
                    fp.write(analyze_multi(py_file, mod_names, pkg_path))
                shutil.copyfile("temp.py", py_file)