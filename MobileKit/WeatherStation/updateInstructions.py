# Updates signed instruction files

from glob import glob
import hashlib
try:
    import json
except:
    import simplejson as json

def unix_line_endings(str):
    return str.replace('\r\n', '\n').replace('\r', '\n')

if __name__ == "__main__":
    for name in glob("instructions*.json"):
        fp = file(name,"rb")
        try:
            instr = json.loads("\n".join(fp.readlines()[1:]))
            for r in instr["regions"]:
                r["name"] = r["plat"]
                del r["plat"]
            content = json.dumps(instr,indent=2,sort_keys=True)
            content = unix_line_endings(content)
            # Prepend a secure hash to the content
            secHash = hashlib.md5('Picarro Surveyor' + content).hexdigest()
            fp.close()
            fp = file(name,"wb")
            fp.write('// ' + secHash + '\n' + content)
        except:
            print "%s is not a valid instructions file" % name
        fp.close()
        print name
