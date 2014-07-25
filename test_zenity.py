#!/usr/bin/python

from PyZenity import InfoMessage
from PyZenity import Question
from PyZenity import ErrorMessage
from PyZenity import GetFilename

#choice=Question('Please press a button.')

lst = GetFilename(multiple=True)

print lst
#if choice:
    #InfoMessage('You pressed Yes!')
#else:
    #ErrorMessage('You pressed No!')
