import configparser


outputList=[]
sectionList=[]
for x in range(0,16):
        sectionList.append("Input"+str(x))
        outputList.append("Output"+str(x))
#rint(sectionList)
        

config = configparser.ConfigParser()


buttonConf=[False]*16
ioConf=[False]*1024
oConf=[False]*32
timerOConf=[False]*32
timervals=[0]*16
longPushThr=0
timeoutThr=0
brownoutThr=0
description="none"
outDefaults=[False]*16
patternSavingShort=[False]*16
patternSavingLong=[False]*16
fastPwmEnable = [False]*16
ultraSlowPwmEnable = [False]*16
debouncetime=0

def readConfFromFile():
        global filename
        global timeoutThr
        global longPushThr
        global brownoutThr
        global description
        global debouncetime
        global fastPwmEnable
        global ultraSlowPwmEnable
        config.read(filename)
        try:
                #global longPushThr
                longPushThr = int(config.get('Global', 'long-push-threshold'))
                #print("Long-push-thr: "+str(longPushThr))
        except:
                #global longPushThr
                longPushThr = 9999
                #print("no long push threshold in config file")
        try:
                #global longPushThr
                debouncetime = int(config.get('Global', 'debounce-time'))
                #print("Long-push-thr: "+str(longPushThr))
        except:
                #global longPushThr
                debouncetime = 9999
                #print("no long push threshold in config file")

        try:    
        #       global timeoutThr
                timeoutThr = int(config.get('Global', 'timeout'))
                #print("Timeout: "+str(timeoutThr))
        except:
        #       global timeoutThr
                timeoutThr = 0
                #print("no timeout thresold in config file")

        try:
                brownoutThr = int(config.get('Global', 'brownout-threshold'))
        except:
                brownoutThr = 0
        
        try:
                description = str(config.get('Global', 'description')).rstrip(" ")
        except:
                description = "none"

        for sections in sectionList:
                try:
                        shortOn = list(map(int,config.get(sections, 'short-on').split(',')))
                #       print("Section: "+str(sectionList.index(sections))+", shortOn: "+str(shortOn))
                except:
                        shortOn=[]
                try:
                        shortOff = list(map(int,config.get(sections, 'short-off').split(',')))
                #       print("Section: "+str(sectionList.index(sections))+", shortOff: "+str(shortOff))
                except:
                        shortOff=[]
                try:
                        longOn = list(map(int,config.get(sections, 'long-on').split(',')))
                #       print("Section: "+str(sectionList.index(sections))+", longOn: "+str(longOn))
                except:
                        longOn=[]
                try:
                        longOff = list(map(int,config.get(sections, 'long-off').split(',')))
                #       print("Section: "+str(sectionList.index(sections))+", longOff: "+str(longOff))
                except:
                        longOff=[]
                try:
                        switchType = config.get(sections, 'switch-type')
                except:
                        switchType = "push-button"
                try:
                        if(config.get(sections, 'pattern-saving-shortpush')=='on'):
                                patternSavingShort[sectionList.index(sections)]=True
                except:
                        patternSavingShort[sectionList.index(sections)]=False

                try:
                        if(config.get(sections, 'pattern-saving-longpush')=='on'):
                                patternSavingLong[sectionList.index(sections)]=True
                except:
                        patternSavingLong[sectionList.index(sections)]=False
                
                ########################### Arrange data, copy into boolean list ###############################
                if sectionList.index(sections)>7:
                        skip = 512
                        multiplier=(sectionList.index(sections)-8)*8
                else:
                        skip = 0
                        multiplier=(sectionList.index(sections))*8

                for x in range(0,len(shortOn)):
                        if (shortOn[x] < 8):
                                bitLocation=shortOn[x]+multiplier+skip
                                ioConf[bitLocation]=True        
                        else:
                                if(shortOn[x] > 15):
                                        raise Exception("Output doesn't exist")
                                bitLocation=shortOn[x]+multiplier+skip+128-8
                                ioConf[bitLocation]=True
                #       print(str(shortOn[x])+": Bit"+str(bitLocation))
                
                for x in range(0,len(shortOff)):
                        if (shortOff[x] < 8):
                                bitLocation=shortOff[x]+multiplier+64+skip
                                ioConf[bitLocation]=True        
                        else:
                                bitLocation=shortOff[x]+multiplier+64+128+skip-8
                                ioConf[bitLocation]=True
                #       print(str(shortOff[x])+": Bit"+str(bitLocation))
                

                for x in range(0,len(longOn)):
                        if (longOn[x] < 8):
                                bitLocation=longOn[x]+256+multiplier+skip
                                ioConf[bitLocation]=True        
                        else:
                                if(longOn[x] > 15):
                                        raise Exception("Output doesn't exist")
                                bitLocation=longOn[x]+256+multiplier+skip+128-8
                                ioConf[bitLocation]=True
                #       print(str(longOn[x])+": Bit"+str(bitLocation))

                for x in range(0,len(longOff)):
                        if (longOff[x] < 8):
                                bitLocation=longOff[x]+256+64+multiplier+skip
                                ioConf[bitLocation]=True        
                        else:
                                if(longOff[x] > 15):
                                        raise Exception("Output doesn't exist")
                                bitLocation=longOff[x]+256+multiplier+64+skip+128-8
                                ioConf[bitLocation]=True
                #       print(str(longOff[x])+": Bit"+str(bitLocation))
                
                if switchType == "toggle-switch":
                #       print("Input"+str(sectionList.index(sections))+": Schalter")
                        buttonConf[sectionList.index(sections)]=True
                #else:
                #       print("Input"+str(sectionList.index(sections))+": Taster")
                
        for outputsection in outputList:
                try:
                        oConfStr = config.get(outputsection, 'input-controlled')
                except:
                        oConfStr=[]
                if oConfStr == 'timeout-only':
                        oConf[outputList.index(outputsection)+16]=True
                elif oConfStr == 'always':
                        oConf[outputList.index(outputsection)]=True
                        oConf[outputList.index(outputsection)+16]=True

                try:
                        oConfStr = config.get(outputsection, 'timer-controlled')
                except:
                        oConfStr=[]
                if oConfStr == 'timeout-only':
                        timerOConf[outputList.index(outputsection)+16]=True
                elif oConfStr == 'always':
                        timerOConf[outputList.index(outputsection)]=True
                        timerOConf[outputList.index(outputsection)+16]=True
                
                try:
                        timervals[outputList.index(outputsection)] = int(config.get(outputsection, 'timeout-value'))
                except:
                        timervals[outputList.index(outputsection)] = 0
                if timervals[outputList.index(outputsection)] > 65535:
                        timervals[outputList.index(outputsection)] = 0
                if timervals[outputList.index(outputsection)] < 0:
                        timervals[outputList.index(outputsection)] = 0

                try:
                        if(config.get(outputsection, 'default-state')=='on'):
                                outDefaults[outputList.index(outputsection)]=True
                        else:
                                outDefaults[outputList.index(outputsection)]=False
                except:
                        outDefaults[outputList.index(outputsection)]=False
                
                try:
                        pwmStr = config.get(outputsection, 'pwm')
                except:
                        pwmStr=""
                
                if pwmStr == 'fast':
                        fastPwmEnable[outputList.index(outputsection)]=True
                elif pwmStr == 'ultra-slow':
                        ultraSlowPwmEnable[outputList.index(outputsection)]=True
                
