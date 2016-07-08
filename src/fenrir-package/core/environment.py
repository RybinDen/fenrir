#!/bin/python

from core import settings
from core import soundIcons
from core import bindings
from core import runtime
from core import screenData
from core import generalInformation

environment = {
'running':True,
'debug':None,
'columns': 0,
'lines': 0,
'delta': '',
'oldCursor':{'x':0,'y':0},
'oldContentBytes': b'',
'oldContentText': '',
'oldContentAttrib': b'',
'newCursor':{'x':0,'y':0},
'newContentBytes': b'',
'newContentText': '',
'newContentAttrib': b'',
'oldTTY':'-1', #to get shure that the first loop is a chagne
'newTTY':'0',
'speechDriverString':'',
'speechDriver': None,
'screenDriverString': '',
'screenDriver': None,
'soundDriverString': '',
'soundDriver': None,
'inputManager': None,
'settings' = settings.settings,
'bindings' = bindings.bindings,
'soundIcons' = soundIcons.soundIcons,
'autospeak' = ['speak_delta'],
}
