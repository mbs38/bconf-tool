# Ugly code following!     

import abusliconf
import array
import serial
import argparse
import time

from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as SerialModbusClient
from pymodbus.client.sync import ModbusTcpClient as TCPModbusClient
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
timerOConfFromDevice = [False]*32
cmdRegisters = [0]*5
timeoutvalsFromDevice = [0]*16
outDefaultsFromDevice = [False]*16
patternSavingFromDevice = [False]*16
description = ""
global erg
SwVersions = ['','reading out firmware version','','timer controlled outputs, default output states on startup','','','','','','brownout','description','autorest flags','group all on instead of pattern saving possible']

def getFeatures(version):
        if(version>40000):
		version=version-40000
		print("SPECIAL device. Custom HW and/or software!")
        elif(version>30000):
		version=version-30000
		print("Device type is: Li")
	elif(version>20000):
		version=version-20000
		print("Device type is: Hut")
	else:
		if(version>10000):
			version=version-10000
			print("Device type is: wbcv2")
		else:
			print("Unknown device!")
			version=0
	print("Software version: "+str(version))
	if(version<(len(SwVersions)-1)):
		print("/****************************************/")
		print("LEGACY FIRMWARE! Update device's firmware!")
		print("/****************************************/")
		print("The following features won't be available:")
		for x in range((version+1),len(SwVersions)):
			print(" "+SwVersions[x])
	return version

def probe():
	try:
		client = SerialModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout=0.5)
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
			print("Client "+str(unit)+" available.")
			return True
		else:
			client.close()
			print("Client "+str(unit)+" unreachable!")
			return False

def getFwVersion():
	client = SerialModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout = 0.5)
	try:
		result = client.read_holding_registers(10000,1,unit=unit)
		vers=int(result.registers[0])
		print("Firmware-Version: "+str(vers))
	except:
		print("Cannot read FW-Version. Maybe legacy device?")
		vers=0
	finally:
		client.close()
		return vers

def readConfs():
	client = SerialModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout = 0.5)
	try:
		connection = client.connect()
		result0 = client.read_coils(2000,512,unit=unit)
		result1 = client.read_coils(2512,512,unit=unit)
		result2 = client.read_coils(3024,32,unit=unit)
		result3 = client.read_coils(3056,16,unit=unit)
                if erg>11:
                    result4 = client.read_coils(3072,16,unit=unit)
		    for x in range(0, 16):
		        patternSavingFromDevice[x]=result4.bits[x]

                if erg < 9:
                    result4 = client.read_holding_registers(2000,3,unit=unit)
                else:
		    result4 = client.read_holding_registers(2000,5,unit=unit)
                if(erg > 2):
			result5 = client.read_coils(3072,32,unit=unit)
			result6 = client.read_holding_registers(4000,16,unit=unit)		
			result7 = client.read_coils(3104,16,unit=unit)
			for x in range(0, 32):
				timerOConfFromDevice[x]=result5.bits[x]
			for x in range(0, 16):
				timeoutvalsFromDevice[x]=int(result6.registers[x])
			for x in range(0, 16):
				outDefaultsFromDevice[x]=result7.bits[x]
                if erg > 9:
			resultDescr = client.read_holding_registers(4016,8,unit=unit)
                        global description
                        description=""
                        for x in range(0, 8):
                                description=description+str(chr(resultDescr.registers[x] & 0xFF))
                                description=description+str(chr((resultDescr.registers[x] & 0xFF00)>>8))
                        description=description.rstrip(chr(0x00))
                cmdRegisters[1]=int(result4.registers[1])
		cmdRegisters[2]=int(result4.registers[2])
                if erg > 8:
                    cmdRegisters[3]=int(result4.registers[3])
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
	return erg

def compare():

	readConfs()
	abusliconf.readConfFromFile()
        if len(abusliconf.description)>16:
                print("ERROR! Description in config file too long! Maximum is 16 characters!")
                exit()

	testResult = 0
	if(IOcffromDevice==abusliconf.ioConf):
		pass#print("input-output-assignments match.")
	else:
		testResult=1
		print("input-output-assignments dont match!")
	if(buttonConf==abusliconf.buttonConf):
		pass#print("button configuration matches")
	else:	
		testResult=1
		print("button configuration doesn't match!")
	if(oConfFromDevice==abusliconf.oConf):
		pass#print("output configuration matches.")
	else:
		testResult=1
		print("output configuration doesn't match!")
	if(abusliconf.longPushThr==cmdRegisters[1]):
		pass#print("longpush threshold matches. "+"("+str(cmdRegisters[1])+")")
	else:
		testResult=1
		print("longpush threshold doesn't match!")
	if(abusliconf.timeoutThr==cmdRegisters[2]):
		pass#print("bus timeout threshold matches. "+"("+str(cmdRegisters[2])+")")
	else:
		print("bus timeout threshold doesn't match!")
		testResult=1
        if erg > 8:
                if(abusliconf.brownoutThr==cmdRegisters[3]):
	    	        pass#print("brownout threshold matches. "+"("+str(cmdRegisters[3])+")")
	        else:
	                print("brownout threshold doesn't match!")
		        testResult=1
        if(erg>2):
		if(timerOConfFromDevice==abusliconf.timerOConf):
			pass#print("timer output configuration matches.")
		else:
			testResult=1
			print("timer output configuration doesn't match!")
		if(abusliconf.timervals==timeoutvalsFromDevice):
			pass#print("output timeout values match.")
		else:
			print("output timeout values doesn't match!")
			testResult=1
		if(outDefaultsFromDevice==abusliconf.outDefaults):
			pass#print("output default states match.")
		else:
			print("output default states don't match!")
			testResult=1
        if(erg>9):
                if(repr(abusliconf.description)==repr(description)):
                    print("Description: "+"("+description+")")
	        else:
		        print("description doesn't match!")
		        testResult=1       
        
        
        if testResult == 1:
		print("ERROR: The device's configuration doesn't match the config file!")
		return False
	else:
		return True

