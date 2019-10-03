# Ugly code following!     

import sys
import pymodbus
import serial
import argparse
from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient #initialize a serial RTU client instance
from pymodbus.transaction import ModbusRtuFramer

#import logging
##logging.basicConfig()
#log = logging.getLogger()
#log.setLevel(logging.DEBUG)

baudrate = 38400
parity = 'N'
port = "/dev/ttyUSB0"
failed = 0

def dassert(deferred, callback):
    def _assertor(value):
        assert(value)
    deferred.addCallback(lambda r: _assertor(callback(r)))
    deferred.addErrback(lambda  _: _assertor(False))
try:
	client = ModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout=0.1)

	for x in range(1,255):
		sys.stdout.write("\r"+str(x))
		sys.stdout.flush()
		connection = client.connect()
		outp=client.read_coils(0,1,unit=x)
		try:
			blah=outp.bits[0]
			sys.stdout.write("\b\b\b")
			sys.stdout.flush()
			sys.stdout.write("Device found, address: "+str(x))
			try:
				fw = client.read_holding_registers(10000,1,unit=x)
                                fw = fw.registers[0]
				version = 0
                                if(fw>60000):
                                        print("UNKNOWN DEVICE TYPE!")
                                elif(fw>50000):
		                        version=fw-50000
                                elif(fw>40000):
		                        print("SPECIAL device. Custom HW and/or software!")
		                        version=fw-40000
                                elif(fw>30000):
		                        version=fw-30000
	                        elif(fw>20000):
		                        version=fw-20000
                                elif(fw>10000):
			                version=fw-10000

                                    
                                sys.stdout.write(", version-id: "+str(fw))
				if(fw>50000 and fw<60000):
					sys.stdout.write(", device type: 1TE")
				if(fw>40000 and fw<50000):
					sys.stdout.write(", device type: UNKNOWN!")
				if(fw>30000 and fw<40000):
					sys.stdout.write(", device type: Li")
				if(fw>20000 and fw<30000):
					sys.stdout.write(", device type: Hut")
				if(fw>10000 and fw<20000):
					sys.stdout.write(", device type: WBCv2")
                                if version>9:
                                        resultDescr = client.read_holding_registers(4016,8,unit=x)
                                        description=""
                                        for x in range(0, 8):
                                                description=description+str(chr(resultDescr.registers[x] & 0xFF))
                                                description=description+str(chr((resultDescr.registers[x] & 0xFF00)>>8))
                                                description=description.rstrip(chr(0x00))
   
					sys.stdout.write(", Description: "+description)
				sys.stdout.write("\n")
			except:
				sys.stdout.write("\n")
			sys.stdout.flush()
		except:
			failed=failed+1
	sys.stdout.write("\b\b\b")
	sys.stdout.write("Scan finished.")
	sys.stdout.write("\n")
	sys.stdout.flush()
except:
	print("Serial error. Is "+port+" available?")

client.close()
