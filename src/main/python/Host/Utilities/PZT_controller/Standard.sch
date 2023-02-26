$$$
import copy
import numpy as np
import itertools as IT
schemeVersion = 1
repeat = 2
cfg = getConfig('../../InstrConfig/Calibration/InstrCal/HotBoxCal.ini')
cfgWB = getConfig('../../InstrConfig/Calibration/InstrCal/WarmBoxCal.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
cfgLaser = getConfig('../../InstrConfig/Calibration/InstrCal/LaserRange.ini')
fsr = float(cfg['AUTOCAL']['CAVITY_FSR'])
NNlow = float(cfgLaser['NN']['LOW'])
NNhigh = float(cfgLaser['NN']['HIGH'])
UUlow = float(cfgLaser['UU']['LOW'])
UUhigh = float(cfgLaser['UU']['HIGH'])
BIG3TH = float(cfg['AUTOCAL']['BIG3TH'])
VOCTH = float(cfg['AUTOCAL']['VOCTH'])
threshold = VOCTH

VOC = 100
H2O_6099 = 213
HDO_6131 = 214
H2O_5962 = 211
H2O_5852 = 511
H2O_5863 = 215
H2O_5864 = 216
H2O_5910 = 217

pztCen = 8192
fit = 32768
ignore = 16384
f24 = 6056.504
ffile = open("/home/picarro/I2000/InstrConfig/Calibration/InstrCal/SelectedFrequencies_Standard.txt","r")

vlaserDict = {}
vlaserDict['vLaser_N'] = (NNlow, NNhigh, 2)
vlaserDict['vLaser_U'] = (UUlow, UUhigh, 0)

def get_vlaser(nu):
    this_vlaser = None
    for name, info in vlaserDict.items():
        if (nu >= info[0]) and (nu < info[1]):
            return info[2]
    return info[2] #defaults to the last laser in the list if neither range is satisfied

def two_laser_row(nu, dwell, id, _vlaser, threshold = 0, extra1=0):
    #ignore _vlaser
    return Row(nu, dwell, id, get_vlaser(nu), threshold = threshold, extra1=extra1, modeIndex=int(nu/fsr) & 0xFFFF)

def make_little_subscheme(fcenter, Nrange, Npeak, Nside, SID, threshold = threshold, ignore_on_first=False, fit_flag_at_end=True, reverse=True, extra1=0):
    Nrange_left, Nrange_right = Nrange
    offsets = list(range(-Nrange_left,Nrange_right+1,1))
    dwells = []
    for off in offsets:
        if off == 0:
            this_dwell = Npeak
        elif off in [-1,1]:
            this_dwell = Nside
        elif off in [-Nrange_left,Nrange_right]:
            this_dwell = int(round(Npeak/2))
        else:
            this_dwell = 1
        dwells.append(this_dwell)
    offsets, dwells
    if reverse:
        offsets += offsets[::-1]
        dwells += dwells[::-1]
    mode_center = int(round((fcenter - f24) / fsr))
    subscheme_row_list = []
    for j, (offset, dwell) in enumerate(zip(offsets, dwells)):
        this_mode = mode_center + offset
        #print(this_mode)
        if j == 0 and ignore_on_first:
            subscheme_row_list.append(two_laser_row(f24 + this_mode * fsr, 2, SID | ignore, 0, threshold = threshold, extra1=extra1))
            subscheme_row_list.append(two_laser_row(f24 + this_mode * fsr, dwell, SID, 0, threshold = threshold, extra1=extra1))
        elif (j == len(offsets) - 1 )and fit_flag_at_end:
            subscheme_row_list.append(two_laser_row(f24 + this_mode * fsr, dwell, SID, 0, threshold = threshold, extra1=extra1))
            subscheme_row_list.append(two_laser_row(f24 + this_mode * fsr, 1, SID | fit, 0, threshold = threshold, extra1=extra1))
        else:
            subscheme_row_list.append(two_laser_row(f24 + this_mode * fsr, dwell, SID, 0, threshold = threshold, extra1=extra1))
    return subscheme_row_list

def make_NH3(SID, threshold = threshold):
    fNH3 = 6075.61161    
    subscheme_row_list = []
    mode_center = int(round((fNH3 - f24) / fsr))
    if (f24 + mode_center * fsr) < fNH3:
        print('if')        
        subscheme_row_list.append(two_laser_row(f24 + (mode_center - 3) * fsr, 10, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center - 2) * fsr, 1, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center - 1) * fsr, 1, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center) * fsr, 10, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center + 1) * fsr, 10, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center + 2) * fsr, 1, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center + 3) * fsr, 1, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center + 4) * fsr, 10, SID, 0, threshold = threshold, extra1=17))
    else:
        print('else')        
        subscheme_row_list.append(two_laser_row(f24 + (mode_center - 4) * fsr, 10, SID, 0, threshold = threshold, extra1=17))        
        subscheme_row_list.append(two_laser_row(f24 + (mode_center - 3) * fsr, 1, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center - 2) * fsr, 1, SID, 0, threshold = threshold,extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center - 1) * fsr, 10, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center) * fsr, 10, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center + 1) * fsr, 1, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center + 2) * fsr, 1, SID, 0, threshold = threshold, extra1=17))
        subscheme_row_list.append(two_laser_row(f24 + (mode_center + 3) * fsr, 10, SID, 0, threshold = threshold, extra1=17))
    return subscheme_row_list				  

flist = [6056.50600, 6057.09, 6057.792, 5962.03, 6099.297, 5852.716, 6131.7855, 5863.88, 5863.92, 5910.21986] 

