# File Name: SmScript.py
#
# Purpose: This script file controls the solenoid valves (3-Valve Control)
#
#
# File History:
# 06-11-20 ytsai   Created file

def Solenoid3ValveControl( parent, config ):
    """ This is the script for controlling '3 Valves'
    """

    # Default valves to open up
    parent._LPC_OpenSolenoidValves( config['valve_default'] )

    # If valve sequencer disabled return
    if eval(config['valve_sequencer_enable'])==0:
        return

    # construct list of valves to open.
    ControlList = [
      (1, config['valve1_time'], config['valve1_bottle']),
      (2, config['valve2_time'], config['valve2_bottle']),
      (3, config['valve3_time'], config['valve3_bottle']) ]

    # Go through list of valves and control them
    while ( parent._terminateSolenoidControl == False and len(ControlList)>0 ):

        # remove valve parameters at head of list
        valve, duration, concentration = ControlList.pop( 0 )

        # open valves for specified duration and close them afterwards.
        parent._LPC_OpenCloseSolenoidValves( valve, eval(duration), eval(concentration) )