########################################################################################
#@brief: writeConfTofile(), write configuration data to file
def writeConfToFile():
        global filename
        configwriter = configparser.ConfigParser()
        configwriter.add_section('Global')
        configwriter.set('Global', 'timeout', str(timeoutThr))
        configwriter.set('Global', 'long-push-threshold', str(longPushThr))
        configwriter.set('Global', 'debounce-time', str(debouncetime))
        configwriter.set('Global', 'brownout-threshold', str(brownoutThr))
        configwriter.set('Global', 'description', str(description))
        for section in sectionList:
                try:
                        configwriter.add_section(section)
                except:
                        print("Section "+section+" already exists, overwriting")
####################### make dummy config file ##########################################
                configwriter.set(section, 'short-on', '')
                configwriter.set(section, 'short-off','')
                configwriter.set(section, 'long-on','')
                configwriter.set(section, 'long-off','')
                configwriter.set(section, 'switch-type', 'push-button')
                configwriter.set(section, 'pattern-saving-shortpush', 'off')
                configwriter.set(section, 'pattern-saving-longpush', 'off')
        for outputsection in outputList:
                try:
                        configwriter.add_section(outputsection)
                except:
                        print("Section "+outputsection+" already exists, overwriting")
                configwriter.set(outputsection, 'input-controlled','never')
                configwriter.set(outputsection, 'timer-controlled','never')
                configwriter.set(outputsection, 'timeout-value','0')
                configwriter.set(outputsection, 'default-state', 'off')
                configwriter.set(outputsection, 'pwm', 'off')
                

