import os
import shutil
import subprocess
import time

def userInput():
    print " "
    instrTypeSelect = raw_input("Input analyzer type and press Enter: ")
    instrTypeSelect = str(instrTypeSelect)
    instrTypeSelect = instrTypeSelect.upper()
    print " "

    if instrTypeSelect == "1" or instrTypeSelect == "CFGDS":
        print "You selected: CFGDS"
        instrType = 1
        instrTypeStr = "CFGDS"
    elif instrTypeSelect == "2" or instrTypeSelect == "CFFDS":
        print "You selected: CFFDS"
        instrType = 2
        instrTypeStr = "CFFDS"
    elif instrTypeSelect == "3" or instrTypeSelect == "CFKADS":
        print "You selected: CFKADS"
        instrType = 3
        instrTypeStr = "CFKADS"
    elif instrTypeSelect == "4" or instrTypeSelect == "CFKBDS":
        print "You selected: CFKBDS"
        instrType = 4
        instrTypeStr = "CFKBDS"
    elif instrTypeSelect == "5" or instrTypeSelect == "CFIDS":
        print "You selected: CFIDS"
        instrType = 5
        instrTypeStr = "CFIDS"
    elif instrTypeSelect == "6" or instrTypeSelect == "FCDS":
        print "You selected: FCDS"
        instrType = 6
        instrTypeStr = "FCDS"
    elif instrTypeSelect == "7" or instrTypeSelect == "FDDS":
        print "You selected: FDDS"
        instrType = 7
        instrTypeStr = "FDDS"
    elif instrTypeSelect == "8" or instrTypeSelect == "JFAADS":
        print "You selected: JFAADS"
        instrType = 8
        instrTypeStr = "JFAADS"
    elif instrTypeSelect == "9" or instrTypeSelect == "CKADS":
        print "You selected: CKADS"
        instrType = 9
        instrTypeStr = "CKADS"
    elif instrTypeSelect == "10" or instrTypeSelect == "AEDS":
        print "You selected: AEDS"
        instrType = 10
        instrTypeStr = "AEDS"
    elif instrTypeSelect == "11" or instrTypeSelect == "SI2000":
        print "You selected: SI2000"
        instrType = 11
        instrTypeStr = "SI2000"	
    else:
        print "Invalid analyzer type! Please try again."
        print "_________________________________________________________________"
        instrType = -1
        instrTypeStr = "invalid"
    
    
    return instrType, instrTypeStr

#determine present working directory
pwd = os.getcwd()
		
#set userlog file paths
userLogIniFilePath = 'C:\Picarro\G2000\AppConfig\Config\DataLogger'
###userLogIniFilePath = pwd + r'\TestCopy'
pathNewUserLog = pwd + r'\UserLogFiles'
	
#print welcome information
print " "
print "Welcome to the Pressure Chamber Test Program!"
print " "
print "Available analyzer types are:"
print "\t1. CFGDS"
print "\t2. CFFDS"
print "\t3. CFKADS"
print "\t4. CFKBDS"
print "\t5. CFIDS"
print "\t6. FCDS"
print "\t7. FDDS"
print "\t8. JFAADS"
print "\t9. CKADS"
#print "\t10. "
print "\t11. SI2000"
print "_________________________________________________________________"

#prompt user for analyzer type
instrType = -1
while instrType == -1:
    instrType, instrTypeStr = userInput()

#prompt user to confirm analyzer type selection
answerYN = 'N'
while answerYN != 'Y':
    answerYN = raw_input("Did you select the correct analyzer type? (Y/N): ")
    answerYN = str(answerYN)
    answerYN = answerYN.upper()
    if answerYN == 'N':
        #prompt user for analyzer type
        instrType = -1
        while instrType == -1:
            instrType, instrTypeStr = userInput()


print " "
raw_input("Connect pressure sensor to COM2 and press Enter...")

#launch program to read pressure sensor
pressProg = subprocess.Popen(r'start /wait python ' + pwd + r'\PressureSensorPrograms\PressureChamberTest_v0-1.py', shell=True)
#prompt user to confirm correct operation of pressure sensor
answerYN = 'N'
while answerYN != 'Y':
    answerYN = raw_input("Did the pressure sensor start correctly? (Y/N): ")
    answerYN = str(answerYN)
    answerYN = answerYN.upper()
    if answerYN == 'N':
        print "STOP! Close all command windows, disconnect pressure sensor and start over..."
        while True:
            dummy = True
	
if instrType == 3 or instrType == 4:
    #save a backup copy of the original UserLog.ini file
    shutil.copyfile(userLogIniFilePath + r'\UserLog_CFKADS.ini', userLogIniFilePath + r'\UserLog_CFKADS_BACKUP.ini')
    
    #make test specific changes to the UserLog.ini file
    shutil.copyfile(pathNewUserLog + r'\UserLog_CFKADS_CFKADS.ini', userLogIniFilePath + r'\UserLog_CFKADS.ini')
elif instrType == 9:
    #save a backup copy of the original UserLog.ini file
    shutil.copyfile(userLogIniFilePath + r'\UserLog_CKADS.ini', userLogIniFilePath + r'\UserLog_CKADS_BACKUP.ini')
    
    #make test specific changes to the UserLog.ini file
    shutil.copyfile(pathNewUserLog + r'\UserLog_CKADS_CKADS.ini', userLogIniFilePath + r'\UserLog_CKADS.ini')
