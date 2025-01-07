#!/usr/bin/env python3
import argparse
import asyncio
import pymodbus
import logging
import pymodbus.client as ModbusClient


newAdr = None
unit = None
client: ModbusClient.ModbusBaseClient

async def run_async_simple_client():
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

    client.set_max_no_responses(0xFFFFFFFF)
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

async def chAdr():
    try:
        adrReg = await client.read_holding_registers(1000,count=1,slave=unit)
        result = await client.write_register(1000,newAdr,slave=unit)        
        adrReg = await client.read_holding_registers(1000,count=1,slave=unit)
        if adrReg.registers[0] == newAdr:
            print("Write: ok")
            result = await client.write_register(1001,16727,slave=unit)        
        print("Store: ok")
    except:
        print("Failed!")
    try:
        adrReg = await client.read_holding_registers(1000,count=1,slave=newAdr)
        print("Verification: pass")
        print("New address: "+str(newAdr))
    except:
        print("Verification failed!")

async def run():
    logger = logging.getLogger()
    logging.disable(logging.CRITICAL)
    await run_async_simple_client()
    await probe()
    await chAdr()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("address", type=int, help="device's current address")
    parser.add_argument("newAddress", type=int, help="new device address")
    args = parser.parse_args()
    unit = args.address
    newAdr = args.newAddress
    asyncio.run(
        run()
    )