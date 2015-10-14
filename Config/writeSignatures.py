import os

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

if __name__ == "__main__":
    for subdir in get_immediate_subdirectories('.'):
        fname = os.path.join(subdir, "installerSignature.txt")
        with open(fname,"w") as fp:
            fp.write("%s" % subdir)

    