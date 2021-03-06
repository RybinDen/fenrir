#!/bin/python
# -*- coding: utf-8 -*-

# Fenrir TTY screen reader
# By Chrys, Storm Dragon, and contributers.

from fenrirscreenreader.core import debug

class command():
    def __init__(self):
        pass
    def initialize(self, environment):
        self.env = environment
    def shutdown(self):
        pass
    def getDescription(self):
        return 'No Description found'

    def run(self):
        if not self.env['runtime']['settingsManager'].getSettingAsBool('speech', 'autoReadIncoming'):
            return
        # is there something to read?
        if not self.env['runtime']['screenManager'].isDelta(ignoreSpace=True):
            return

        # this must be a keyecho or something
        #if len(self.env['screen']['newDelta'].strip(' \n\t')) <= 1:
        xMove = abs(self.env['screen']['newCursor']['x'] - self.env['screen']['oldCursor']['x'])
        yMove = abs(self.env['screen']['newCursor']['y'] - self.env['screen']['oldCursor']['y'])
        #print('-----')
        #print(self.env['screen']['newDelta'])
        #print(xMove, yMove, len(self.env['screen']['newNegativeDelta']), self.env['screen']['newNegativeDelta'])
        #print(xMove, yMove, len(self.env['screen']['newDelta']), self.env['screen']['newDelta'])
        if (xMove >= 1) and abs(xMove) == len(self.env['screen']['newDelta']):
        # if len(self.env['screen']['newDelta'].strip(' \n\t0123456789')) <= 2:
            if not '\n' in self.env['screen']['newDelta']:
                return
        # shift line
        if (xMove != 0) and len(self.env['screen']['newNegativeDelta']) == 0:
            return
        # filter out delete 
        if (xMove == 0) and (yMove == 0):
            if len(self.env['screen']['newNegativeDelta']) - len(self.env['screen']['newDelta']) in [1,2,3]:
                return

        self.env['runtime']['outputManager'].presentText(self.env['screen']['newDelta'], interrupt=False, flush=False)

    def setCallback(self, callback):
        pass

