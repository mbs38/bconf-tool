# Ugly code following!     

import time
import math
import array
import pymodbus
import serial
import argparse
from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient #initialize a serial RTU client instance
from pymodbus.transaction import ModbusRtuFramer

#import logging
#logging.basicConfig()
#log = logging.getLogger()
#log.setLevel(logging.DEBUG)

baudrate = 38400
parity = 'N'
port = "/dev/ttyUSB0"

global actualVoltage

def probe():
	try:
		client = ModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout=0.5)
		connection = client.connect()
		result0 = client.read_coils(2000,1,unit=unit)
		client.close()
	except:
		print ("Serial error. Is "+port+" available?")
		client.close()
	else:
		try:
			result0.string
		except:
			client.close()
			print("Client exists.")
			return True
		else:
			client.close()
			print("Client unreachable!")
			return False



def calibrate():
	
		client = ModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate)
		connection = client.connect()
		result = client.write_register(1001,38559,unit=unit) #read back value from eeprom
		time.sleep(3)
		oldTick = client.read_holding_registers(1002,1,unit=unit)
		print("Old conversion factor: "+str(oldTick.registers[0]))
		oldVoltage = client.read_holding_registers(52,1,unit=unit)
		print("Measured voltage according to client (millivolts): "+str(oldVoltage.registers[0]))
		result = client.write_register(1002,1,unit=unit) #write new tick value
		result = client.write_register(1001,39559,unit=unit) 
		print("Set conversion factor to 1, measuring..")
		time.sleep(3)
		voltReg = client.read_holding_registers(52,1,unit=unit) #measure voltage
		#calculate tick voltage:
		newTick = int(round(actualVoltage / voltReg.registers[0],0))
		print("New conversion factor: "+str(newTick))
		result = client.write_register(1002,newTick,unit=unit) #write new tick value
		tickReg = client.read_holding_registers(1002,1,unit=unit) #read back tick value
		if tickReg.registers[0] == newTick:
			print("Write: ok")
			try:
				result = client.write_register(1001,36745,unit=unit) #send store command
				print("Store: ok")
			except:
				print("Store failed!")
		try:
			time.sleep(1)
			result = client.write_register(1001,38559,unit=unit) #read back value from eeprom
			time.sleep(1)
			tickReg = client.read_holding_registers(1002,1,unit=unit) #actually read tick value
			if tickReg.registers[0] == newTick:
				print("Verification: pass")
				
				newMeasVoltage = client.read_holding_registers(52,1,unit=unit)
				print("Measured voltage according to client (millivolts): "+str(newMeasVoltage.registers[0]))
			else:
				print("Verification Failed!")
		except:
			print("Verification failed!")
		client.close()
	
#		print("Failed!")
#		client.close()

parser = argparse.ArgumentParser()

parser.add_argument("address", type=int, help="device's address")
parser.add_argument("voltage", type=int, help="measured voltage at device in millivolts")

args = parser.parse_args()
unit = args.address
actualVoltage = args.voltage
if probe():
	try:
		calibrate()
	except:
		print("Failed!")
