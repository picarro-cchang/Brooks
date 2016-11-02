#!/usr/bin/python
#
"""
File Name: ValveControl.py
Purpose: Controller for valves and sample handling

File History:
    23-Oct-2016  sze  Initial version.

Copyright (c) 2016 Picarro, Inc. All rights reserved
"""
from collections import deque
import math

from Host.autogen import interface
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log, LogExc
from Host.DriverSimulator.Utilities import prop_das, prop_fpga

APP_NAME = "DriverSimulator"
EventManagerProxy_Init(APP_NAME)

INVALID_PRESSURE_VALUE = -100.0

class ValveControl(object):
    # Hard-wired constants for flow control when locked
    flowFractionalFlowTol = 0.02
    flowPressureTol = 1.0
    flowControlLockedGain = 0.4
    #
    state = prop_das(interface.VALVE_CNTRL_STATE_REGISTER)
    cavityPressure = prop_das(interface.CAVITY_PRESSURE_REGISTER)
    setpoint = prop_das(interface.VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER)
    userInlet = prop_das(interface.VALVE_CNTRL_USER_INLET_VALVE_REGISTER)
    userOutlet = prop_das(interface.VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER)
    inlet = prop_das(interface.VALVE_CNTRL_INLET_VALVE_REGISTER)
    outlet = prop_das(interface.VALVE_CNTRL_OUTLET_VALVE_REGISTER)
    dpdtMax = prop_das(interface.VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER)
    dpdtAbort = prop_das(interface.VALVE_CNTRL_CAVITY_PRESSURE_RATE_ABORT_REGISTER)
    inletGain1 = prop_das(interface.VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER)
    inletGain2 = prop_das(interface.VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER)
    inletMin = prop_das(interface.VALVE_CNTRL_INLET_VALVE_MIN_REGISTER)
    inletMax = prop_das(interface.VALVE_CNTRL_INLET_VALVE_MAX_REGISTER)
    inletMaxChange = prop_das(interface.VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER)
    outletGain1 = prop_das(interface.VALVE_CNTRL_OUTLET_VALVE_GAIN1_REGISTER)
    outletGain2 = prop_das(interface.VALVE_CNTRL_OUTLET_VALVE_GAIN2_REGISTER)
    outletMin = prop_das(interface.VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER)
    outletMax = prop_das(interface.VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER)
    outletMaxChange = prop_das(interface.VALVE_CNTRL_OUTLET_VALVE_MAX_CHANGE_REGISTER)
    solenoidValves = prop_das(interface.VALVE_CNTRL_SOLENOID_VALVES_REGISTER)
    threshState = prop_das(interface.VALVE_CNTRL_THRESHOLD_STATE_REGISTER)
    latestLoss = prop_das(interface.RDFITTER_LATEST_LOSS_REGISTER)
    lossThreshold = prop_das(interface.VALVE_CNTRL_RISING_LOSS_THRESHOLD_REGISTER)
    rateThreshold = prop_das(interface.VALVE_CNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER)
    inletTriggeredValue = prop_das(interface.VALVE_CNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER)
    outletTriggeredValue = prop_das(interface.VALVE_CNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER)
    solenoidMask = prop_das(interface.VALVE_CNTRL_TRIGGERED_SOLENOID_MASK_REGISTER)
    solenoidState = prop_das(interface.VALVE_CNTRL_TRIGGERED_SOLENOID_STATE_REGISTER)
    sequenceStep = prop_das(interface.VALVE_CNTRL_SEQUENCE_STEP_REGISTER)
    flowState = prop_das(interface.FLOW_CNTRL_STATE_REGISTER)
    flow = prop_das(interface.FLOW1_REGISTER)
    flowSetpoint = prop_das(interface.FLOW_CNTRL_SETPOINT_REGISTER)
    flowControlGain = prop_das(interface.FLOW_CNTRL_GAIN_REGISTER)

    def __init__(self, sim):
        self.sim = sim
        self.das_registers = sim.das_registers
        self.fpga_registers = sim.fpga_registers

    def init(self):
        self.valveCntrlDelay = 20
        self.state = interface.VALVE_CNTRL_DisabledState
        self.threshState = interface.VALVE_CNTRL_THRESHOLD_DisabledState
        self.inlet = 0
        self.outlet = 0
        self.solenoidValves = 0
        self.sequenceStep = -1
        self.deltaT = 0.2
        self.lastLossPpb = 0
        self.lastPressure = INVALID_PRESSURE_VALUE
        self.dwellCount = 0
        self.nonDecreasingCount = 0
        self.previousState = self.state
        self.savedInletValue = 0
        self.savedOutletValue = 0
        self.savedState = interface.VALVE_CNTRL_DisabledState
        self.last5 = deque()
        return interface.STATUS_OK

    def proportionalValveStep(self):
        
        # Calculate finite difference approximation to pressure change rate
        #  and update self.nonDecreasingCount 
        if self.lastPressure > INVALID_PRESSURE_VALUE:
            dpdt = (self.cavityPressure - self.lastPressure) / self.deltaT
            if self.cavityPressure - self.lastPressure > -0.2:
                self.nonDecreasingCount += 1
            else:
                self.nonDecreasingCount = 0
        else:
            dpdt = 0
        error = self.setpoint - self.cavityPressure
        self.lastPressure = self.cavityPressure

        # Check if we exceed maximum rate of change allowed
        if abs(dpdt) > self.dpdtAbort:
            self.sim.message_puts(interface.LOG_LEVEL_STANDARD, "Maximum pressure change exceeded. Valves closed to protect cavity.")
            state = interface.VALVE_CNTRL_DisabledState

        if self.state == interface.VALVE_CNTRL_DisabledState:
            self.inlet = 0
            self.outlet = 0
            self.nonDecreasingCount = 0
        elif self.state == interface.VALVE_CNTRL_ManualControlState:
            self.inlet = self.userInlet
            self.outlet = self.userOutlet
        elif self.state == interface.VALVE_CNTRL_OutletControlState:
            # Control pressure using outlet proportional valve. The inlet proportional
            #  valve controls the flow (or is set to a user-specified value if flow
            #  control is not enabled)
            if self.flowState == interface.FLOW_CNTRL_DisabledState:
                self.inlet = self.userInlet
            elif self.flowState == interface.FLOW_CNTRL_EnabledState:
                # Control the flow using the inlet valve
                flowGain = self.flowControlGain
                if (abs(self.flow - self.flowSetpoint) < self.flowFractionalFlowTol * self.flowSetpoint and
                    abs(self.setpoint - self.cavityPressure) < self.flowPressureTol):
                    flowGain = self.flowControlLockedGain
                delta = flowGain * (self.flowSetpoint - self.flow)
                delta = min(max(delta, -self.inletMaxChange), self.inletMaxChange)
                valveValue = self.inlet + delta
                valveValue = min(max(valveValue, self.inletMin), self.inletMax)
                self.inlet = valveValue
            # Control of outlet valve 
            # Gain2 sets how the pressure rate setpoint depends on the pressure error
            dpdtSet = self.outletGain2 * error
            dpdtSet = min(max(dpdtSet, -self.dpdtMax), self.dpdtMax)
            # Implement an integral controller for the rate of change of pressure
            # Gain1 sets the integral gain
            dError = dpdtSet - dpdt
            delta = -self.outletGain1 * dError  # -ve because opening outlet valve decreases pressure
            delta = min(max(delta, -self.outletMaxChange), self.outletMaxChange)
            valveValue = self.outlet + delta
            valveValue = min(max(valveValue, self.outletMin), self.outletMax)
            self.outlet = valveValue
        elif self.state == interface.VALVE_CNTRL_InletControlState:
            # Control pressure using inlet proportional valve. The outlet proportional
            #  valve controls the flow (or is set to a user-specified value if flow
            #  control is not enabled)
            if self.flowState == interface.FLOW_CNTRL_DisabledState:
                self.outlet = self.userOutlet
            elif self.flowState == interface.FLOW_CNTRL_EnabledState:
                # Control the flow using the outlet valve
                flowGain = self.flowControlGain
                if (abs(self.flow - self.flowSetpoint) < 5.0 and
                    abs(self.setpoint - self.cavityPressure) < 1.0):
                    flowGain = 1.0
                delta = flowGain * (self.flowSetpoint - self.flow)
                delta = min(max(delta, -self.outletMaxChange), self.outletMaxChange)
                valveValue = self.outlet + delta
                valveValue = min(max(valveValue, self.outletMin), self.outletMax)
                self.outlet = valveValue
            # Control of inlet valve 
            # Gain2 sets how the pressure rate setpoint depends on the pressure error
            dpdtSet = self.inletGain2 * error
            dpdtSet = min(max(dpdtSet, -self.dpdtMax), self.dpdtMax)
            # Implement an integral controller for the rate of change of pressure
            # Gain1 sets the integral gain
            dError = dpdtSet - dpdt
            delta = self.inletGain1 * dError  # +ve because opening inlet valve increases pressure
            delta = min(max(delta, -self.inletMaxChange), self.inletMaxChange)
            valveValue = self.inlet + delta
            valveValue = min(max(valveValue, self.inletMin), self.inletMax)
            self.inlet = valveValue
        elif self.state == interface.VALVE_CNTRL_SaveAndCloseValvesState:
            # Remember state of valves so they can be restored later 
            if self.state != self.previousState:
                self.savedState = self.previousState
                self.savedInletValue = self.inlet
                self.savedOutletValue = self.outlet
            self.inlet = 0
            self.outlet = 0
        elif self.state == interface.VALVE_CNTRL_RestoreValvesState:
            self.inlet = self.savedInletValue
            self.outlet = self.savedOutletValue
            self.state = self.savedState
        self.userInlet = self.inlet
        self.userOutlet = self.outlet
        if self.outlet >= self.outletMax and self.nonDecreasingCount > 10:
            self.sim.message_puts(interface.LOG_LEVEL_STANDARD, "Check vacuum pump connection, valves closed to protect cavity.")    
            self.state = interface.VALVE_CNTRL_DisabledState
        self.previousState = self.state

    def step(self):
        if self.valveCntrlDelay == 0:
            self.proportionalValveStep()
            self.thresholdTriggerStep()
            # self.valveSequencerStep()
        else:
            self.valveCntrlDelay -= 1
        return interface.STATUS_OK

    def thresholdTriggerStep(self):
        lossPpb = 1000.0 * self.latestLoss
        self.last5.append(lossPpb)
        while len(self.last5) > 5:
            self.last5.popleft()
        # Find median of values in deque
        lossPpb = sorted(self.last5)[len(self.last5)//2]
        # Calculate rate of change of loss
        lossRate = (lossPpb - self.lastLossPpb) / self.deltaT
        self.lastLossPpb = lossPpb
        if self.threshState == interface.VALVE_CNTRL_THRESHOLD_ArmedState:
            # When armed, check if loss is above rising loss threshold and if
            #  rate is below rising loss rate threshold. If both hold, the system
            #  enters the triggered state.
            self.state = interface.VALVE_CNTRL_ManualControlState
            if self.outletTriggeredValue >= 0:
                self.outlet = self.outletTriggeredValue
            if self.inletTriggeredValue >= 0:
                self.inlet = self.inletTriggeredValue
            self.solenoidValves = (self.solenoidValves & ~self.solenoidMask) | (self.solenoidState & self.solenoidMask)
            self.threshState = interface.VALVE_CNTRL_THRESHOLD_TriggeredState

    def valveSequencerStep(self):
        if self.sequenceStep >= 0:
            if self.sequenceStep < interface.NUM_VALVE_SEQUENCE_ENTRIES:
                maskAndValue = valveSequence[sequenceStep].maskAndValue
                dwell = valveSequence[sequenceStep].dwell
                # Zero mask and value means we should stay at the present step
                if maskAndValue != 0:
                    value = maskAndValue & 0xFF
                    maskAndValue >>= 8
                    if self.dwellCount == 0:
                        self.solenoidValves = (self.solenoidValves & ~maskAndValue) | value
                    if self.dwellCount >= dwell:
                        self.sequenceStep += 1
                        self.dwellCount = 0
                    else:
                        self.dwellCount += 1
            else:
                self.sequenceStep = -1