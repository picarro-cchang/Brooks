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
# 11-21-16 dfleck   modified outletonly flow mode, increased pressure timeout to hours from 5 minutes

import os, sys, time, getopt
from Host.autogen import interface
from Host.SampleManager import *

class OutletOnlyMode(SampleManagerBaseMode):

  def RPC_FlowStart(self):
    """START FLOW"""
    status = self._RPC_GetStatus()
    mask = SAMPLEMGR_STATUS_STABLE|SAMPLEMGR_STATUS_FLOWING|SAMPLEMGR_STATUS_FLOW_STARTED
    if (status & mask) == mask:
        return True
    # Check that cavity is warmed up to within 5 degC of setpoint before starting flow
    cavityTemp,cavityTempSetpoint = self._RPC_ReadCavityTemperatureAndSetpoint()
    
    if abs(cavityTemp-cavityTempSetpoint) > 5:
        print "Cavity temperature is too far from setpoint to start flow. Difference is", abs(cavityTemp-cavityTempSetpoint)
        return False
        
    self._clearStatus()
    
    self._LPC_WritePressureSetpoint( self.operate_pressure_sp_torr )
    
    # Check for terminate request. See terminate remarks in Sample Manager base class.
    if self._terminateCalls: return False

    # Set valve control
    self._LPC_SetValveControl(interface.VALVE_CNTRL_OutletOnlyControlState )
    
    # Wait until pressure stabilize
    # setPoint = self._RPC_ReadPressureSetpoint()
    print "Waiting for pressure to stabilize"
    status = self._LPC_WaitPressureStabilize( self.operate_pressure_sp_torr, tolerance=0.02,
      timeout=18000, checkInterval=2, lockCount=5 )
    if status==False:
        print "Pressure failed to stabilize."
        return False
    print "After pressure stabilization"
    # N.B. Assert SAMPLEMGR_STATUS_FLOW_STARTED to allow measurements to start
    self._setStatus( SAMPLEMGR_STATUS_FLOW_STARTED ) 

  def RPC_FlowStop(self):
    """Close outlet valve by setting high pressure setpoint"""
    self._LPC_WritePressureSetpoint( self.fill_pressure_sp_torr )
    self._clearStatus()

  def RPC_Park(self):
    """PARK"""
    self.RPC_FlowStop()

    self._LPC_WritePressureSetpoint( self.fill_pressure_sp_torr )
    self._LPC_WaitPressureStabilize( self.fill_pressure_sp_torr, tolerance=0.001, timeout=120, checkInterval=0.5 )
    self._LPC_StopValveControl()
    self._setStatus( SAMPLEMGR_STATUS_PARKED, excl=True )

    self._LPC_StopSolenoidValveControl()

  def RPC_Prepare(self):
    """PREPARE"""
    #self._LPC_OpenSolenoidValves( self.solenoid_valves )
    #self._setStatus( SAMPLEMGR_STATUS_PREPARED )
    self._LPC_StartSolenoidValveControl( 'SmScript', 'Solenoid3ValveControl', 'VALVES' )
    
  def RPC_Purge(self):
    """PURGE"""
    self._setStatus( SAMPLEMGR_STATUS_PURGED, excl=True )
