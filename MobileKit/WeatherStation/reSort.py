f1name = r"R:\crd_G2000\FCDS\1061-FCDS2003\Comparison\NewpeaksWithStrays.rank"
f2name = r"R:\crd_G2000\FCDS\1061-FCDS2003\Comparison\Newpeaks.rank"
foutname = r"R:\crd_G2000\FCDS\1061-FCDS2003\Comparison\Scrambledpeaks.rank"

f1 = open(f1name,"r")
f2 = open(f2name,"r")
fout = open(foutname,"w")

f2lines = f2.readlines()

for l in f2lines:
    fout.write(l)

    
for l in f1:
    if l not in f2lines:
        fout.write(l)
        
f1.close()
f2.close()
fout.close()        