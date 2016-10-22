import psutil as pu
from tables import *
import time
import ntplib

MapPort2Program = {
         50000: "LOGGER",
         50010: "DRIVER",
         50015: "FREQ_CONVERTER",
         50030: "SUPERVISOR",
         50031: "SUPERVISOR_BACKUP",
         50050: "CONTROLLER",
         50060: "ARCHIVER",
         50070: "MEAS_SYSTEM",
         50075: "SPECTRUM_COLLECTOR",
         50080: "SAMPLE_MGR",
         50090: "DATALOGGER",
         50100: "ALARM_SYSTEM",
         50110: "INSTR_MANAGER",
         50120: "COMMAND_HANDLER",
         50160: "DATA_MANAGER",
         50180: "FITTER1",
         50181: "FITTER2",
         50182: "FITTER3",
         50200: "VALVE_SEQUENCER",
         50210: "COORDINATOR",
         50220: "QUICK_GUI",
         50072: "PERIPH_INTRF",
         50073: "CONFIG_MONITOR"
    }

TableColumns = {
    "time": Float64Col(),  
    "CPU_Usage": Float32Col(), 
    "Memory_Usage": Float32Col(),
    "Time_Offset": Float32Col(),
    "Time_Delay": Float32Col()
}
    
date = time.strftime("%Y%m%d_%H%M%S", time.localtime())
output = openFile(r"test_results_" + date + ".h5", "w")
Picarro_Programs = []
for proc in pu.process_iter():
    for c in proc.connections():
        try:
            port = int(c.laddr[1])
            if port in MapPort2Program:
                TableColumns[MapPort2Program[port] + "_Mem"] = Int64Col()
                #TableColumns[MapPort2Program[port] + "_CPU"] = Int64Col()
                Picarro_Programs.append(port)
        except:
            pass
filters = Filters(complevel=1, fletcher32=True)
table = output.createTable(output.root, "results", TableColumns, filters=filters)
row = table.row
ntp = ntplib.NTPClient()
old_time = time.time()
try:
    while True:
        t = time.time()
        row['time'] = t
        row['CPU_Usage'] = pu.cpu_percent()
        row['Memory_Usage'] = pu.virtual_memory().percent
        try:
            response = ntp.request('pool.ntp.org', version=3)
            row['Time_Offset'] = response.offset
            row['Time_Delay'] = response.delay
        except Exception, e:
            print "%s: %s" % (Exception, e)
        for proc in pu.process_iter():
            for c in proc.connections():
                try:
                    port = int(c.laddr[1])
                    if port in Picarro_Programs:
                        row[MapPort2Program[port] + "_Mem"] = proc.memory_info().rss
                        #row[MapPort2Program[port] + "_CPU"] = proc.cpu_percent()
                except:
                    pass
        row.append()
        print t
        if t - old_time >= 100:
            table.flush()
            print "OK"
            old_time = t
        time.sleep(5)
except Exception, e:
    print "%s: %s" % (Exception, e)
    raise
finally:
    output.close()
