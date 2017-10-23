#pylint: disable=trailing-whitespace, line-too-long, bad-whitespace, invalid-name, R0204, C0200
#pylint: disable=superfluous-parens, missing-docstring, broad-except
#pylint: disable=too-many-lines, too-many-instance-attributes, too-many-statements, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-public-methods, too-many-locals, too-many-arguments

#============================================================================
# Log RFexplorer scans to csv files; start a new file every hour.
#============================================================================

import time
from datetime import datetime, timedelta

import RFExplorer
from RFExplorer import RFE_Common 
from ftplib import FTP

#---------------------------------------------------------
# Helper functions
#---------------------------------------------------------

def FormatMaxHold(objRFE, startTime):
    """This function prints the amplitude and frequency peak of the max hold data
    """
    nInd = objRFE.SweepData.Count-1
    sweepObj = objRFE.SweepData.MaxHoldData
    if sweepObj == None:
        return ""
    peakIndex = sweepObj.GetPeakStep()      #Get index of the peak
    fAmplitudeDBM = sweepObj.GetAmplitude_DBM(peakIndex)    #Get amplitude of the peak
    fCenterFreq = sweepObj.GetFrequencyMHZ(peakIndex)   #Get frequency of the peak
    startFreq = sweepObj.GetFrequencyMHZ(0)
    endFreq = sweepObj.GetFrequencyMHZ(sweepObj.TotalSteps-1)

    sResult = str(startTime)
    sResult += ", start freq, {0:.1f}, MHz".format(startFreq)
    sResult += ", end freq, {0:.1f}, MHz".format(endFreq)
    sResult += ", Peak, {0:.1f}, MHz".format(fCenterFreq)
    sResult += ", {0:.1f}, dBm".format(fAmplitudeDBM)

#    date = str(startTime).split(' ')[0]
    time = str(startTime).split(' ')[1].split('.')[0]
    print("{:s}: Peak {:.1f} dBm at {:.1f} MHz".format(time, fAmplitudeDBM, fCenterFreq))
    
    for nStep in range(sweepObj.TotalSteps):
        sResult += ","
        sResult += str('{0:4.1f}'.format(sweepObj.GetAmplitude_DBM(nStep)))
    return sResult + "\n"
    
def ResetRFE():
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


#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

SERIALPORT = "/dev/ttyUSB0"    #serial port identifier
BAUDRATE = 500000

objRFE = RFExplorer.RFECommunicator()     #Initialize object and thread

#---------------------------------------------------------
# Main processing loop
#---------------------------------------------------------

pwd = input("password: ")
ftp = None

try:
    #Connect to specified port
    if (objRFE.ConnectPort(SERIALPORT, BAUDRATE)):
        ResetRFE()
        
        #If object is an analyzer, we can scan for received sweeps
        if (objRFE.IsAnalyzer()):
            print("Initialized...")

            startTime=datetime.now()
            print(str(startTime))
            
            fname = str(startTime).split('.')[0].replace(' ','_').replace(':','-') + ".csv"
            logfile = open(fname, 'w')
            print("logging to file: " + fname)

            while (True):
                
                # collect RFE_Common.CONST_MAX_ELEMENTS scans
                while (objRFE.SweepData.Count < RFE_Common.CONST_MAX_ELEMENTS):
                    objRFE.ProcessReceivedString(True)
                    
                    # each scan takes about 0.1 seconds, so check for data at 20Hz max
                    time.sleep(0.05)
                    
                scanTime=datetime.now()
                
                # transfer and reset the maxhold array 
                record = FormatMaxHold(objRFE, scanTime)
                objRFE.SweepData.CleanAll()
                logfile.write(record)

                # send the current file to the server and reset every 10 minutes
                resetTime = datetime.now()
                if ((resetTime-startTime).seconds >= 2 * 60):
                    logfile.close()
                    
                    if (ftp != None): ftp.quit()

                    ftp = FTP('71.205.254.76')
                    ftp.login(user='markw', passwd=pwd)
                    print(ftp.getwelcome())
                    ftp.cwd('/data')

                    # send the current file to the server
                    ftpcommand = "STOR %s" % fname
                    print("ftp command %s" % ftpcommand)
                    with open(fname, 'rb') as tmpfile:
                        ftp.storbinary(ftpcommand, tmpfile)
                    ftp.quit()
                     
                    print("reset at " + str(resetTime))                    
                    ResetRFE()
                    startTime = datetime.now()
                    print("reset took " + str(startTime-resetTime))
                    
                    fname = str(startTime).split('.')[0].replace(' ','_').replace(':','-') + ".csv"
                    logfile = open(fname, 'w')
                    print("logging to file: " + fname)
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
