

                      AI Autosampler files
                      ====================


                      Author: Tracy Walder

                      Last updated: 2/25/2014



Files under this folder are the latest versions I could find from the network under this folder:

    source code folder:

    M:\Greg\Projects\Autosampler\Latest\Autosampler


Any DLL or EXE files that we ship were used from here instead, rather than Greg's folder above. This
is the folder Manufacturing uses to grab files for installation on new systems.

    ship folder:

    R:\crd_G2000\_Water\AI Autosampler Dev\USB_Install_Drive\AutosamplerExe


Unfortunately Greg left things rather disorganized (without any documentation as to what's what)
so I have to rely on file dates/times and/or use Beyond Compare on text files.


Notes:
------

The x86 folder contains DLLs and executables provided by Applied Instruments, along with some support files.


The ALSG_API.dll file in the ship folder is newer than the one in Greg's folder (1.26.0.0 vs.1.25.4.0)

Use the .td files in the source folder (AddOns\AutosamplerExe) for releases. The ones in x86 are there
for historical purposes. I believe AI included these files in an SDK, which we later modified for distributing
to our customers.


Files:
======

filename                description
--------                -----------
ALS-G_Control.exe       What is this for?

alsgDLL.py              Looks like a program for testing ALSG_API.DLL. Did we write this?

ALSG_API.DLL            Win32 DLL needed by the autosampler code. Needs to be in the same folder as the
                        built Autosampler.exe. File provided by AI.

Autosampler.ini
AutosamplerState.ini


CDM20824_Setup.exe      This is the USB -> Virtual COM Port driver for the autosampler (FTDI USB-Serial converter).
                        FTDI= Future Technology Devices International Ltd.; website is http://www.ftdichip.com
                        
                        Virtual COM Port (VCP) drivers cause the USB device to appear as an additional COM port to
                        the PC. Application software can access the USB device in the same way as it would access
                        a standard COM port.
                        
                        Drivers here: http://www.ftdichip.com/Drivers/VCP.htm
                        
                        Part of the install procedure for Manufacturing is to run this program.

                        There is also an older version named CDM20814_Setup.exe in the ship folder.


Default.td

Method.td

Parameter.ini

Parameter.td

Picarro_Training_Utility.exe    Customized utility program for training the autosampler.

Sequence.td





