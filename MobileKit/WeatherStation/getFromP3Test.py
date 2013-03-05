import getFromP3 as gp3
import Host.Common.SurveyorInstStatus as sis

def mostCommon(iterable):
    hist = {}
    for c in iterable:
        if c not in hist: hist[c] = 0
        hist[c] += 1
    sc = [(hist[c],c) for c in iterable]
    sc.sort()
    return sc[-1][1] if sc else None

def getStabClass(alog):
    p3 = gp3.P3_Accessor_ByPos(alog)
    gen = p3.genAnzLog("dat")(startPos=0,endPos=100)
    weatherCodes = [(int(d.data["INST_STATUS"])>>sis.INSTMGR_AUX_STATUS_SHIFT) & sis.INSTMGR_AUX_STATUS_WEATHER_MASK for d in gen]
    stabClasses = [sis.classByWeather.get(c-1,"None") for c in weatherCodes]
    return mostCommon(stabClasses)
    
def testMostCommon():
    from random import randrange
    charList = [chr(ord('A')+i) for i in range(26)]
    tokens = []
    lmax = 30
    # Generate a string with random frequencies of distinct random letters
    l = 0
    while l<lmax:
        l = randrange(l+1,lmax+1)
        j = randrange(len(charList))
        tokens.append((l,charList[j]))
        del charList[j]
    chars = []
    for f,c in tokens: 
        for i in range(f):
            chars.append(c)
    # Shuffle elements
    lc = len(chars)
    for i in range(lc-1):
        j = randrange(i+1,lc)
        chars[i],chars[j] = chars[j],chars[i]
    # Check that mostCommon finds the most common letter synthesized
    assert mostCommon("".join(chars)) == tokens[-1][1]
    
if __name__ == "__main__":
    #for i in range(1000):
    #    testMostCommon()
    #    if i%100 == 0: print i
    alog = 'FCDS2010-20120703-043357Z-DataLog_User_Minimal.dat'
    print getStabClass(alog)
