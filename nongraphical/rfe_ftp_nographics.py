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
from ftplib import FTP

# import sys
# sys.path.insert(0, '/home/markw/git/kd0aij/RFExplorer-for-Python/RFExplorer')
import RFExplorer

#---------------------------------------------------------
# Helper functions
#---------------------------------------------------------

def PrintPeak(objRFE):
    """This function prints the amplitude and frequency peak of the max hold data
	"""
    nInd = objRFE.SweepData.Count-1
    print("sweep count: %d" % nInd)
    sweepObj = objRFE.SweepData.MaxHoldData
    peakIndex = sweepObj.GetPeakStep()      #Get index of the peak
    fAmplitudeDBM = sweepObj.GetAmplitude_DBM(peakIndex)    #Get amplitude of the peak
    fCenterFreq = sweepObj.GetFrequencyMHZ(peakIndex)   #Get frequency of the peak
    startFreq = sweepObj.GetFrequencyMHZ(0)
    endFreq = sweepObj.GetFrequencyMHZ(sweepObj.TotalSteps)

    print("peak index [" + str(peakIndex) + "]: Peak: " + "{0:.3f}".format(fCenterFreq) + " MHz  " + 
     str(fAmplitudeDBM) + " dBm\n")
    #print(sweepObj.Dump())
    sResult = "start freq:" + str(startFreq) + ", end freq: " + str(endFreq) + " MHz, Peak: " + "{0:.3f}".format(fCenterFreq) + " MHz, " + str(fAmplitudeDBM) + " dBm\n"
    sResult += str(datetime.now()) + "\n"
    for nStep in range(sweepObj.TotalSteps):
        if (nStep > 0):
            sResult += ","
        sResult += str('{:04.1f}'.format(sweepObj.GetAmplitudeDBM(nStep, None, False)))
    sResult += "\n"
    return sResult

#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

SERIALPORT = "/dev/ttyUSB0"    #serial port identifier, use None to autodetect
BAUDRATE = 500000

objRFE = RFExplorer.RFECommunicator()     #Initialize object and thread
TOTAL_SECONDS = 60           #Initialize time span to display activity
maxhold = []

#---------------------------------------------------------
# Main processing loop
#---------------------------------------------------------

ftp = FTP('ftp.arvadamodelers.com')
pwd = input("password: ")
ftp.login(user='wxupload@arvadamodelers.com', passwd=pwd)
print(ftp.getwelcome())
ftp.cwd('/rfscans')

try:
    #Find and show valid serial ports
    objRFE.GetConnectedPorts()    

    #Connect to available port
    if (objRFE.ConnectPort(SERIALPORT, BAUDRATE)):
        #Reset the unit to start fresh
        objRFE.SendCommand("r")
        #Wait for unit to notify reset completed
        while(objRFE.IsResetEvent):
            pass
        #Wait for unit to stabilize
        time.sleep(10)

        #Request RF Explorer configuration
        objRFE.SendCommand_RequestConfigData()
        #Wait to receive configuration and model details
        while(objRFE.ActiveModel == RFExplorer.RFE_Common.eModel.MODEL_NONE):
            objRFE.ProcessReceivedString(True)    #Process the received configuration

        #If object is an analyzer, we can scan for received sweeps
        if (objRFE.IsAnalyzer()):
            print("Initialized...")

            # turn Autogrow off since it will quickly run out of RAM
            # there is a max of 1000 sweeps allowed in RFESweepDataCollection
            objRFE.SweepData.m_bAutogrow = False
            
            iseq = 0
            fseq = 0
            fname = "scan_%04d.csv" % fseq
            logfile = open('tmpfile', 'w')
            # run forever
            while (True):
                iseq += 1
                # collect data for TOTAL_SECONDS
                startTime=datetime.now()
                print("start %d sec interval at %s" % (TOTAL_SECONDS, str(startTime)))
                while ((datetime.now() - startTime).seconds<TOTAL_SECONDS):    
                    #Process all received data from device 
                    objRFE.ProcessReceivedString(True)
                
                # check status: for now just check for changes in max hold data
                if (not maxhold):
                    # get reference to maxhold SweepData object
                    objMaxHold = objRFE.SweepData.MaxHoldData
                    # make a copy of the maxhold list
                    maxhold = objMaxHold.m_arrAmplitude[:];
                else:
                    # update the longterm maxhold data
                    for i in range(len(maxhold)):
                        if (maxhold[i] < objMaxHold.GetAmplitude_DBM(i)):
                            maxhold[i] = objMaxHold.GetAmplitude_DBM(i)
                            print("new max: freq: %.1f, amp: %.1f" % (objMaxHold.GetFrequencyMHZ(i), maxhold[i]))
                            
                # write to tmp file and ftp to host
                logfile.write(PrintPeak(objRFE))

                # transfer and start a new file every 10 minutes (to avoid getting kicked off the server)
                if (iseq == 10):
                    iseq = 0
                    logfile.close()
                    # clear the maxhold data
                    objRFE.SweepData.m_MaxHoldData = None
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
        else:
            print("Error: Device connected is a Signal Generator. \nPlease, connect a Spectrum Analyzer")
    else:
        print("Not Connected")
except Exception as obEx:
    print("Error: " + str(obEx))

#---------------------------------------------------------
# Close object and release resources
#---------------------------------------------------------

#ftp.quit()
                
objRFE.Close()    #Finish the thread and close port
objRFE = None 
