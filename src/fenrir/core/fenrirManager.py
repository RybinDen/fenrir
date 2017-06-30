#!/bin/env python3
# -*- coding: utf-8 -*-

# Fenrir TTY screen reader
# By Chrys, Storm Dragon, and contributers.

import os, sys, signal, time
import fenrirVersion

if not os.path.dirname(os.path.realpath(fenrirVersion.__file__)) in sys.path:
    sys.path.append(os.path.dirname(os.path.realpath(fenrirVersion.__file__)))

from core import i18n
from core import settingsManager
from core import debug
import argparse

class fenrirManager():
    def __init__(self):
        self.initialized = False
        cliArgs = self.handleArgs()
        if not cliArgs:
            return        
        try:
            self.environment = settingsManager.settingsManager().initFenrirConfig(cliArgs, self)
            if not self.environment:
                raise RuntimeError('Cannot Initialize. Maybe the configfile is not available or not parseable')
        except RuntimeError:
            raise
        self.initialized = True        
        self.environment['runtime']['outputManager'].presentText(_("Start Fenrir"), soundIcon='ScreenReaderOn', interrupt=True)          
        signal.signal(signal.SIGINT, self.captureSignal)
        signal.signal(signal.SIGTERM, self.captureSignal)
        self.wasCommand = False
        
    def handleArgs(self):
        args = None
        parser = argparse.ArgumentParser(description="Fenrir Help")
        parser.add_argument('-s', '--setting', metavar='SETTING-FILE', default='/etc/fenrir/settings/settings.conf', help='Use a specified settingsfile')
        parser.add_argument('-o', '--options', metavar='SECTION#SETTING=VALUE,..', default='', help='Overwrite options in given settings file')        
        try:
            args = parser.parse_args()
        except Exception as e:
            parser.print_help()
        return args    
    def proceed(self):
        if not self.initialized:
            return
        self.environment['runtime']['eventManager'].startMainEventLoop()
        self.shutdown()
    def handleInput(self):
        eventReceived = self.environment['runtime']['inputManager'].getInputEvent()
        startTime = time.time()
        if eventReceived:
            self.prepareCommand()
            if not (self.wasCommand  or self.environment['general']['tutorialMode']) or  self.environment['runtime']['screenManager'].isSuspendingScreen():
                self.environment['runtime']['inputManager'].writeEventBuffer()
            if self.environment['runtime']['inputManager'].noKeyPressed():
                if self.wasCommand:
                        self.wasCommand = False   
                        self.environment['runtime']['inputManager'].clearEventBuffer()            
                if self.environment['general']['tutorialMode']:
                    self.environment['runtime']['inputManager'].clearEventBuffer()
                if self.environment['input']['keyForeward'] > 0:
                    self.environment['input']['keyForeward'] -=1
            #self.environment['runtime']['screenManager'].update('onInput')                            
            self.environment['runtime']['commandManager'].executeDefaultTrigger('onInput')       
        self.handleCommands()
    def handleScreenChange(self):
        self.environment['runtime']['screenManager'].update('onScreenChange')
        '''        
        if self.environment['runtime']['applicationManager'].isApplicationChange():
            self.environment['runtime']['commandManager'].executeDefaultTrigger('onApplicationChange')
            self.environment['runtime']['commandManager'].executeSwitchTrigger('onSwitchApplicationProfile', \
              self.environment['runtime']['applicationManager'].getPrevApplication(), \
              self.environment['runtime']['applicationManager'].getCurrentApplication())          
        '''        
        self.environment['runtime']['commandManager'].executeDefaultTrigger('onScreenChanged')             
            
    def handleScreenUpdate(self):
        s = time.time()

        self.environment['runtime']['screenManager'].update('onUpdate')
        '''
        if self.environment['runtime']['applicationManager'].isApplicationChange():
            self.environment['runtime']['commandManager'].executeDefaultTrigger('onApplicationChange')
            self.environment['runtime']['commandManager'].executeSwitchTrigger('onSwitchApplicationProfile', \
              self.environment['runtime']['applicationManager'].getPrevApplication(), \
              self.environment['runtime']['applicationManager'].getCurrentApplication())          
        '''              
        self.environment['runtime']['commandManager'].executeDefaultTrigger('onScreenUpdate')
        #print(time.time() -s)
    def handlePlugInputDevice(self):
        self.environment['runtime']['commandManager'].executeDefaultTrigger('PlugInputDevice')   
    def handleHeartBeat(self):
        self.environment['runtime']['commandManager'].executeDefaultTrigger('onHeartBeat')  
        #self.environment['runtime']['outputManager'].brailleText(flush=False)                        
    
    def prepareCommand(self):
        if self.environment['runtime']['screenManager'].isSuspendingScreen():
            self.wasCommand = False
            return        
        if self.environment['runtime']['inputManager'].noKeyPressed():
            return
        if self.environment['input']['keyForeward'] > 0:
            return
        shortcut = self.environment['runtime']['inputManager'].getCurrShortcut()        
        command = self.environment['runtime']['inputManager'].getCommandForShortcut(shortcut)        
        if len(self.environment['input']['prevDeepestInput']) <= len(self.environment['input']['currInput']):
            self.wasCommand = command != '' or self.environment['runtime']['inputManager'].isFenrirKeyPressed() or self.environment['runtime']['inputManager'].isScriptKeyPressed()    
        if command == '':
            return
            
        self.environment['runtime']['commandManager'].queueCommand(command)  

    def handleCommands(self): 
        if not self.environment['runtime']['commandManager'].isCommandQueued():
            return
        self.environment['runtime']['commandManager'].executeCommand( self.environment['commandInfo']['currCommand'], 'commands')

    def shutdownRequest(self):
        self.environment['runtime']['eventManager'].stopMainEventLoop()

    def captureSignal(self, siginit, frame):
        self.shutdownRequest()

    def shutdown(self):
        self.environment['runtime']['eventManager'].stopMainEventLoop()        
        self.environment['runtime']['outputManager'].presentText(_("Quit Fenrir"), soundIcon='ScreenReaderOff', interrupt=True)       
        self.environment['runtime']['eventManager'].cleanEventQueue()
        self.environment['runtime']['eventManager'].stopMainEventLoop(True)
        for currManager in self.environment['general']['managerList']:
            if self.environment['runtime'][currManager]:
                self.environment['runtime'][currManager].shutdown()                      
                del self.environment['runtime'][currManager]
        self.environment = None

def main():
    app = fenrir()
    app.proceed()
    del app

if __name__ == "__main__":
    main()        
