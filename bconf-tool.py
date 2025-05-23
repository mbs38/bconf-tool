#!/usr/bin/env python3
import knownendpoints
import abusliconf
import array
import serial
import argparse
import time
import asyncio
import pymodbus
import logging
import pymodbus.client as ModbusClient


unit = None
client: ModbusClient.ModbusBaseClient

async def connect_bus():
    """Run async client."""
    global client
    client = ModbusClient.AsyncModbusSerialClient(
        "/dev/ttyUSB0",
        timeout=0.1,
        retries=0,
        baudrate=38400,
        bytesize=8,
        parity="N",
        stopbits=1,
        reconnect_delay=0.1,
        reconnect_delay_max=0
    )

    await client.connect()
    assert client.connected

async def probe():
    global client
    try:
        result0 = await client.read_coils(2000,count=1,slave=unit)
        return True
    except Exception as e:
        return False


IOcffromDevice = [False]*1024
buttonConf = [False]*16
oConfFromDevice = [False]*32
timerOConfFromDevice = [False]*32
cmdRegisters = [0]*5
timeoutvalsFromDevice = [0]*16
outDefaultsFromDevice = [False]*16
patternSavingFromDeviceShortPush = [False]*16
patternSavingFromDeviceLongPush = [False]*16
fastPwmEnableFromDevice = [False]*16
ultraSlowPwmEnableFromDevice = [False]*16
pushButtonDimmingConfFromDevice = [False]*64
description = ""
debouncetimeFromDevice = 0
version=None
devType=None
SwVersions = knownendpoints.SwVersions
BoardTypes = knownendpoints.BoardTypes


def checkinsanity():
    if abusliconf.debouncetime<8 or abusliconf.debouncetime>25:
        print("ERROR! Debounce time illegal. Must be 7 < debouncetime < 26.")
        return True
    if (abusliconf.debouncetime==25 and abusliconf.longPushThr!=30) or (abusliconf.debouncetime==8 and abusliconf.longPushThr!=100) or (abusliconf.debouncetime!=8 and abusliconf.debouncetime!=25):
        print("WARNING: The debounce time value and the longpush threshold value must fit each other. Well tested working values are:")
        print("debounce time = 8, longpush thr = 100")
        print("debounce time = 25, longpush thr = 30")
        print("From firmware version 22 onward 8/100 is the new standard. If you change these settings and your inputs don't work it's not my problem..")
    return False
        

async def getFeatures():
    global version
    global devType
    version = await getFwVersion()
    if(version >= 60000): #device with fw version 15+ => "extended fw/hw identifiers"
        try:
            result = await client.read_holding_registers(10000,count=3,slave=unit)
            version=int(result.registers[1])
            devType=int(result.registers[2])
            print("Firmware-Version: "+str(version))
             
            if(version>((len(SwVersions)))):
                print("THIS VERSION OF BCONF-TOOL SUPPORTS DEVICES UP TO FIRMWARE VERSION "+str(len(SwVersions))+"!")
                print("THIS DEVICE HAS FIRMWARE VERSION "+str(version)+"! UPDATE BCONF-TOOL!")
            if(devType>(len(BoardTypes)-1)):
                print("THIS VERSION OF BCONF-TOOL DOES NOT SUPPORT THIS DEVICE! UPDATE BCONF-TOOL!")
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

async def getFwVersion():
    try:
        result = await client.read_holding_registers(10000,count=1,slave=unit)
        vers=int(result.registers[0])
    except:
        print("Cannot read FW-Version. Maybe legacy or incompatible device?")
        vers=0
    finally:
        return vers

