#!/usr/bin/env python3
import argparse
import asyncio
import pymodbus
import logging
import pymodbus.client as ModbusClient
import sys


global oldDiscretes
global oldCoils
global coilsChanged
global discretesChanged
port = None
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
    except Exception as e:
        print(e)
        print("Client not reachable, exitting.")
        exit()

def printStates(outs,ins):
    sys.stdout.write("\n")
    sys.stdout.write("Device address: "+str(unit)+"\n")
    sys.stdout.write("Outputs        Inputs\n")
    for x in range(0,16):
        sys.stdout.write(outs[x])
        if(outs[x]=="On "):
            sys.stdout.write(" ")
        sys.stdout.write("            "+ins[x])
        if(ins[x]=="On "):
            sys.stdout.write(" ")
        sys.stdout.write("\n")
    for x in range(0,19):
        sys.stdout.write("\033[F")

    sys.stdout.flush()


async def monitor():
    try:            
        oldCoils = await client.read_coils(0,count=16,slave=unit)
        oldDiscretes = await client.read_discrete_inputs(0,count=16,slave=unit)
        discretesChanged = [False]*16
        coilsChanged = [False]*16
        
        blahvar = 0
        killvar = 1
        while killvar == 1:
            if True:#try:
                coils = await client.read_coils(0,count=16,slave=unit)
                discretes = await client.read_discrete_inputs(0,count=16,slave=unit)
                outs = ["Off"]*16
                ins = ["Off"]*16
                for x in range(0,16):
                    if(coils.bits[x] != oldCoils.bits[x]):
                        coilsChanged[x] = True
                    if(coils.bits[x] == True):
                        outs[x]="On "
                    if(coilsChanged[x] == True):
                        outs[x]=u"\u001b[31m"+outs[x]+u"\u001b[0m"
                for x in range(0,16):
                    if(discretes.bits[x] != oldDiscretes.bits[x]):
                        discretesChanged[x] = True
                    if(discretes.bits[x] == True):
                        ins[x]="On "
                    if(discretesChanged[x] == True):
                        ins[x]=u"\u001b[31m"+ins[x]+u"\u001b[0m"    
            printStates(outs,ins)
        client.close()
    except Exception as e:
            print("Polling error: "+str(e))
    client.close()

async def run():
    await connect_bus()
    await probe()
    await monitor()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("address", type=int, help="device address")
    parser.add_argument("port", type=str, help="serial port like /dev/ttyUSB0")
    args = parser.parse_args()
    unit = args.address
    port = args.port
    asyncio.run(
        run()
    )