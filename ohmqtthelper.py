#!/usr/bin/env python3
import argparse
import csv


parser = argparse.ArgumentParser(description='Bridge between ModBus and MQTT')
parser.add_argument('--config', required=True, help='Configuration file. Required!')
parser.add_argument('--output', required=True, help='Output item file. File will not be overwritten. New stuff will be added at the end. Required!')
#parser.add_argument('--set-loop-break',default='0.01',type=float, help='Set pause in main polling loop. Defaults to 10ms.')


args=parser.parse_args()

verbosity = 10
#Switch agsBus9Out2 "Warnleuchte: Achtung Aufzeichnung" (Licht) {mqtt="<[mosquitto:modbus/agsBus9/state/warnleuchteZGR:state:ON:True],
#                                                                      <[mosquitto:modbus/agsBus9/state/warnleuchteZGR:state:OFF:False],
#                                                                        >[mosquitto:modbus/agsBus9/set/warnleuchteZGR:command:ON:True],
#                                                                        >[mosquitto:modbus/agsBus9/set/warnleuchteZGR:command:OFF:False]"} 
# Now let's read the config file

outfile = open(str(args.output),"a+")

with open(args.config,"r") as csvfile:
    csvfile.seek(0)
    reader=csv.DictReader(csvfile)
    currentPoller=None
    pollerTopic=None
    pollerType=None
    for row in reader:
        if row["type"]=="poller" or row["type"]=="poll":
            rate = float(row["col6"])
            slaveid = int(row["col2"])
            reference = int(row["col3"])
            size = int(row["col4"])

            if row["col5"] == "holding_register":
                functioncode = 3
                dataType="int16"
                if size>123: #applies to TCP, RTU should support 125 registers. But let's be safe.
                    currentPoller=None
                    if verbosity>=1:
                        print("Too many registers (max. 123). Ignoring poller "+row["topic"]+".")
                    continue
            elif row["col5"] == "coil":
                functioncode = 1
                dataType="bool"
                if size>2000: #some implementations don't seem to support 2008 coils/inputs
                    currentPoller=None
                    if verbosity>=1:
                        print("Too many coils (max. 2000). Ignoring poller "+row["topic"]+".")
                    continue
            elif row["col5"] == "input_register":
                functioncode = 4
                dataType="int16"
                if size>123:
                    currentPoller=None
                    if verbosity>=1:
                        print("Too many registers (max. 123). Ignoring poller "+row["topic"]+".")
                    continue
            elif row["col5"] == "input_status":
                functioncode = 2
                dataType="bool"
                if size>2000:
                    currentPoller=None
                    if verbosity>=1:
                        print("Too many inputs (max. 2000). Ignoring poller "+row["topic"]+".")
                    continue

            else:
                print("Unknown function code ("+row["col5"]+" ignoring poller "+row["topic"]+".")
                currentPoller=None
                continue
            pollerType = row["col5"]
            pollerTopic = row["topic"]
            currentPoller = True
            continue
        elif row["type"]=="reference" or row["type"]=="ref":
            outstring = ""
            if currentPoller is not None:
                if pollerType == "coil" and "w" in row["col3"]:
                    outstring = "\nSwitch "+row["topic"]+" \""+row["topic"]+"\" () "+"{mqtt=\"<[mosquitto:modbus/"+pollerTopic+"/state/"+row["topic"]+":state:ON:True],\n"
                    outstring+= "<[mosquitto:modbus/"+pollerTopic+"/state/"+row["topic"]+":state:OFF:False],\n"
                    outstring+= ">[mosquitto:modbus/"+pollerTopic+"/set/"+row["topic"]+":command:ON:True],\n"
                    outstring+= ">[mosquitto:modbus/"+pollerTopic+"/set/"+row["topic"]+":command:OFF:False]\"}"
                
                if pollerType == "coil" and "w" not in row["col3"] and "r" in row["col3"]:
                    outstring = "\nContact "+row["topic"]+" \""+row["topic"]+"\" () "+"{mqtt=\"<[mosquitto:modbus/"+pollerTopic+"/state/"+row["topic"]+":state:OPEN:True],\n"
                    outstring+= "<[mosquitto:modbus/"+pollerTopic+"/state/"+row["topic"]+":state:CLOSED:False]\"}"
                
                elif pollerType == "holding_register" and "w" not in row["col3"] and "r" in row["col3"]:
                    outstring = "\nNumber "+row["topic"]+" \""+row["topic"]+"\" () "+"{mqtt=\"<[mosquitto:modbus/"+pollerTopic+"/state/"+row["topic"]+":state:default]\"}"
                
                elif pollerType == "input_register" and "r" in row["col3"]:
                    outstring = "\nNumber "+row["topic"]+" \""+row["topic"]+"\" () "+"{mqtt=\"<[mosquitto:modbus/"+pollerTopic+"/state/"+row["topic"]+":state:default]\"}"
                
                elif pollerType == "holding_register" and "w" in row["col3"] and "r" in row["col3"]:
                    outstring = "\nNumber "+row["topic"]+" \""+row["topic"]+"\" () "+"{mqtt=\"<[mosquitto:modbus/"+pollerTopic+"/state/"+row["topic"]+":state:default],\n"
                    outstring+= ">[mosquitto:modbus/"+pollerTopic+"/set/"+row["topic"]+":command:default]\"}"
                
                outfile.write(outstring+"\n")
             


            else:
                print("No poller for reference "+row["topic"]+".")

outfile.close()