async def readConfs():
    global version
    result0 = await client.read_coils(2000,count=512,slave=unit)
    result1 = await client.read_coils(2512,count=512,slave=unit)
    result2 = await client.read_coils(3024,count=32,slave=unit)
    result3 = await client.read_coils(3056,count=16,slave=unit)
    if version>11:
        result4 = await client.read_coils(3120,count=32,slave=unit)
        for x in range(0, 16):
            patternSavingFromDeviceShortPush[x]=result4.bits[x]
        for x in range(0, 16):
            patternSavingFromDeviceLongPush[x]=result4.bits[x+16]

    if version < 9:
        result8 = await client.read_holding_registers(2000,count=3,slave=unit)
    else:
        result8 = await client.read_holding_registers(2000,count=5,slave=unit)
    if(version > 2):
        result5 = await client.read_coils(3072,count=32,slave=unit)
        result6 = await client.read_holding_registers(4000,count=16,slave=unit)
        result7 = await client.read_coils(3104,count=16,slave=unit)
        for x in range(0, 32):
                timerOConfFromDevice[x]=result5.bits[x]
        for x in range(0, 16):
                timeoutvalsFromDevice[x]=int(result6.registers[x])
        for x in range(0, 16):
                outDefaultsFromDevice[x]=result7.bits[x]
    if version > 9:
        resultDescr = await client.read_holding_registers(4016,count=8,slave=unit)
        global description
        description=""
        for x in range(0, 8):
            description=description+str(chr(resultDescr.registers[x] & 0xFF))
            description=description+str(chr((resultDescr.registers[x] & 0xFF00)>>8))
        description=description.rstrip(chr(0x00))
    cmdRegisters[1]=int(result8.registers[1])
    cmdRegisters[2]=int(result8.registers[2])
    if version > 8:
        cmdRegisters[3]=int(result8.registers[3])
    for x in range(0, 512):
        IOcffromDevice[x] = result0.bits[x]
        IOcffromDevice[x+512] = result1.bits[x]
    for x in range(0, 16):
        buttonConf[x]=result3.bits[x]
    for x in range(0, 32):
        oConfFromDevice[x]=result2.bits[x]

    if version > 21:
        global debouncetimeFromDevice
        debounce_res = await client.read_holding_registers(4024,count=1,slave=unit)
        debouncetimeFromDevice = int(debounce_res.registers[0])

    if version > 22:
        global fastPwmEnableFromDevice
        global ultraSlowPwmEnableFromDevice
        resPwm = await client.read_coils(3152,count=32,slave=unit)
        for x in range(0,16):
            fastPwmEnableFromDevice[x]=resPwm.bits[x] 
        for x in range(0,16):
            ultraSlowPwmEnableFromDevice[x]=resPwm.bits[x+16]
    if version > 23 and (devType==11 or devType == 9):
        global pushButtonDimmingConfFromDevice
        result9 = await client.read_coils(3200,count=64,slave=unit)
        for x in range(0,64):
            pushButtonDimmingConfFromDevice[x]=result9.bits[x]


async def compare():
    await readConfs()
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
    if version > 21:
        if abusliconf.longPushThr==9999:
            abusliconf.longPushThr=100
    if abusliconf.longPushThr!=9999:    
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
    if version > 8:
        if(abusliconf.brownoutThr==cmdRegisters[3]):
            pass#print("brownout threshold matches. "+"("+str(cmdRegisters[3])+")")
        else:
            print("brownout threshold doesn't match!")
            testResult=1
    if(version>2):
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
    if(version>9):
        if(repr(abusliconf.description)==repr(description)):
            if len(description)>0:
                print("Description: "+"("+description+")")
        else:
            print("description doesn't match!")
            testResult=1
    if version > 11:
        if patternSavingFromDeviceShortPush==abusliconf.patternSavingShort:
            pass
        else:
            print("pattern saving (short push) control bits don't match")
            testResult=1
        if patternSavingFromDeviceLongPush==abusliconf.patternSavingLong:
            pass
        else:
            testResult=1
            print("pattern saving (long push) control bits don't match")
   
    if version > 21:
        if abusliconf.debouncetime==9999:
            abusliconf.debouncetime=8
        if debouncetimeFromDevice==abusliconf.debouncetime:
            pass
        else:
            testResult=1
            print("debounce time does not match")
    
    if version > 22:
        if fastPwmEnableFromDevice==abusliconf.fastPwmEnable:
            pass
        else:
            print("fast pwm settings don't match")
            testResult=1
        if ultraSlowPwmEnableFromDevice==abusliconf.ultraSlowPwmEnable:
            pass
        else:
            print("ultra slow pwm settings don't match")
            testResult=1

    if version > 23:
        if pushButtonDimmingConfFromDevice==abusliconf.pushButtonDimmingConf:
            pass
        else:
            print("push button dimming confs don't match")
            testResult=1

    if testResult == 1:
        print("ERROR: The device's configuration doesn't match the config file!")
        return False
    else:
        return True
    
