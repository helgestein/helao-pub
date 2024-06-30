import os
import sys
import numpy as np
import asyncio
import pyHamiltonPSD as PSD
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
from sdc_cyan import config
import time

class HamiltonPSD:
    def __init__(self, psd_conf): #psd_conf = config['psdDriver']
        self.inst = PSD
        self.inst.pumps = []
        self.conf = psd_conf
        self.connect()
        self.inst.definePump('0', self.conf['psd_type'], self.conf['psd_syringe']) # make sure that 1.25 mL syringe is added in util.py and psd.py
        self.cmd4 = self.inst.CommandPSD4(self.inst.CommandPSD4)
        self.cmd = self.inst.Command(self.inst.Command)
        self.initialize()
        print("Pump is successfully initialized")

    def initialize(self):
        self.inst.executeCommand(self.inst.pumps[0], self.cmd.enableHFactorCommandsAndQueries() + self.inst.pumps[0].command.executeCommandBuffer(), True) # enable Hamilton protocol
        time.sleep(0.5)
        self.inst.executeCommand(self.inst.pumps[0], self.cmd.initializeValve() + self.inst.pumps[0].command.executeCommandBuffer(), True) # initialization of the valve
        time.sleep(0.5)
        self.inst.executeCommand(self.inst.pumps[0], self.cmd.initializeSyringeOnly(10) + self.inst.pumps[0].command.executeCommandBuffer(), True) # initialization of the syringe with speed = 10
        time.sleep(0.5)
    
    def connect(self):
        self.inst.connect(self.conf['port'], self.conf['baud'])
        print("Successfully connected to the pump")

    def pump(self, step = 0):
        response = self.inst.executeCommand(self.inst.pumps[0], self.cmd4.absolutePosition(step)+ self.inst.pumps[0].command.executeCommandBuffer(), True)
        return response

    def speed(self, speed = 10):
        response = self.inst.executeCommand(self.inst.pumps[0], self.cmd.setSpeed(speed) + self.inst.pumps[0].command.executeCommandBuffer(), True)
        return response

    #def valve(self, valve_number):
    #    response = self.inst.executeCommand(self.inst.pumps[0], self.cmd.moveValveInShortestDirection(valve_number)+ self.inst.pumps[0].command.executeCommandBuffer()) # valve from 1 to 8 (counter closewise from the syringe)
    #    return response
    
    def valve_angle(self, valve_angle):
        #response = self.inst.executeCommand(self.inst.pumps[0], self.cmd.clockwiseAngularValveMove(valve_angle)+ self.inst.pumps[0].command.executeCommandBuffer(), True) # from 1 (0 deg) to 8 (315 deg)
        response = self.inst.executeCommand(self.inst.pumps[0], self.cmd.shortestDirectAngularValveMove(valve_angle)+ self.inst.pumps[0].command.executeCommandBuffer(), True) # from 1 (0 deg) to 8 (315 deg)
        return response
    
    def parse_message(self, message):
        message = message.strip()
        if '/0' in message and '`' in message and '\x03' in message:
            message = message.replace('/0', '').replace('`', '')
            data = message.split('\x03')[0]
            return data
        else:
            return None
        
    def query_syringe(self):
        pos_syringe = self.inst.executeCommand(self.inst.pumps[0], self.cmd.absoluteSyringePosition(), True) # abs syringe position
        return self.parse_message(pos_syringe)
    
    def query_valve(self):
        pos_valve = self.inst.executeCommand(self.inst.pumps[0], self.cmd.valveNumericalPositionQuery(), True)
        return self.parse_message(pos_valve)

    def reset(self):
        response = self.inst.executeCommand(self.inst.pumps[0], self.cmd.resetPSD(), True)
        return response

    def disconnect(self):
        self.reset()
        self.inst.disconnect()
        print("Successfully disconnected from the pump")