CH4_forward = make_little_subscheme(flist[1], (8,8), 7, 2, VOC, threshold = BIG3TH, ignore_on_first=False, fit_flag_at_end=False, reverse=False, extra1=25)
CO2_forward = make_little_subscheme(flist[0], (5,5), 7, 2, VOC, threshold = BIG3TH, ignore_on_first=False, fit_flag_at_end=False, reverse=False, extra1=12)
H2O_forward = make_little_subscheme(flist[2], (5,5), 7, 2, VOC, threshold = BIG3TH, ignore_on_first=False, fit_flag_at_end=False, reverse=False, extra1=11)
NH3_forward = make_NH3(VOC, threshold = VOCTH)


H2O_6099_Rows = make_little_subscheme(flist[4], (5,5), 7, 2, H2O_6099, threshold = BIG3TH, ignore_on_first=True, fit_flag_at_end=True, reverse=True, extra1=H2O_6099)
H2O_5962_Rows = make_little_subscheme(flist[3], (5,5), 7, 2, H2O_5962, threshold = BIG3TH, ignore_on_first=True, fit_flag_at_end=True, reverse=True, extra1=H2O_5962)
HDO_6131_Rows  = make_little_subscheme(flist[6], (5,3), 7, 2, HDO_6131, threshold = VOCTH, ignore_on_first=True, fit_flag_at_end=True, reverse=True, extra1=HDO_6131)
H2O_5863_Rows  = make_little_subscheme(flist[7], (5,5), 7, 2, H2O_5863, threshold = BIG3TH, ignore_on_first=True, fit_flag_at_end=True, reverse=True, extra1=H2O_5863)
H2O_5864_Rows  = make_little_subscheme(flist[8], (5,5), 7, 2, H2O_5864, threshold = BIG3TH, ignore_on_first=True, fit_flag_at_end=True, reverse=True, extra1=H2O_5864)
H2O_5910_Rows  = make_little_subscheme(flist[9], (5,5), 7, 2, H2O_5910, threshold = VOCTH, ignore_on_first=True, fit_flag_at_end=True, reverse=True, extra1=H2O_5910)
mode_s = int(round((flist[4] - f24) / fsr)) -5
goto_start_H2O_6099 = [Row(f24 + mode_s*fsr,0,ignore|H2O_6099,get_vlaser(flist[4]),modeIndex=int((f24 + mode_s*fsr)/fsr) & 0xFFFF)]
mode_s = int(round((flist[3] - f24) / fsr)) -5    
goto_start_H2O_5962 = [Row(f24 + mode_s*fsr,0,ignore|H2O_5962,get_vlaser(flist[3]),modeIndex=int((f24 + mode_s*fsr)/fsr) & 0xFFFF)]

   
sweep_up = []
f_last = 0.0
laser_now = 1
lines_dict = {'co2_6056':{'f0':6056.506,
                            'r':0.1,
                            'done':False,
                            'rows':CO2_forward},
                'ch4_6057':{'f0':6057.09,
                            'r':0.144,
                            'done':False,
                            'rows':CH4_forward},
                'h2o_6057':{'f0':6057.792,
                            'r':0.105,
                            'done':False,
                            'rows':H2O_forward},
                'nh3_6075':{'f0':6075.61171,
                            'r':0.125,
                            'done':False,
                            'rows':NH3_forward}
                            }
while True:
    line = ffile.readline()
    if not line: break
    values = line.split()
    mode = float(values[0])
    d = 1 + int(values[2])#1
    f = f24+mode*fsr
    dnu = False
    for key in lines_dict:
        f_now = lines_dict[key]['f0']
        r_now = lines_dict[key]['r']
        d_now = lines_dict[key]['done']
        rows = lines_dict[key]['rows']
        if (f >= f_now - r_now) and (f <= f_now + r_now) and (d_now==False):
            sweep_up += rows
            dnu = True
            lines_dict[key]['done'] = True
        elif (f_last < f_now) and (f_now < f) and (d_now==False):
            sweep_up += rows
            lines_dict[key]['done'] = True
        elif (f >= f_now - r_now) and (f <= f_now + r_now):
            dnu = True
    if dnu == False:
        last_laser = laser_now
        laser_now = get_vlaser(f)
        if last_laser != laser_now:
            if len(sweep_up)>0:
                ####add ignore for first data point on laser for reverse scan
                sweep_up.append(Row(sweep_up[-1].setpoint, sweep_up[-1].dwell, sweep_up[-1].virtualLaser, threshold = sweep_up[-1].threshold, extra1=sweep_up[-1].extra1, modeIndex=int(sweep_up[-1].setpoint/fsr) & 0xFFFF))
                sweep_up[-1].subschemeId |= ignore
                sweep_up[-1].dwell = 3
                
            ####add ignore for first data point on laser
            sweep_up.append(Row(f,3,VOC|ignore,get_vlaser(f), threshold = VOCTH, extra1=100, modeIndex=int(f/fsr) & 0xFFFF))
            sweep_up.append(Row(f,d,VOC,get_vlaser(f), threshold = VOCTH, extra1=100, modeIndex=int(f/fsr) & 0xFFFF))
            
        else:
            sweep_up.append(Row(f,d,VOC,get_vlaser(f), threshold = VOCTH, extra1=100, modeIndex=int(f/fsr) & 0xFFFF))

    f_last = f
ffile.close()

sweep_down = deepcopy(sweep_up[::-1])

sweep_up[-1].subschemeId |= fit

schemeRows = sweep_down + sweep_up + H2O_5910_Rows + H2O_5962_Rows + H2O_6099_Rows + HDO_6131_Rows 


#schemeRows = sweep_down + sweep_up + H2O_5910_Rows + H2O_6099_Rows + HDO_6131_Rows 


schemeInfo = {}
schemeInfo.update({'masterFrequency': f24, 'fsr': fsr})
$$$
