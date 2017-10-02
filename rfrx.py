#pylint: disable=trailing-whitespace, line-too-long, bad-whitespace, invalid-name, R0204, C0200
#pylint: disable=superfluous-parens, missing-docstring, broad-except
#pylint: disable=too-many-lines, too-many-instance-attributes, too-many-statements, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-public-methods, too-many-locals, too-many-arguments

#============================================================================
#This is an example code for RFExplorer python functionality. 
#Display amplitude value in dBm and frequency in MHz of the maximum value of sweep data.
#The number of stored sweep data can be configurated by time
#============================================================================

import time
from datetime import datetime, timedelta
import serial

#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

rfmodem1 = serial.Serial('/dev/ttyUSB1', 57600, timeout=15)

#---------------------------------------------------------
# Main processing loop
#---------------------------------------------------------

k = 0
while (True):
	rec = rfmodem1.readline()
	print("record: {0:d}\n".format(k) + str(rec.decode()))
	k += 1
	