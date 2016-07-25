#!/bin/python

class command():
    def __init__(self):
        pass
    def run(self, environment):
        if environment['runtime']['settingsManager'].getSettingAsBool(environment, 'speech', 'enabled') or \
          environment['runtime']['settingsManager'].getSettingAsBool(environment, 'sound', 'enabled') or \
          environment['runtime']['settingsManager'].getSettingAsBool(environment, 'braille', 'enabled'):
            environment['runtime']['outputManager'].presentText(environment, "fenrir muted")          
            environment = environment['runtime']['settingsManager'].setSetting(environment, 'speech', 'enabled','False')
            environment = environment['runtime']['settingsManager'].setSetting(environment, 'sound', 'enabled','False')
            environment = environment['runtime']['settingsManager'].setSetting(environment, 'braille', 'enabled','False')
        else:
            environment['runtime']['outputManager'].presentText(environment, "fenrir unmuted")           
            environment = environment['runtime']['settingsManager'].setSetting(environment, 'speech', 'enabled','True')
            environment = environment['runtime']['settingsManager'].setSetting(environment, 'sound', 'enabled','True')
            environment = environment['runtime']['settingsManager'].setSetting(environment, 'braille', 'enabled','True')
        return environment    
    def setCallback(self, callback):
        pass
    def shutdown(self):
        pass