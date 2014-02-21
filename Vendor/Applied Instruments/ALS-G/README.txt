

                      AI Autosampler files
                      ====================


                      Author: Tracy Walder

                      Last updated: 2/20/2014



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

Picarro_Training_Utility.exe - how did we build this? was it custom created for us?

ALS-G_Control.exe - what is this for?

CDM20824_Setup.exe - What does this do? Part of the install procedure for Manufacturing is to run this program.
                     There is also an older version named CDM20814_Setup.exe in the ship folder.







