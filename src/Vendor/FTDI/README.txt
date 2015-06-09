
                FTDI Files
                Future Technology Devices International Ltd.
                
                website: http://www.ftdichip.com
                
We are using their Virtual COM Port (VCP) drivers for autosampler communications.

CDM = Combined Driver Model.

FTDI have previously provided two types of driver for Windows OS: a D2XX direct driver and a virtual 
COM port (VCP) driver. Previously, these drivers were mutually exclusive and could not be installed at the 
same time. The new Windows combined driver model (CDM) which may be installed on Windows 2000, 
XP, VISTA or Windows 7 allows applications to access FTDI devices through either the D2XX DLL or a 
COM port without having to change driver type. However, it should be noted that an application can only 
communicate through one of these interfaces at a time and cannot send commands to the D2XX DLL and 
the associated COM port at the same time. 


Web site description:
    Virtual COM port (VCP) drivers cause the USB device to appear as an additional
    COM port available to the PC. Application software can access the USB device
    in the same way as it would access a standard COM port.
    
Current driver version for Windows is 2.08.30 (release date 2013-08-01). It includes
support for: Windows XP, Windows Server 2003, Windows Vista, Windows Server 2008,
Windows 7, Windows Server 2008 R2 and Windows 8. Same version covers both x86 and x64.

Also, as Windows 8 RT is a closed system not allowing for 3rd party driver installation
our Windows 8 driver will not support this variant of the OS.


The "CDM 2.08.30 WHQL Certified" folder contains the 2.8.30.0 driver download files from FTDI.