async def store():
    try:
        result4 = await client.write_register(2000,17239,slave=unit)
        print("Store: ok")
    except:
        print("Modbus error. Store failed.")

async def loadEEPROMcontent():
    print("Trying to load config from EEPROM.")
    try:
        result4 = await client.write_register(2000,17234,slave=unit)
        print("Loading from EEPROM initiated.")
    except:
        print("Modbus error. Loading from EEPROM failed.")


async def upload():
    abusliconf.readConfFromFile()
    
    if len(abusliconf.description)>16:
        print("ERROR! Description in config file too long! Maximum is 16 characters!")
        client.close()
        exit()
    if version>21:
        if abusliconf.debouncetime==9999:
            abusliconf.debouncetime=8
            print("INFO: Setting debouncetime to default value: 8")
        if abusliconf.longPushThr==9999:
            abusliconf.longPushThr=100
            print("INFO: Setting longpush threshold to default value: 100")
        if checkinsanity():
            client.close()
            exit()
    else:
        if abusliconf.longPushThr==9999:
            abusliconf.longPushThr=30
            print("INFO: Setting longpush threshold to default value: 100")

    try:
        result0 = await client.write_coils(2000,abusliconf.ioConf[0:512],slave=unit)
        result0 = await client.write_coils(2512,abusliconf.ioConf[512:1024],slave=unit)
        result2 = await client.write_coils(3024,abusliconf.oConf,slave=unit)
        if(version>2):
            result5 = await client.write_coils(3072,abusliconf.timerOConf,slave=unit)
            result7 = await client.write_coils(3104,abusliconf.outDefaults, slave=unit)
            result6 = await client.write_registers(4000,abusliconf.timervals,slave=unit)
        result3 = await client.write_coils(3056,abusliconf.buttonConf,slave=unit)
        result4 = await client.write_register(2001,abusliconf.longPushThr,slave=unit)
        result4 = await client.write_register(2002,abusliconf.timeoutThr,slave=unit)
        if version > 8:
            result4 = await client.write_register(2003,abusliconf.brownoutThr,slave=unit)
        if version > 9:
            descrAsInts = [0]*8
            for x in range(0, 8):
                if (x*2)<len(abusliconf.description):
                    descrAsInts[x]=int(ord(abusliconf.description[x*2]))
                if (x*2+1)<len(abusliconf.description):
                    descrAsInts[x]=int(descrAsInts[x]|(ord(abusliconf.description[x*2+1])<<8))
            result5 = await client.write_registers(4016,descrAsInts,slave=unit)
        if version > 11:
            result5 = await client.write_coils(3120,abusliconf.patternSavingShort,slave=unit)
            result5 = await client.write_coils(3136,abusliconf.patternSavingLong,slave=unit)
        if version > 21:
            result5 = await client.write_register(4024,abusliconf.debouncetime,slave=unit)
        if version > 22:
            result5 = await client.write_coils(3152,abusliconf.fastPwmEnable,slave=unit)
            result5 = await client.write_coils(3168,abusliconf.ultraSlowPwmEnable,slave=unit)
        if version > 23 and (devType==11 or devType == 9):
            result5 = await client.write_coils(3200,abusliconf.pushButtonDimmingConf,slave=unit)
        print("Upload done.")
    except:
        print("Modbus error during upload.")

