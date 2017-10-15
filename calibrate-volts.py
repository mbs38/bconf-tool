# Ugly code following!     

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

global newAdr

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
	try:
		connection = client.connect()
		oldTick = client.read_holding_registers(1002,1,unit=unit)
		print("Old conversion factor: "+oldTick.registers[0])
		result = client.write_register(1002,1,unit=unit) #write new tick value
		print("Measuring..")
		sleep(2)
		voltReg = client.read_holding_registers(52,1,unit=unit) #measure voltage
		#calculate tick voltage:
		newTick = round(actualVoltage / voltReg.registers[0],0)
		int(newTick)
		print("New conversion factor: "+newTick)
		result = client.write_register(1002,newTick,unit=unit) #write new tick value
		tickReg = client.read_holding_registers(1002,1,unit=unit) #read back tick value
		if tickReg.registers[0] == newTick:
			print("Write: ok")
			result = client.write_register(1001,36745,unit=unit) #send store command
		print("Store: ok")
	except:
		print("Failed!")
	try:
		sleep(0.5)
		result = client.write_register(1001,38559,unit=unit) #read back value from eeprom
		sleep(0.5)
		tickReg = client.read_holding_registers(1002,1,unit=unit) #actually read tick value
		if tickReg.registers[0] == newTick:
			print("Verification: pass")
		else:
			print("Verification Failed!")
	except:
		print("Verification failed!")
	client.close()

parser = argparse.ArgumentParser()

parser.add_argument("address", type=int, help="device's address")
parser.add_argument("voltage", type=int, help="measured voltage at device in millivolts")

args = parser.parse_args()
unit = args.address
actualVoltage = args.voltage
newTick = 40
if probe():
	calibrate()
