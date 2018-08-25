# Ugly code following!     
import time
import sys
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

def printStates(outs,ins):
    sys.stdout.write("Device address: "+str(unit)+"\n")
    sys.stdout.write("Outputs        Inputs\n")
    for x in range(0,16):
        sys.stdout.write(outs[x])
        if(outs[x]=="On"):
            sys.stdout.write(" ")
        sys.stdout.write("            "+ins[x])
        if(ins[x]=="On"):
            sys.stdout.write(" ")
        sys.stdout.write("\n")
    for x in range(0,18):
        sys.stdout.write("\033[F")

    sys.stdout.flush()
    


def monitor():

	client = ModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate)
	try:
		client = ModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout=0.5)
		connection = client.connect()
                
                while True:
                    try:
                        coils = client.read_coils(0,16,unit=unit)
                        discretes = client.read_discrete_inputs(0,16,unit=unit)
        #                holding0 = client.read_holding_registers(0,16,unit=unit)
                        outs = ["Off"]*16
                        ins = ["Off"]*16
                        for x in range(0,15):
                            if(coils.bits[x] == True):
                                outs[x]="On"

                        for x in range(0,15):
                            if(discretes.bits[x] == True):
                                ins[x]="On"
                        printStates(outs,ins)
                    except:
                        print("Polling error!")
                        outs = ["Err"]*16
                        ins = ["Err"]*16
                    

                        
                    
                client.close()
	except:
		print("Polling error!")
	client.close()

parser = argparse.ArgumentParser()

parser.add_argument("address", type=int, help="device address")
args = parser.parse_args()
unit = args.address



if probe():
	monitor()
