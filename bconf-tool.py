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
patternSavingFromDeviceShortPush = [False]*16
patternSavingFromDeviceLongPush = [False]*16
description = ""
global erg
SwVersions = ['-','reading out firmware version','','timer controlled outputs, default output states on startup','-','-','-','-','-','brownout','description','autorest flags','support for 1TE device','group all on instead of pattern saving possible','new firmware/hardware register layout']
BoardTypes = ["unknown","agsBusLi","MonsterHW02","MonsterHW04","HutBasic","WBCv2","VariantWBCv2","AGSomat","HutVertical/1TE","5 channel LED PWM Dimmer"]

client = SerialModbusClient(method = "rtu", port = port, stopbits = 1, bytesize = 8, parity = parity, baudrate = baudrate, timeout=1.0)
try:
    connection = client.connect()
except:
    print("Cannot open serial port. Is "+port+" available?")

def getFeatures():
    version = getFwVersion()
    if(version >= 60000): #device with fw version 15+ => "extended fw/hw identifiers"
        try:
            result = client.read_holding_registers(10000,3,unit=unit)
            version=int(result.registers[1])
            devType=int(result.registers[2])
            print("Firmware-Version: "+str(version))
            print("Hardware/Board-Type: "+BoardTypes[devType])
        except:
            print("Cannot read extended fw/hw identifier.")
            version=0
    elif(version>50000 and version<60000):
        print("Device type: 1TE")
        version=version-50000
    elif(version>40000):
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
    if(version<(len(SwVersions)-1)):
        print("/****************************************/")
        print("LEGACY FIRMWARE! Update device's firmware!")
        print("/****************************************/")
        print("The following features won't be available:")
        for x in range((version+1),len(SwVersions)):
            print(" "+SwVersions[x])
    return version

def probe():
    result0 = client.read_coils(2000,1,unit=unit)
    try:
        result0.string
    except:
        print("Client "+str(unit)+" available.")
        return True
    else:
        print("Client "+str(unit)+" unreachable!")
        return False

def getFwVersion():
    try:
        result = client.read_holding_registers(10000,1,unit=unit)
        vers=int(result.registers[0])
    except:
        print("Cannot read FW-Version. Maybe legacy or incompatible device?")
        vers=0
    finally:
        return vers

def readConfs():
    result0 = client.read_coils(2000,512,unit=unit)
    result1 = client.read_coils(2512,512,unit=unit)
    result2 = client.read_coils(3024,32,unit=unit)
    result3 = client.read_coils(3056,16,unit=unit)
    if erg>11:
        result4 = client.read_coils(3120,32,unit=unit)
        for x in range(0, 16):
            patternSavingFromDeviceShortPush[x]=result4.bits[x]
        for x in range(0, 16):
            patternSavingFromDeviceLongPush[x]=result4.bits[x+16]

    if erg < 9:
        result8 = client.read_holding_registers(2000,3,unit=unit)
    else:
        result8 = client.read_holding_registers(2000,5,unit=unit)
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
    cmdRegisters[1]=int(result8.registers[1])
    cmdRegisters[2]=int(result8.registers[2])
    if erg > 8:
        cmdRegisters[3]=int(result8.registers[3])
    for x in range(0, 512):
    	IOcffromDevice[x] = result0.bits[x]
    	IOcffromDevice[x+512] = result1.bits[x]
    for x in range(0, 16):
    	buttonConf[x]=result3.bits[x]
    for x in range(0, 32):
    	oConfFromDevice[x]=result2.bits[x]
    return erg

def compare():
    readConfs()
    print("Comparing.")
    abusliconf.readConfFromFile()
    if len(abusliconf.description)>16:
        print("ERROR! Description in config file too long! Maximum is 16 characters!")
        client.close()
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
    if erg > 11:
        if patternSavingFromDeviceShortPush==abusliconf.patternSavingShort:
            pass
        else:
            print("pattern saving (short push) control bits don't match")
        if patternSavingFromDeviceLongPush==abusliconf.patternSavingLong:
            pass
        else:
            print("pattern saving (long push) control bits don't match")

    
    if testResult == 1:
        print("ERROR: The device's configuration doesn't match the config file!")
        return False
    else:
        return True
    
def store():
    try:
    	result4 = client.write_register(2000,17239,unit=unit)
    	print("Store: ok")
    except:
    	print("Modbus error. Store failed.")

def loadEEPROMcontent():
    print("Trying to load config from EEPROM.")
    try:
    	result4 = client.write_register(2000,17234,unit=unit)
    	print("Loading from EEPROM initiated.")
    except:
    	print("Modbus error. Loading from EEPROM failed.")


def upload():
    abusliconf.readConfFromFile()
    
    if len(abusliconf.description)>16:
        print("ERROR! Description in config file too long! Maximum is 16 characters!")
        client.close()
        exit()
    try:
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
        if erg > 11:
            result5 = client.write_coils(3120,abusliconf.patternSavingShor,unit=unit)
            result5 = client.write_coils(3136,abusliconf.patternSavingLong,unit=unit)
        print("Upload done.")
    except:
    	print("Modbus error during upload.")

parser = argparse.ArgumentParser()

parser.add_argument("command", type=str, help="command to perform. Allowed commands: upload, download, store, compare, eeprom-download")
parser.add_argument("address", type=int, help="device address")
parser.add_argument("file", type=str, help="config file source/destination")
args = parser.parse_args()
unit = args.address
abusliconf.filename = args.file
if (args.command == "download"):
    if probe():
        erg=getFeatures()
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
        erg=getFeatures()
        if compare():
            print("Verification: pass")

elif(args.command == "eeprom-download"):
    if probe():
        erg=getFeatures()
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
            abusliconf.writeConfToFile()
            print ("Writing to file: "+abusliconf.filename)
            if(compare()):
                print("Verification: pass")
        else:
            print("Aborting. Configuration in RAM unchanged. Not written to file "+abusliconf.filename+".")

elif (args.command == "upload"):
    if probe():
        erg=getFeatures()
        upload()
        if(compare()):
            print("Verification: pass")


elif (args.command == "store"):
    if probe():
        erg=getFeatures()
        if(compare()):
            print("Verification: pass")
            store()
        else:
            print("Cannot write to EEPROM!")

else:
    print("Invalid command. Allowed commands: upload, download, store, compare, eeprom-download")

client.close()
