# Ugly code following!     

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
			return True
		else:
			client.close()
			print("Client unreachable!")
			return False



def chAdr():

	client = ModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate)
	try:
		connection = client.connect()
		adrReg = client.read_holding_registers(1000,1,unit=unit)
		result = client.write_register(1000,newAdr,unit=unit)		
		adrReg = client.read_holding_registers(1000,1,unit=unit)
		if adrReg.registers[0] == newAdr:
			print("Write: ok")
			result = client.write_register(1001,16727,unit=unit)		
		print("Store: ok")
	except:
		print("Failed!")
	try:
		adrReg = client.read_holding_registers(1000,1,unit=newAdr)
		print("Verification: pass")
		print("New address: "+str(newAdr))
	except:
		print("Verification failed!")
	client.close()

parser = argparse.ArgumentParser()

parser.add_argument("address", type=int, help="device's current address")
parser.add_argument("newAddress", type=int, help="new device address")
args = parser.parse_args()
unit = args.address
newAdr = args.newAddress
if probe():
	chAdr()
