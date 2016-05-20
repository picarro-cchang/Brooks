import glob
import os
import re
import shutil
import sys

re1 = re.compile("(import\s+((\w*)(\.\w*)*)(\s+(as\s+\w*))?)")
re2 = re.compile("(from\s+((\w*)(\.\w*)*))\s+import\s+(.*)")
def analyze_local(filename, mod_names, pkg_path):
    init = True
    dir_name = os.path.dirname(filename)
    result = []    
    with file(filename,"r") as fp:
        for ln, line in enumerate(fp):
            match1 = re1.search(line)
            match2 = re2.search(line)
            if match2:
                if match2.group(3) in mod_names:
                    if init:
                        print filename
                        init = False
                    print "  %4d: %s" % (ln+1, line.rstrip())
                    new_line = line.replace(match2.group(1), match2.group(1).replace(match2.group(2),pkg_path + "." + match2.group(2)))
                    result.append("%s" % new_line.rstrip())
                else:
                    result.append("%s" % line.rstrip())
            elif match1:
                if match1.group(3) in mod_names:
                    if init:
                        print filename
                        init = False
                    print "  %4d: %s" % (ln+1, line.rstrip())
                    if match1.group(6): # as clause present
                        new_line = line.replace(match1.group(1), match1.group(1).replace(match1.group(2),pkg_path + "." + match1.group(2)))
                    else: 
                        new_line = line.replace(match1.group(1), match1.group(1).replace(match1.group(2),pkg_path + "." + match1.group(2)) 
                                                + " as " + match1.group(2))
                    result.append("%s" % new_line.rstrip())
                else:
                    result.append("%s" % line.rstrip())
            else:
                result.append("%s" % line.rstrip())
    return "\n".join(result)

                    
                    
if __name__ == "__main__":
    for root, dirs,files in os.walk(r'src\Host'):
        py_files = glob.glob(os.path.join(root,"*.py"))
        mod_names = [os.path.split(fname)[-1][:-3] for fname in py_files]
        pkg_path = ".".join(root.split(os.path.sep)[1:])
        for name in files:
            if name.endswith('py'):
                py_file = os.path.join(root, name)                
                with file("temp.py", "w") as fp:
                    fp.write(analyze_local(py_file, mod_names, pkg_path))
                shutil.copyfile("temp.py", py_file)
