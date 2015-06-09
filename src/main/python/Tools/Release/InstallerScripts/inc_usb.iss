; USB related files and driver installation

[Files]
Source: {#sandboxDir}\host\Vendor\libusb\libusb0\libusb0.dll; DestDir: {sys}; Tasks: LibUSB; Flags: replacesameversion

Source: {#sandboxDir}\host\Vendor\libusb\libusb0\libusb0.sys; DestDir: {sys}\Drivers; Tasks: LibUSB; Flags: replacesameversion

Source: {#sandboxDir}\host\Vendor\libusb\libusb0\PicarroUninitialized.inf; DestDir: {win}\inf; Flags: replacesameversion; BeforeInstall: MyBeforeInstall

Source: {#sandboxDir}\host\Vendor\libusb\libusb0\PicarroUSB.inf; DestDir: {win}\inf; Flags: replacesameversion

Source: {#sandboxDir}\host\Vendor\libusb\libusb0\Cypress.inf; DestDir: {win}\inf; Flags: replacesameversion


[Tasks]
Name: LibUSB; Description: Install USB driver; Flags: unchecked







