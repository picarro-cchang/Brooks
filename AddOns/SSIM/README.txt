SSIM2 software and firmware

Author:       Tracy Walder
Last updated: 4/16/2014


***************************
   SSIM2 Host Software
***************************

The software only consists of an installer that installs config files and shortcuts. Works with existing host software.

For this reason, did not require a rebuild for Win7, and builds are compatible with both WinXP and Win7.
A change in the user manual should trigger a new build, as would any SSIM config file changes.

Note: The release.py script needs to be updated to work when using source from a git branch, since
      currently the master branch is way out of date!



***************************
   Arduino Firmware
***************************
Arduino firmware source code is archived in these folders:

_1_04\
    _1_04.pde    1.04 source, was current version shipping on SSIM2 modules incorporating Arduino R2 boards.
                 Compatible with Arduino 1.0 application to compile/upload to the R2 board.
                 
                 Original version came from here: S:\Projects\SSIM2\Firmware\_1_04
    
_1_05\
   _1_05.ino     1.05 source, for Arduino R3 boards which require a newer driver on the host computer. 
                 The 1.0.5-r2 Arduino tools and driver are pre-installed on Win7 images. In order to
                 use this tool version to compile/upload software to the R3 board, had to change
                 Wire.receive() -> Wire.read(); also bumped version number to 1.05 (uf command).

                 
To load and test firmware on the Arduino board:

1. Install the driver and tools on the host Win7 (or WinXP) box
        M:\LV8_Development\Instrument Install Software\arduino-1.0   (for R2 boards)

        M:\LV8_Development\Instrument Install Software W7\arduino-1.0.5-r2-windows.zip (going forward)
        
   Can unpack the zip and run dpinst-x86.exe in arduino-1.0.5-r2\drivers folder to install the driver.

2. Run arduino.exe in the arduino-1.0.5-r2 folder. Tools > Serial Port, select the serial port it is
   operating on (typically COM10).

3. File > Open, select _1_05\_1_05.ino

4. Verify the code compiles by clicking the Verify toolbar button (looks like a checkmark)

5. Upload it by clicking the Upload toolbar button (looks like a right arrow)

6. Tools > Serial Monitor to open a serial command window
   a. type uf<Enter> which reports the version number (1.05)
   b. if Arduino is in a SSIM2 module (with the daughterboard piggybacked), can initialize the
      pressure settings (linear relationship) using these commands:
      
      uB0    (a zero not the letter O; sets the y-offset to 0)
      uM1500 (sets the slope to 1500)
      
      Note: Mfg calibrates these settings, but these values are good enough for validation that
      the Arduino is working in the SSIM2

   c. read the voltage from the pressure sensor
      u7     (reports a value, like 0.49651)
      
   d. read the pressure, in Torr
      u8     (reports a value, like 745.450927)

After confirming the firmware is functioning properly, save it to a new folder (best to follow the
existing naming convention), add it to git, and copy it to the network where Mfg. uses it. Currently
this is located here: S:\Projects\SSIM2\Firmware





