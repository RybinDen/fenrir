#!/bin/python

class command():
    def __init__(self):
        pass
    def initialize(self, environment):
        return environment
    def shutdown(self, environment):
        return environment 
    def getDescription(self, environment):
        return 'No Description found'         
    def run(self, environment):
        return environment
    def setCallback(self, callback):
        pass
