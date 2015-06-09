from Host.autogen import interface
from tables import openFile

def genRingdownEntries(rdFileName):
    h5 = openFile(rdFileName,"r")
    rdTable = h5.root.rdData
    names = rdTable.colnames
    entries = []
    for i,r in enumerate(rdTable.iterrows()):
        entry = interface.RingdownEntryType()
        for name,ctype in entry._fields_:
            if name in names:
                try:
                    setattr(entry,name,r[name])
                except:
                    setattr(entry,name,int(r[name]))
        entries.append(entry)
    return entries