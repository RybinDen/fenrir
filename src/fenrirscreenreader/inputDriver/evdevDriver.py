#!/bin/python
# -*- coding: utf-8 -*-

# Fenrir TTY screen reader
# By Chrys, Storm Dragon, and contributers.

_evdevAvailable = False
_udevAvailable = False
_evdevAvailableError = ''
_udevAvailableError = ''
try:
    import evdev
    from evdev import InputDevice, UInput
    _evdevAvailable = True

except Exception as e:
    _evdevAvailableError = str(e)

try:
    import pyudev
    _udevAvailable = True
except Exception as e:
    _udevAvailableError = str(e)

import time
from select import select
import multiprocessing
from multiprocessing.sharedctypes import Value
from ctypes import c_bool

from fenrirscreenreader.core.eventData import fenrirEventType
from fenrirscreenreader.core import inputData
from fenrirscreenreader.core import debug
from fenrirscreenreader.core.inputDriver import inputDriver

class driver(inputDriver):
    def __init__(self):
        inputDriver.__init__(self)
        self._manager = multiprocessing.Manager()
        self.iDevices = {}
        self.iDevicesFD = self._manager.list()
        self.uDevices = {}
        self.gDevices = {}
        self.iDeviceNo = 0
        self.watchDog = Value(c_bool, True)
    def initialize(self, environment):
        self.env = environment
        self.env['runtime']['inputManager'].setShortcutType('KEY')        
        global _evdevAvailable
        global _udevAvailable        
        self._initialized = _evdevAvailable
        if not self._initialized:
            global _evdevAvailableError
            self.env['runtime']['debug'].writeDebugOut('InputDriver: ' + _evdevAvailableError,debug.debugLevel.ERROR)         
            return  
        self.updateInputDevices()
        if _udevAvailable:
            self.env['runtime']['processManager'].addCustomEventThread(self.plugInputDeviceWatchdogUdev)        
        #else:
        #    self.env['runtime']['processManager'].addSimpleEventThread(fenrirEventType.PlugInputDevice, self.plugInputDeviceWatchdogTimer)                
        self.env['runtime']['processManager'].addCustomEventThread(self.inputWatchdog)
    def plugInputDeviceWatchdogUdev(self,active , eventQueue):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='input')
        monitor.start()
        while active.value:
            validDevices = []
            device = monitor.poll(1)
            while device:
                try:
                    if not '/sys/devices/virtual/input/' in device.sys_path:
                        if device.device_node:
                            validDevices.append(str(device.device_node))
                    device = monitor.poll(0.1)
                except:                    
                    pass
            if validDevices:
                eventQueue.put({"Type":fenrirEventType.PlugInputDevice,"Data":validDevices})
        return time.time()       
    def plugInputDeviceWatchdogTimer(self, active):
        time.sleep(10)
        return None
         
    def inputWatchdog(self,active , eventQueue):
        try:
            while active.value:
                r, w, x = select(self.iDevices, [], [], 0.7)
                for fd in r:
                    event = None
                    foreward = False
                    eventFired = False
                    try:
                        event = self.iDevices[fd].read_one()                              
                    except:
                        self.removeDevice(fd)
                    while(event):
                        self.env['input']['eventBuffer'].append( [self.iDevices[fd], self.uDevices[fd], event])
                        if event.type == evdev.events.EV_KEY:
                            if event.code != 0:
                                currMapEvent = self.mapEvent(event)
                                if not currMapEvent:
                                    foreward = True                            
                                if not isinstance(currMapEvent['EventName'], str):
                                    foreward = True                            
                                if not foreward or eventFired:
                                    if currMapEvent['EventState'] in [0,1,2]:
                                        eventQueue.put({"Type":fenrirEventType.KeyboardInput,"Data":currMapEvent.copy()}) 
                                        eventFired = True
                        else:
                            if not event.type in [0,4]:
                                foreward = True
                              
                        event = self.iDevices[fd].read_one()   
                    if foreward and not eventFired:
                        self.writeEventBuffer()
                        self.clearEventBuffer() 
        except Exception as e:
            self.env['runtime']['debug'].writeDebugOut("INPUT WATCHDOG CRASH: "+str(e),debug.debugLevel.ERROR)                
         
    def handleInputEvent(self, event):
        return       

    def writeEventBuffer(self):
        if not self._initialized:
            return    
        for iDevice, uDevice, event in self.env['input']['eventBuffer']:
            try:
                if uDevice:
                    if self.gDevices[iDevice.fd]:
                        self.writeUInput(uDevice, event)
            except Exception as e:
                pass           

    def clearEventBuffer(self):
        if not self._initialized:
            return    
        del self.env['input']['eventBuffer'][:]
                        
    def writeUInput(self, uDevice, event):
        if not self._initialized:
            return    
        uDevice.write_event(event)
        uDevice.syn()

    def updateInputDevices(self, newDevices = None, init = False):
        if init:
            self.removeAllDevices()

        deviceFileList = None

        if newDevices and not init:
            deviceFileList = newDevices
        else:
            deviceFileList = evdev.list_devices()
            if len(deviceFileList) == self.iDeviceNo:
                return  
        if not deviceFileList:
            return

        mode = self.env['runtime']['settingsManager'].getSetting('keyboard', 'device').upper()
        
        iDevicesFiles = []
        for device in self.iDevices:
            iDevicesFiles.append(self.iDevices[device].fn)

        eventType = evdev.events
        for deviceFile in deviceFileList:
            try:
                if not deviceFile:
                    continue
                if deviceFile == '':
                    continue
                if deviceFile in iDevicesFiles:
                    continue
                
                try:
                    open(deviceFile)
                except Exception as e:
                    self.env['runtime']['debug'].writeDebugOut("Not readable Inputdevice : " + deviceFile +' ' + str(e),debug.debugLevel.ERROR)                                
                    continue
                # 3 pos absolute
                # 2 pos relative
                # 1 Keys

                try:
                    currDevice = evdev.InputDevice(deviceFile)
                except:
                    continue

                try:
                    if currDevice.name.upper() in ['','SPEAKUP','PY-EVDEV-UINPUT']:
                        continue                
                    if currDevice.phys.upper() in ['','SPEAKUP','PY-EVDEV-UINPUT']:
                        continue                    
                    if 'BRLTTY' in  currDevice.name.upper():
                        continue                             
                except:
                    pass

                cap = currDevice.capabilities()
                if mode in ['ALL','NOMICE']:
                    if eventType.EV_KEY in cap:
                        if 116 in cap[eventType.EV_KEY] and len(cap[eventType.EV_KEY]) < 10:
                            self.env['runtime']['debug'].writeDebugOut('Device Skipped (has 116):' + currDevice.name,debug.debugLevel.INFO)                                                                
                            continue
                        if len(cap[eventType.EV_KEY]) < 60:
                            self.env['runtime']['debug'].writeDebugOut('Device Skipped (< 60 keys):' + currDevice.name,debug.debugLevel.INFO)                                                                                        
                            continue                                                   
                        if mode == 'ALL':
                            self.addDevice(currDevice)
                            self.env['runtime']['debug'].writeDebugOut('Device added (ALL):' + self.iDevices[currDevice.fd].name, debug.debugLevel.INFO)                           
                        elif mode == 'NOMICE':
                            if not ((eventType.EV_REL in cap) or (eventType.EV_ABS in cap)):
                                self.addDevice(currDevice)
                                self.env['runtime']['debug'].writeDebugOut('Device added (NOMICE):' + self.iDevices[currDevice.fd].name,debug.debugLevel.INFO)                                                
                            else:
                                self.env['runtime']['debug'].writeDebugOut('Device Skipped (NOMICE):' + currDevice.name,debug.debugLevel.INFO)                                        
                elif currDevice.name.upper() in mode.split(','):
                    self.addDevice(currDevice)
                    self.env['runtime']['debug'].writeDebugOut('Device added (Name):' + self.iDevices[currDevice.fd].name,debug.debugLevel.INFO)                                                                                                                                            
            except Exception as e:
                self.env['runtime']['debug'].writeDebugOut("Device Skipped (Exception): " + deviceFile +' ' + currDevice.name +' '+ str(e),debug.debugLevel.INFO)
        self.iDeviceNo = len(evdev.list_devices())
        self.updateMPiDevicesFD()

    def updateMPiDevicesFD(self):
        try:
            for fd in self.iDevices:
                if not fd in self.iDevicesFD:
                    self.iDevicesFD.append(fd)
            for fd in self.iDevicesFD:
                if not fd in self.iDevices:
                    self.iDevicesFD.remove(fd)  
        except:
            pass
    def mapEvent(self, event):
        if not self._initialized:
            return None    
        if not event:
            return None
        mEvent = inputData.inputEvent
        try:
            mEvent['EventName'] = evdev.ecodes.keys[event.code]
            mEvent['EventValue'] = event.code
            mEvent['EventSec'] = event.sec
            mEvent['EventUsec'] = event.usec                
            mEvent['EventState'] = event.value
            mEvent['EventType']  = event.type
            return mEvent
        except Exception as e:
            return None
       
    def getLedState(self, led = 0):
        if not self.hasIDevices():
            return False    
        # 0 = Numlock
        # 1 = Capslock
        # 2 = Rollen
        for fd, dev in self.iDevices.items():
            if led in dev.leds():
                return True
        return False          
    def toggleLedState(self, led = 0):
        if not self.hasIDevices():
            return False    
        ledState = self.getLedState(led)
        for i in self.iDevices:
            # 17 LEDs
            if 17 in self.iDevices[i].capabilities():            
                if ledState == 1:
                    self.iDevices[i].set_led(led , 0)
                else:
                    self.iDevices[i].set_led(led , 1)
    def grabAllDevices(self):
        if not self._initialized:
            return
        for fd in self.iDevices:
            self.grabDevice(fd)  

    def ungrabAllDevices(self):
        if not self._initialized:
            return          
        for fd in self.iDevices:
            self.ungrabDevice(fd)

    def createUInputDev(self, fd):
        if not self.env['runtime']['settingsManager'].getSettingAsBool('keyboard', 'grabDevices'):
            self.uDevices[fd] = None
            return
        try:
            test = self.uDevices[fd]
            return
        except KeyError:
            self.uDevices[fd] = None
        if self.uDevices[fd] != None:
            return
        try:      
            self.uDevices[fd] = UInput.from_device(self.iDevices[fd])            
        except Exception as e:
            try:
                self.env['runtime']['debug'].writeDebugOut('InputDriver evdev: compat fallback:  ' + str(e),debug.debugLevel.WARNING)         
                dev = self.iDevices[fd]
                cap = dev.capabilities()
                del cap[0]
                self.uDevices[fd] = UInput(
                  cap,
                  dev.name,
                )
            except Exception as e:
                self.env['runtime']['debug'].writeDebugOut('InputDriver evdev: init Uinput not possible:  ' + str(e),debug.debugLevel.ERROR)         
                return               
    def addDevice(self, newDevice):
        self.env['runtime']['debug'].writeDebugOut('InputDriver evdev: device added:  ' + str(newDevice.fd) + ' ' +str(newDevice),debug.debugLevel.INFO)      
        self.iDevices[newDevice.fd] = newDevice  
        self.gDevices[newDevice.fd] = False                      
        self.createUInputDev(newDevice.fd)
    def grabDevice(self, fd):
        if not self.env['runtime']['settingsManager'].getSettingAsBool('keyboard', 'grabDevices'):
            return
        try:
            self.iDevices[fd].grab()
            self.gDevices[fd] = True                        
        except IOError:            
            self.gDevices[fd] = True            
        except Exception as e:
            self.env['runtime']['debug'].writeDebugOut('InputDriver evdev: grabing not possible:  ' + str(e),debug.debugLevel.ERROR)         
    def ungrabDevice(self,fd):
        if not self.env['runtime']['settingsManager'].getSettingAsBool('keyboard', 'grabDevices'):
            return      
        try:
            self.gDevices[fd] = False                    
            self.iDevices[fd].ungrab()            
        except:
            pass    
    def removeDevice(self,fd):
        self.env['runtime']['debug'].writeDebugOut('InputDriver evdev: device removed:  ' + str(fd) + ' ' +str(self.iDevices[fd]),debug.debugLevel.INFO)         
        self.clearEventBuffer()
        try:
            self.ungrabDevice(fd)
        except:
            pass
        try:
            self.iDevices[fd].close()
        except:
            pass
        try:
            self.uDevices[fd].close()
        except:
            pass 
        try:
            del(self.iDevices[fd])
        except:
            pass
        try:
            del(self.uDevices[fd])
        except:
            pass  
        try:
            del(self.gDevices[fd])
        except:
            pass              
        self.updateMPiDevicesFD()
                 
    def hasIDevices(self):
        if not self._initialized:
            return False
        if not self.iDevices:
            return False
        if len(self.iDevices) == 0:
            return False
        return True    

    def removeAllDevices(self):
        if not self.hasIDevices():
            return
        devices = self.iDevices.copy()
        for fd in devices:
            self.removeDevice(fd)
        self.iDevices.clear()
        self.uDevices.clear()
        self.gDevices.clear()        
        self.iDeviceNo = 0 
