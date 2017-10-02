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
from ftplib import FTP

#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

rfmodem1 = serial.Serial('/dev/ttyUSB1', 57600, timeout=15)

ftp = FTP('192.168.0.1')
pwd = input("password: ")
ftp.login(user='markw', passwd=pwd)
print(ftp.getwelcome())
ftp.cwd('new/rfscans')

fseq = 0
fname = "scan_%04d.csv" % fseq
logfile = open('tmpfile', 'w')

#---------------------------------------------------------
# Main processing loop
#---------------------------------------------------------

iseq = 0
while (True):
	iseq += 1
	rec = rfmodem1.readline()
	print("record: {0:d}\n".format(iseq) + str(rec.decode()))
	
	# write to tmp file
	logfile.write(str(rec.decode()))
	
	if (iseq == 10):
		# transfer and start a new file
		iseq = 0
		logfile.close()
		# first send the current file to the server
		ftpcommand = "STOR %s" % fname
		print("ftp command %s" % ftpcommand)
		 
		with open('tmpfile', 'rb') as tmpfile:
			ftp.storbinary(ftpcommand, tmpfile)
		# create new tmpfile
		fseq += 1
		startTime=datetime.now()
		print("start new file at " + str(startTime))
		fname = "scan_%04d.csv" % fseq
		logfile = open('tmpfile', 'w')
