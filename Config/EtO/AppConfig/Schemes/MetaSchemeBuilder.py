# -*- coding: utf-8 -*-
"""
Created on Tue Aug 28 12:17:51 2018

@author: chris
"""
import numpy as np
import os

"""
sampleCodeSnippet
SchemeCount = 2
Scheme_1_Path = ../Schemes/SGDBR_sweep1.sch
Scheme_2_Path = ../Schemes/SGDBR_sweep2.sch
"""

schemeTemplate = """$$$
import copy
import numpy as np
schemeVersion = 1
repeat = 1
fsr = %.8f
laser = 0
id = %d
pztCen = 8192
fit = 32768

schemeRows = []

def makeScan(base,incr,stepAndDwell,id,vLaser,extra1=0):
    result = []
    for s,d in stepAndDwell:
        result.append(Row(base+s*incr,d,id,vLaser,extra1=extra1))
    return result

schemeRows = []

fstart = %.5f
fsr_steps = %d
subschemesteps = %d

for nss in range(subschemesteps):
    thisStart = fstart + nss*fsr_steps*fsr
    schemeRows += makeScan(thisStart, fsr, 
                           [(n, 1) for n in np.arange(fsr_steps)],
                           100, laser,extra1=id+nss)

    schemeRows[-1].subschemeId |= fit
$$$
"""

nu_center = 6057.8000  #standard CFADS water peak

#AVX80-9001 (SGDBR UU008)
nu_start0 = 5995.0
nu_end = 6179.4
fsr = 0.0206069

centerIndex = int((nu_center - nu_start0)/fsr)
nu_start = nu_center - centerIndex*fsr

Nschemes = 2
NsubSchemes = 5
Ntotal = int((nu_end - nu_start) / Nschemes / fsr) * Nschemes
NperScheme = Ntotal / Nschemes
NperSubScheme = int(NperScheme / NsubSchemes)
fn_template = 'FSRscheme_%d_%d.sch'
mode_def_snippet = 'SchemeCount = %d\n' % Nschemes
for ns in range(Nschemes):
    fstart = nu_start + ns*NperScheme*fsr
    fend = fstart + NperScheme*fsr
    spectrumID = ns*NsubSchemes
    thisScheme = schemeTemplate % (fsr, spectrumID, fstart, NperSubScheme, NsubSchemes)
    schemeName = fn_template % (fstart,fend)
    mode_def_snippet += r"Scheme_%d_Path = ../Schemes/%s" % (ns+1, schemeName) + '\n'
    #print thisScheme
    #print '- '*40
    with open(schemeName, 'w') as outScheme:
        outScheme.write(thisScheme)

print mode_def_snippet 
fsnip = r'modeCodeSnippet.txt'
with open(fsnip,'w') as snipguy:
    snipguy.write(mode_def_snippet)
    



