# File Name: ProportionalMode.py
#
# Purpose: Sample Manager Control Mode Script
#
# Rules/Notations:
# - Avoid all direct access to _DriverRpc
# - "if self._terminateCalls==True: return", should be add inside routines that take
#   a long time to execute. This is used to terminate current calls when
#   commands is received.
# - Class name and filename should be same (excluding ".py" extension).
#   Section name inside configuration file must also be the same.
# - Config names inside configuration file must not collide with names in base class
#   and script.
# - Do not use time.sleep directly, use self._sleep.
#
# RPC Commands exported
#   - FlowStart
#   - FlowStop
#   - FlowPumpDisable
#   - Prepare
#   - Park
#   - Purge
#
# File History:
# 06-11-06 ytsai   Created file
# 12-30-09 alex    Modified code for G2000 platform

import os
import sys
import time
import getopt
from Host.autogen import interface
from Host.SampleManager.SampleManager import *


class ProportionalMode(SampleManagerBaseMode):
    def RPC_FlowStart(self):
        """START FLOW"""
        status = self._RPC_GetStatus()
        mask = SAMPLEMGR_STATUS_STABLE | SAMPLEMGR_STATUS_FLOWING | SAMPLEMGR_STATUS_FLOW_STARTED
        if (status & mask) == mask:
            return True
        self._clearStatus()

        self._LPC_WritePressureSetpoint(self.operate_pressure_sp_torr)

        # Check for terminate request. See terminate remarks in Sample Manager base class.
        if self._terminateCalls: return False

        # Set valve control
        if self.valve_mode == INLETVALVE:
            self._LPC_SetValveControl(interface.VALVE_CNTRL_InletControlState)
        elif self.valve_mode == OUTLETVALVE:
            self._LPC_SetValveControl(interface.VALVE_CNTRL_OutletControlState)

        # Step valve to target value (valve stepped is opposite of valve controlled )
        if self.valve_mode == INLETVALVE:
            stepValve = OUTLETVALVE
            targetpos = self.outlet_valve_target
            minpos = self.outlet_valve_start
        elif self.valve_mode == OUTLETVALVE:
            stepValve = INLETVALVE
            targetpos = self.inlet_valve_target
            minpos = self.inlet_valve_start
        startpos = self._RPC_GetValve(stepValve)
        if startpos < minpos:
            startpos = minpos
        deltapos = targetpos - startpos
        step = self.proportional_step
        try:
            iterations = deltapos / step
            status = self._LPC_StepValve(valve=stepValve, start=startpos, step=step, iterations=iterations, interval=2)
            if status == False:
                print "Step valve failed."
                return False
        except:
            pass
        self._LPC_SetValve(stepValve, targetpos)
        self._Sleep(5)

        # Wait until pressure stabilize
        # setPoint = self._RPC_ReadPressureSetpoint()
        print "Waiting for pressure to stabilize"
        status = self._LPC_WaitPressureStabilize(self.operate_pressure_sp_torr,
                                                 tolerance=0.02,
                                                 timeout=600,
                                                 checkInterval=1,
                                                 lockCount=5)
        if status == False:
            print "Pressure failed to stabilize."
            return False
        print "After pressure stabilization"
        # N.B. Assert SAMPLEMGR_STATUS_FLOW_STARTED to allow measurements to start
        self._setStatus(SAMPLEMGR_STATUS_FLOW_STARTED)

    def RPC_FlowStop(self):
        """STOP FLOW"""
        print "RPC_FlowStop"
        if self.valve_mode == INLETVALVE:
            self._LPC_CloseValve(OUTLETVALVE)
        else:
            self._LPC_CloseValve(INLETVALVE)
        self._LPC_StopValveControl()
        self._LPC_StopSolenoidValveControl()
        self._clearStatus()

    def RPC_Park(self):
        """PARK"""
        self.RPC_FlowStop()

        self._LPC_WritePressureSetpoint(self.fill_pressure_sp_torr)

        # Check to see if need to pump down cavity
        if self._RPC_ReadPressure() > self._RPC_ReadPressureSetpoint():
            if self._LPC_PumpDownCavity(tolerance=0.01) == False:
                return False  # TODO: report to INSTRMGR
        # Goto pressure with inlet control
        else:
            self._LPC_SetValveControl(interface.VALVE_CNTRL_InletControlState)
            self._LPC_WaitPressureStabilize(self.fill_pressure_sp_torr, tolerance=0.001, timeout=600, checkInterval=0.5)
            if status == False:
                print "Pressure failed to stabilize."

        self._LPC_StopValveControl()
        self._LPC_WritePressureSetpoint(self.operate_pressure_sp_torr)
        self._setStatus(SAMPLEMGR_STATUS_PARKED, excl=True)

        self._LPC_StopSolenoidValveControl()

    def RPC_Prepare(self):
        """PREPARE"""
        #self._LPC_OpenSolenoidValves( self.solenoid_valves )
        #self._setStatus( SAMPLEMGR_STATUS_PREPARED )
        self._LPC_StartSolenoidValveControl('SmScript', 'Solenoid3ValveControl', 'VALVES')

    def RPC_Purge(self):
        """PURGE"""
        self._setStatus(SAMPLEMGR_STATUS_PURGED, excl=True)
