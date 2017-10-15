# Ugly code following!     

import abusliconf
import array
import pymodbus
import serial
import argparse
from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient #initialize a serial RTU client instance
from pymodbus.transaction import ModbusRtuFramer

#import logging
#logging.basicConfig()
##log = logging.getLogger()
#log.setLevel(logging.DEBUG)


baudrate = 38400
parity = 'N'
port = "/dev/ttyUSB0"
unit=0 # the slave unit this request is targeting

IOcffromDevice = [False]*1024
buttonConf = [False]*16
oConfFromDevice = [False]*32
cmdRegisters = [0]*3

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

def readConfs():

	client = ModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout = 0.5)
	try:
		connection = client.connect()
		result0 = client.read_coils(2000,512,unit=unit)
		result1 = client.read_coils(2511,512,unit=unit)
		result2 = client.read_coils(3024,32,unit=unit)
		result3 = client.read_coils(3056,16,unit=unit)
		result4 = client.read_holding_registers(2000,3,unit=unit)
		
		cmdRegisters[1]=int(result4.registers[1])
		cmdRegisters[2]=int(result4.registers[2])
		for x in range(0, 512):
			IOcffromDevice[x] = result0.bits[x]
			IOcffromDevice[x+512] = result1.bits[x]
		for x in range(0, 16):
			buttonConf[x]=result3.bits[x]
		for x in range(0, 32):
			oConfFromDevice[x]=result2.bits[x]
	except:
		print("Modbus error.")
	client.close()

def compare():

	print("Downloading from device "+str(unit))
	readConfs()
	abusliconf.readConfFromFile()
	testResult = 0
	if(IOcffromDevice==abusliconf.ioConf):
		print("input-output-assignments match.")
	else:
		testResult=1
		print("input-output-assignments dont match!")
	if(buttonConf==abusliconf.buttonConf):
		print("button configuration matches")
	else:	
		testResult=1
		print("button configuration doesn't match!")
	if(oConfFromDevice==abusliconf.oConf):
		print("output configuration matches.")
	else:
		testResult=1
		print("output configuration doesn't match!")
	if(abusliconf.longPushThr==cmdRegisters[1]):
		print("longpush threshold matches.")
	else:
		testResult=1
		print("longpush threshold doesn't match!")
	if(abusliconf.timeoutThr==cmdRegisters[2]):
		print("bus timeout threshold matches.")
	else:
		print("bus timeout threshold doesn't match!")
		testResult=1

	if testResult == 1:
		print("ERROR: The device's configuration doesn't match the config file!")
		return False
	else:
		return True

def store():
	client = ModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate)
	try:
		connection = client.connect()
		result4 = client.write_register(2000,17239,unit=unit)
		print("Store: ok")
	except:
		print("Modbus error.")
	client.close()


def upload():
	abusliconf.readConfFromFile()
	client = ModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout=0.5)
	try:
		
		connection = client.connect()
		result0 = client.write_coils(2000,abusliconf.ioConf[0:512],unit=unit)
		result0 = client.write_coils(2512,abusliconf.ioConf[512:1024],unit=unit)
		result2 = client.write_coils(3024,abusliconf.oConf,unit=unit)
		result3 = client.write_coils(3056,abusliconf.buttonConf,unit=unit)
		result4 = client.write_register(2001,abusliconf.longPushThr,unit=unit)
		result4 = client.write_register(2002,abusliconf.timeoutThr,unit=unit)
		print("Upload done.")
	except:
		print("Modbus error during upload.")
	client.close()

parser = argparse.ArgumentParser()

parser.add_argument("command", type=str, help="command to perform. Allowed commands: upload, download, store, compare")
parser.add_argument("address", type=int, help="device address")
parser.add_argument("file", type=str, help="config file source/destination")
args = parser.parse_args()
unit = args.address
abusliconf.filename = args.file
if (args.command == "download"):
	if probe():
		readConfs()
		abusliconf.buttonConf=buttonConf
		abusliconf.ioConf=IOcffromDevice
		abusliconf.oConf=oConfFromDevice
		abusliconf.longPushThr=cmdRegisters[1]
		abusliconf.timeoutThr=cmdRegisters[2]
		abusliconf.writeConfToFile()
		print ("Written to file: "+abusliconf.filename)
	
		if(compare()):
			print("Verification: pass")


elif (args.command == "compare"):
	if probe():
		if compare():
			print("Verification: pass")


elif (args.command == "upload"):
		if probe():
			print("Uploading. Please wait, this might take a couple of seconds..")
			upload()				
			print("Comparing.")
			if(compare()):
				print("Verification: pass")
	

elif (args.command == "store"):
	if probe():
		if(compare()):
			print("Verification: pass")
			store()
		else:
			print("Cannot write to EEPROM!")
		
else:
	print("Invalid command. Allowed commands: upload, download, store, compare")
