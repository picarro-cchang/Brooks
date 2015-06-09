; USB related files and driver installation

[Files]
Source: {#sandboxDir}\host\Vendor\libusb\libusb1\libusb-1.0.dll; DestDir: {sys}; Tasks: LibUSB; Flags: replacesameversion

[Tasks]
Name: LibUSB; Description: Install USB driver; Flags: unchecked