def store():
	client = SerialModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate)
	try:
		connection = client.connect()
		result4 = client.write_register(2000,17239,unit=unit)
		print("Store: ok")
	except:
		print("Modbus error. Store failed.")
	client.close()

def loadEEPROMcontent():
	print("Trying to load config from EEPROM.")
	client = SerialModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate)
	try:
		connection = client.connect()
		result4 = client.write_register(2000,17234,unit=unit)
		print("Loading from EEPROM initiated.")
	except:
		print("Modbus error. Loading from EEPROM failed.")
	client.close()


def upload():
	abusliconf.readConfFromFile()
	
        if len(abusliconf.description)>16:
            print("ERROR! Description in config file too long! Maximum is 16 characters!")
            exit()

	
        client = SerialModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout=0.5)
        try:
		connection = client.connect()
		result0 = client.write_coils(2000,abusliconf.ioConf[0:512],unit=unit)
		result0 = client.write_coils(2512,abusliconf.ioConf[512:1024],unit=unit)
		result2 = client.write_coils(3024,abusliconf.oConf,unit=unit)
		if(erg>2):
			result5 = client.write_coils(3072,abusliconf.timerOConf,unit=unit)
                        result7 = client.write_coils(3104,abusliconf.outDefaults, unit=unit)
			result6 = client.write_registers(4000,abusliconf.timervals,unit=unit)
		result3 = client.write_coils(3056,abusliconf.buttonConf,unit=unit)
		result4 = client.write_register(2001,abusliconf.longPushThr,unit=unit)
		result4 = client.write_register(2002,abusliconf.timeoutThr,unit=unit)
                if erg > 8:
		        result4 = client.write_register(2003,abusliconf.brownoutThr,unit=unit)
                if erg > 9:
                        descrAsInts = [0]*8
                        for x in range(0, 8):
                                if (x*2)<len(abusliconf.description):
                                        descrAsInts[x]=int(ord(abusliconf.description[x*2]))
                                if (x*2+1)<len(abusliconf.description):
                                        descrAsInts[x]=int(descrAsInts[x]|(ord(abusliconf.description[x*2+1])<<8))
                        result5 = client.write_registers(4016,descrAsInts,unit=unit)
		print("Upload done.")
	except:
		print("Modbus error during upload.")
	client.close()

parser = argparse.ArgumentParser()

parser.add_argument("command", type=str, help="command to perform. Allowed commands: upload, download, store, compare, eeprom-download")
parser.add_argument("address", type=int, help="device address")
parser.add_argument("file", type=str, help="config file source/destination")
args = parser.parse_args()
unit = args.address
abusliconf.filename = args.file
if (args.command == "download"):
	if probe():
		erg=getFeatures(getFwVersion())
		readConfs()
		abusliconf.buttonConf=buttonConf
		abusliconf.ioConf=IOcffromDevice
		abusliconf.oConf=oConfFromDevice
		abusliconf.timerOConf=timerOConfFromDevice
		abusliconf.longPushThr=cmdRegisters[1]
		abusliconf.timeoutThr=cmdRegisters[2]
                if erg > 8: 
                        abusliconf.brownoutThr=cmdRegisters[3]
                if erg > 9:
                        abusliconf.description=description
		abusliconf.timervals=timeoutvalsFromDevice
		abusliconf.outDefaults=outDefaultsFromDevice
		abusliconf.writeConfToFile()
		print ("Written to file: "+abusliconf.filename)
	
		if(compare()):
			print("Verification: pass")


elif (args.command == "compare"):
	if probe():
		erg=getFeatures(getFwVersion())
		if compare():
			print("Verification: pass")

elif(args.command == "eeprom-download"):
	if probe():
		erg=getFeatures(getFwVersion())
		question=str(raw_input('Warning! Configuration stored in RAM will be overwritten with EEPROM content. Continue? (y/n)'))
		if(question=='y'):
			print("Okay.")
			loadEEPROMcontent()
			time.sleep(2)		
			readConfs()
			abusliconf.buttonConf=buttonConf
			abusliconf.ioConf=IOcffromDevice
			abusliconf.oConf=oConfFromDevice
			abusliconf.timerOConf=timerOConfFromDevice
			abusliconf.longPushThr=cmdRegisters[1]
			abusliconf.timeoutThr=cmdRegisters[2]
                        if erg >8:
			        abusliconf.brownoutThr=cmdRegisters[3]
			abusliconf.timervals=timeoutvalsFromDevice
			abusliconf.outDefaults=outDefaultsFromDevice
                        if erg > 9:
                                abusliconf.description=description
                        #abusliconf.brownoutThr=brownoutThr
			abusliconf.writeConfToFile()
			print ("Writing to file: "+abusliconf.filename)
			if(compare()):
				print("Verification: pass")
		else:
			print("Aborting. Configuration in RAM unchanged. Not written to file "+abusliconf.filename+".")

elif (args.command == "upload"):
		if probe():
			erg=getFeatures(getFwVersion())
			upload()				
			print("Comparing.")
			if(compare()):
				print("Verification: pass")
	

elif (args.command == "store"):
	if probe():
		erg=getFeatures(getFwVersion())
		if(compare()):
			print("Verification: pass")
			store()
		else:
			print("Cannot write to EEPROM!")
		
else:
	print("Invalid command. Allowed commands: upload, download, store, compare, eeprom-download")