elif instrType == 11:
    #save a backup copy of the original UserLog.ini file
    #shutil.copyfile(userLogIniFilePath + r'\UserLog_AMADS_lct.ini', userLogIniFilePath + r'\UserLog_AMADS_lct_BACKUP.ini')
    
    #make test specific changes to the UserLog.ini file
    #shutil.copyfile(pathNewUserLog + r'\UserLog_AMADS.ini', userLogIniFilePath + r'\UserLog_AMADS_lct.ini')
	pass
else:
    #save a backup copy of the original UserLog.ini file
    shutil.copyfile(userLogIniFilePath + r'\UserLog.ini', userLogIniFilePath + r'\UserLog_BACKUP.ini')
    
    #make test specific changes to the UserLog.ini file
    shutil.copyfile(pathNewUserLog + r'\UserLog_' + instrTypeStr + r'.ini', userLogIniFilePath + r'\UserLog.ini')    

#Inform user
if instrType == 5 or instrType == 8:
    print "_________________________________________________________________"
    print "UserLog.ini updated. Log file will write to:"
    print "C:\UserData\DataLog_User"
    print "_________________________________________________________________"
else:
    print "_________________________________________________________________"
    print "UserLog.ini updated. Log file will write to:"
    print "C:/Picarro/G2000/Log/PressureTest"
    print "_________________________________________________________________"





#restart analyzer
print " "
print "Select \"Stop software but keep driver running\"..."
os.system(r"C:\Picarro\G2000\HostExe\StopSupervisor.exe")
print " "
print "Starting mode switcher..."
time.sleep(15)
print "Please restart analyzer in the correct mode..."
quickGuiProg = subprocess.Popen(r'C:\Picarro\G2000\HostExe\SupervisorLauncher.exe -c C:\Picarro\G2000\\AppConfig\Config\Utilities\SupervisorLauncher_Integration.ini')
print "Wait for analyzer to start up completely..."
time.sleep(2)

#ask user if analyzer restarted correctly
answerYN = 'N'
while answerYN != 'Y':
    answerYN = raw_input("Did the analyzer start correctly? (Y/N): ")
    answerYN = str(answerYN)
    answerYN = answerYN.upper()
    if answerYN == 'N':
        #restart analyzer
		print " "
		print "Select \"Stop software but keep driver running\"..."
		os.system(r"C:\Picarro\G2000\HostExe\StopSupervisor.exe")
		print " "
		print "Starting analyzer, please wait..."
		time.sleep(15)
		quickGuiProg = subprocess.Popen(r'C:\Picarro\G2000\HostExe\SupervisorLauncher.exe -a -c C:\Picarro\G2000\\AppConfig\Config\Utilities\SupervisorLauncher.ini')
		print "Wait for analyzer to start up completely..."
		time.sleep(2)

#Prompt user to initiate pressure control
print "_________________________________________________________________"
print "Ready to run test, use Flow Vision software for pressure control..."

#ask user if test is finished
print "_________________________________________________________________"
print "Test running..."
answerYN = 'N'
while answerYN != 'Y':
    print " "
    answerYN = raw_input("Test complete? (Y/N): ")
    answerYN = str(answerYN)
    answerYN = answerYN.upper()
    if answerYN == 'N':
        print "Continuing measurements..."

#user confirm if test is completed
answerYN = 'N'
while answerYN != 'Y':
    print " "
    answerYN = raw_input("Are you sure the test is complete? (Y/N): ")
    answerYN = str(answerYN)
    answerYN = answerYN.upper()
    if answerYN == 'N':
        print "Continuing measurements..."


print " "
print "Restoring analyzer..."
if instrType == 3 or instrType == 4:
	#restore UserLog.ini file
    shutil.copyfile(userLogIniFilePath + r'\UserLog_CFKADS_BACKUP.ini', userLogIniFilePath + r'\UserLog_CFKADS.ini')
    print "Cleaning up files..."
    os.remove(userLogIniFilePath + r'\UserLog_CFKADS_BACKUP.ini')
elif instrType == 9:
	#restore UserLog.ini file
    shutil.copyfile(userLogIniFilePath + r'\UserLog_CKADS_BACKUP.ini', userLogIniFilePath + r'\UserLog_CKADS.ini')
    print "Cleaning up files..."
    os.remove(userLogIniFilePath + r'\UserLog_CKADS_BACKUP.ini')
elif instrType == 11:
	#restore UserLog.ini file
    #shutil.copyfile(userLogIniFilePath + r'\UserLog_AMADS_lct_BACKUP.ini', userLogIniFilePath + r'\UserLog_AMADS_lct.ini')
    #print "Cleaning up files..."
    #os.remove(userLogIniFilePath + r'\UserLog_AMADS_lct_BACKUP.ini')
	pass
else:
    #restore UserLog.ini file
    shutil.copyfile(userLogIniFilePath + r'\UserLog_BACKUP.ini', userLogIniFilePath + r'\UserLog.ini')
    print "Cleaning up files..."
    os.remove(userLogIniFilePath + r'\UserLog_BACKUP.ini')

print "Test completed successfully!"
print "Please close all command windows"