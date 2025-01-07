#!/usr/bin/env python3
import sys
import argparse
import knownendpoints
import asyncio
import pymodbus
import logging

baudrate = 38400
parity = 'N'
port = "/dev/ttyUSB0"
failed = 0
timeout = 1
BoardTypes = knownendpoints.BoardTypes

import pymodbus.client as ModbusClient
client: ModbusClient.ModbusBaseClient
debug = False
async def run_async_simple_client():
    """Run async client."""
    # activate debugging
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

    client.set_max_no_responses(0xFFFFFFFF)
    await client.connect()
    assert client.connected

async def run_scan():
    for x in range(1,254):
        sys.stdout.write("\r"+str(x))
        sys.stdout.flush()
        try:
            outp = await client.read_coils(1,count=1,slave=x)
            sys.stdout.write("\b\b\b")
            sys.stdout.flush()
            sys.stdout.write("Device found, address: "+str(x))
            sys.stdout.flush()
        except Exception as e:
            continue
        try:
            fw = await client.read_holding_registers(10000,count=1,slave=x)
            fw = fw.registers[0]
            if(fw >= 60000): #device with fw version 15+ => "extended fw/hw identifiers"
                try:
                    result = await client.read_holding_registers(10000,count=3,slave=x)
                    version=int(result.registers[1])
                    devType=int(result.registers[2])
                    sys.stdout.write(" Firmware-Version: "+str(version))
                    sys.stdout.write(" Hardware/Board-Type: "+BoardTypes[devType])
                except:
                    sys.stdout.write(" Cannot read extended fw/hw identifier.")
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
                resultDescr = await client.read_holding_registers(4016,count=8,slave=x)
                description=""
                for y in range(0, 8):
                    description=description+str(chr(resultDescr.registers[y] & 0xFF))
                    description=description+str(chr((resultDescr.registers[y] & 0xFF00)>>8))
                    description=description.rstrip(chr(0x00))
                if len(description)>0:
                    sys.stdout.write(", Description: \""+description+"\"")
            if version>19:
                result = await client.read_holding_registers(10003,count=3,slave=x)
                year=int(result.registers[0])>>8
                month=int(result.registers[0])&0x00FF
                day=int(result.registers[1])>>8
                hour=int(result.registers[1])&0x00FF
                minutes=int(result.registers[2])>>8
                seconds=int(result.registers[2])&0x00FF
                sys.stdout.write(", Buildtime: "+str(day)+"."+str(month)+"."+str(year)+" "+str(hour)+":"+str(minutes)+":"+str(seconds))
            if version>20:
                systime = await client.read_input_registers(0,4,slave=x)
                sys.stdout.write(", Uptime: "+str(systime.registers[0])+" days "+str(systime.registers[1])+":"+str(systime.registers[2])+":"+str(systime.registers[3]))
            sys.stdout.write("\n")
        except:
            sys.stdout.write("\n")
        sys.stdout.flush()
    sys.stdout.write("\b\b\b")
    sys.stdout.write("Scan finished.")
    sys.stdout.write("\n")
    sys.stdout.flush()
     
    client.close()

async def run():
    logger = logging.getLogger()
    logging.disable(logging.CRITICAL)
    await run_async_simple_client(),
    await run_scan()

if __name__ == "__main__":
    asyncio.run(
        run()
    )

exit()

client.close()
