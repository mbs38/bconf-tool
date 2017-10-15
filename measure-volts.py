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
		time.sleep(2)
		oldVoltage = client.read_holding_registers(52,1,unit=unit)
		print("Measured voltage according to client (millivolts): "+str(oldVoltage.registers[0]))
		client.close()
	
#		print("Failed!")
#		client.close()

parser = argparse.ArgumentParser()

parser.add_argument("address", type=int, help="device's address")

args = parser.parse_args()
unit = args.address
if probe():
	calibrate()
