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
	client = ModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout=0.05)

	for x in range(1,255):
		sys.stdout.write("\r"+str(x))
		sys.stdout.flush()
		connection = client.connect()
		outp=client.read_coils(0,1,unit=x)
		try:
			blah=outp.bits[0]
			sys.stdout.write("\b\b\b")
			sys.stdout.flush()
			print("Device found, address: "+str(x))
		except:
			failed=failed+1
	sys.stdout.write("\b\b\b")
	sys.stdout.write("Scan finished.")
	sys.stdout.write("\n")
	sys.stdout.flush()
except:
	print("Serial error. Is "+port+" available?")

client.close()
