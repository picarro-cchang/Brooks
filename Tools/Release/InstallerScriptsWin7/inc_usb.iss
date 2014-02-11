; USB related files and driver installation

[Files]
Source: {#resourceDir}\libusb0.dll; DestDir: {sys}; Tasks: LibUSB; Flags: replacesameversion
Source: {#resourceDir}\libusb0.sys; DestDir: {sys}\Drivers; Tasks: LibUSB; Flags: replacesameversion
Source: {#resourceDir}\PicarroUSB.inf; DestDir: {win}\inf; Flags: replacesameversion

[Tasks]
Name: LibUSB; Description: Install USB driver