####################### prepare lists for config file #####################################
        for x in range(0,16):
                if(buttonConf[x]==True):
                        configwriter.set(sectionList[x], 'switch-type', 'toggle-switch')
        
        for x in range(0,16):
                if(patternSavingShort[x]==True):
                        configwriter.set(sectionList[x], 'pattern-saving-shortpush', 'on')
                        
        for x in range(0,16):
                if(patternSavingLong[x]==True):
                        configwriter.set(sectionList[x], 'pattern-saving-longpush', 'on')
        
        for section in sectionList:
                shortOn = []
                shortOff = []
                longOn = []
                longOff = []
                
                if sectionList.index(section)>7:
                        skip = 512
                        multiplier=(sectionList.index(section)-8)*8
                else:
                        skip = 0
                        multiplier=(sectionList.index(section))*8
                
                #shorton:
                for x in range(0,16):
                        if x<8  and ioConf[x+multiplier+skip]==True:
                                shortOn.append(x)
                                
                        if x>7 and ioConf[x-8+multiplier+skip+128]==True:
                                shortOn.append(x)
                        
                        
                        if x<8 and ioConf[x+64+multiplier+skip]==True:
                                shortOff.append(x)
                        if x>7 and ioConf[x-8+64+128+multiplier+skip]==True:
                                shortOff.append(x)

                        
                        if x<8 and ioConf[x+256+multiplier+skip]==True:
                                longOn.append(x)
                        if x>7 and ioConf[x-8+256+128+multiplier+skip]==True:
                                longOn.append(x)

                
                        if x<8 and ioConf[x+256+64+multiplier+skip]==True:
                                longOff.append(x)
                        if x>7 and ioConf[x-8+256+64+128+multiplier+skip]==True:
                                longOff.append(x)

                
######################### finally, write to file ##################################
                configwriter.set(section, 'short-on', ','.join(map(str,shortOn)))
                configwriter.set(section, 'short-off', ','.join(map(str,shortOff)))
                configwriter.set(section, 'long-on', ','.join(map(str,longOn)))
                configwriter.set(section, 'long-off', ','.join(map(str,longOff)))
                
        for outputsection in outputList:
                if(oConf[outputList.index(outputsection)+16]):
                        configwriter.set(outputsection, 'input-controlled','timeout-only')
                if(oConf[outputList.index(outputsection)]):
                        configwriter.set(outputsection, 'input-controlled','always')
        
        for outputsection in outputList:
                if(fastPwmEnable[outputList.index(outputsection)]):
                        configwriter.set(outputsection, 'pwm','fast')
                if(ultraSlowPwmEnable[outputList.index(outputsection)]):
                        configwriter.set(outputsection, 'pwm','ultra-slow')

        for outputsection in outputList:
                if(timerOConf[outputList.index(outputsection)+16]):
                        configwriter.set(outputsection, 'timer-controlled','timeout-only')
                if(timerOConf[outputList.index(outputsection)]):
                        configwriter.set(outputsection, 'timer-controlled','always')
                configwriter.set(outputsection,'timeout-value',str(timervals[outputList.index(outputsection)]))
                
        for outputsection in outputList:
                if(outDefaults[outputList.index(outputsection)]):
                        configwriter.set(outputsection, 'default-state', 'on')
                else:
                        configwriter.set(outputsection, 'default-state', 'off')
        
        with open(filename, 'w') as configfile:
                configwriter.write(configfile)

