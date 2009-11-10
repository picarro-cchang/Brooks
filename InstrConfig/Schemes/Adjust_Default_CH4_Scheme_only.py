#E.Lai
#Scheme Creation for CFADS52_v25_CO2_NW_NoCal_CH4_Cal.sch

#Reading the Generated Scheme files
scheme_file = r'CFADSxx_v25_CO2_NW_NoCal_CH4_Cal.sch'
np = file(scheme_file,"r")

final_np = "001_Alpha_CO2_NW_NoCal_CH4_Cal.sch"
new_lp2 = file(final_np, "w")

#Reading the strings of file
wave_strings = np.readlines()

#Concatenating the strings to produce correct Scheme sequence
string_1 = wave_strings[0]

for x in range(1,8):
    string_1 = string_1 + wave_strings[x]
    sequence = string_1
    
# Correct Scheme Sequence for the CO2 Peak
addline1 = ("6237.40740 3 10 0 0 0\n")
addline2 = ("6237.40770 3 10 0 0 0\n")
addline3 = ("6237.40800 13 10 0 0 0\n")
addline4 = ("6237.40830 3 10 0 0 0\n")
addline5 = ("6237.40860 3 10 0 0 0\n")

concat_addline = addline1 + addline2 + addline3 + addline4 + addline5

string_2 = wave_strings[13]
      
for y in range(14,22):
    string_2 = string_2 + wave_strings[y]
    sequence_2 = string_2
    

string_3 = wave_strings[27]

for z in range(28,69):
    string_3 = string_3 + wave_strings[z]
    sequence_3 = string_3
    

addline6 = ("6237.40740 3 12 0 0 0\n")
addline7 = ("6237.40770 3 12 0 0 0\n")
addline8 = ("6237.40800 13 12 0 0 0\n")
addline9 = ("6237.40830 3 12 0 0 0\n")
addline10 = ("6237.40860 3 12 0 0 0\n")

concat_addline_2 = addline6 + addline7 + addline8 + addline9 + addline10

string_4 = wave_strings[74]

for a in range(75,83):
    string_4 = string_4 + wave_strings[a]
    sequence_4 = string_4
    
string_5 = wave_strings[88]

for b in range(89,100):
    string_5 = string_5 + wave_strings[b]
    sequence_5 = string_5

concat_sequence = sequence + concat_addline + sequence_2 + concat_addline + sequence_3 + concat_addline_2 +  sequence_4 + concat_addline_2 + sequence_5

print >>new_lp2, concat_sequence

#Water Scheme-User input of Cavity FSR
fsr_CO2 = input("Enter CO2 FSR: ")

fsr_CH4 = input("Enter CH4 FSR: ")

fsr_average = float(((fsr_CO2) + (fsr_CH4))/2)

#Functional Variables

scheme_const = 16.000000

fsr_value = wave_strings[103]

fsr_variables = fsr_value.split()

fsr_neg = float(fsr_variables[0])

#Wavelength List Generation

new_add = ("2 26 1 0 0")

print >>new_lp2, fsr_neg, new_add

fsr_list = []

for x in range(1,18):
    fsr_neg = fsr_neg + (-(fsr_average/scheme_const))
    fsr_list.append(fsr_neg)
    
    
for x in range(0,16):
    new_seq = fsr_list[x]
    print >>new_lp2, round(new_seq,5), new_add

#Concatenating the last segment of scheme
string_6 = wave_strings[117]

for x in range(118,124):
    string_6 = string_6 +wave_strings[x]
    sequence_6 = string_6
    
print >>new_lp2, sequence_6

np.close
new_lp2.close
