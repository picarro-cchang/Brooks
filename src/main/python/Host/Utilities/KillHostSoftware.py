import os

host_software_components = ["AlarmSystem", "Archiver", "Controller", "ControlBridge", \
                            "DataLogger", "DataManager", "DataManagerPublisher", "Driver", \
                            "EventManager", "Fitter", "HostStartup", "InstMgr", "MobileKitMonitor", \
                            "MeasSystem", "QuickGui", "RDFreqConverter", "RestartSurveyor", "RestartSupervisor", "SampleManager", \
                            "Serial2Socket", "SpectrumCollector", "StopSupervisor", "Supervisor", "SupervisorLauncher" \
                            ]

for c in host_software_components:
    os.system(r'taskkill.exe /IM ' + c + '.exe /F')