async def run():
    global version
    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, help="command to perform. Allowed commands: upload, download, store, compare, eeprom-download")
    parser.add_argument("address", type=int, help="device address")
    parser.add_argument("file", type=str, help="config file source/destination")
    global unit
    args = parser.parse_args()
    unit = args.address
    abusliconf.filename = args.file
    await connect_bus()
    if (args.command == "download"):
        if await probe():
            version = await getFeatures()
            await readConfs()
        abusliconf.buttonConf=buttonConf
        abusliconf.ioConf=IOcffromDevice
        abusliconf.oConf=oConfFromDevice
        abusliconf.timerOConf=timerOConfFromDevice
        abusliconf.longPushThr=cmdRegisters[1]
        abusliconf.timeoutThr=cmdRegisters[2]
        abusliconf.patternSavingLong=patternSavingFromDeviceLongPush
        abusliconf.patternSavingShort=patternSavingFromDeviceShortPush
        if version > 8:
            abusliconf.brownoutThr=cmdRegisters[3]
        if version > 9:
            abusliconf.description=description
        abusliconf.timervals=timeoutvalsFromDevice
        abusliconf.outDefaults=outDefaultsFromDevice


        if version > 21:
            abusliconf.debouncetime=debouncetimeFromDevice
        if version > 22:
            abusliconf.ultraSlowPwmEnable=ultraSlowPwmEnableFromDevice
            abusliconf.fastPwmEnable=fastPwmEnableFromDevice

        if version > 23:
            abusliconf.pushButtonDimmingConf = pushButtonDimmingConfFromDevice

        abusliconf.writeConfToFile()
        print ("Written to file: "+abusliconf.filename)

        if(await compare()):
            print("Verification: pass")


    elif (args.command == "compare"):
        if await probe():
            version= await getFeatures()
            if await compare():
                print("Verification: pass")

    elif(args.command == "eeprom-download"):
        if await probe():
            version = await getFeatures()
            question=str(input('Warning! Configuration stored in RAM will be overwritten with EEPROM content. Continue? (y/n)'))
            if(question=='y'):
                print("Okay.")
                await loadEEPROMcontent()
                time.sleep(2)
                await readConfs()
                abusliconf.buttonConf=buttonConf
                abusliconf.ioConf=IOcffromDevice
                abusliconf.oConf=oConfFromDevice
                abusliconf.timerOConf=timerOConfFromDevice
                abusliconf.longPushThr=cmdRegisters[1]
                abusliconf.timeoutThr=cmdRegisters[2]
                abusliconf.patternSavingLong=patternSavingFromDeviceLongPush
                abusliconf.patternSavingShort=patternSavingFromDeviceShortPush
                if version >8:
                    abusliconf.brownoutThr=cmdRegisters[3]
                abusliconf.timervals=timeoutvalsFromDevice
                abusliconf.outDefaults=outDefaultsFromDevice
                if version > 9:
                    abusliconf.description=description
                if version > 21:
                    abusliconf.debouncetime=debouncetimeFromDevice
                if version > 22:
                    abusliconf.ultraSlowPwmEnable=ultraSlowPwmEnableFromDevice
                    abusliconf.fastPwmEnable=fastPwmEnableFromDevice
                abusliconf.writeConfToFile()
                print ("Writing to file: "+abusliconf.filename)
                if(await compare()):
                    print("Verification: pass")
            else:
                print("Aborting. Configuration in RAM unchanged. Not written to file "+abusliconf.filename+".")

    elif (args.command == "upload"):
        if await probe():
            version=await getFeatures()
            await upload()
            if(await compare()):
                print("Verification: pass")


    elif (args.command == "store"):
        if await probe():
            version= await getFeatures()
            if(await compare()):
                print("Verification: pass")
                await store()
            else:
                print("Cannot write to EEPROM!")

    else:
        print("Invalid command. Allowed commands: upload, download, store, compare, eeprom-download")

    client.close()

if __name__ == "__main__":
    asyncio.run(
        run()
    )