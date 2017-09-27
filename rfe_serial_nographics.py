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
import numpy as np

# import sys
# sys.path.insert(0, '/home/markw/git/kd0aij/RFExplorer-for-Python/RFExplorer')
import RFExplorer
from matplotlib import pyplot as plt

#---------------------------------------------------------
# Helper functions
#---------------------------------------------------------

def PrintPeak(objRFE, startTime):
    """This function prints the amplitude and frequency peak of the max hold data
    """
    nInd = objRFE.SweepData.Count-1
    print("sweep count: %d" % nInd)
    sweepObj = objRFE.SweepData.MaxHoldData
    if sweepObj == None:
        return ""
    peakIndex = sweepObj.GetPeakStep()      #Get index of the peak
    fAmplitudeDBM = sweepObj.GetAmplitude_DBM(peakIndex)    #Get amplitude of the peak
    fCenterFreq = sweepObj.GetFrequencyMHZ(peakIndex)   #Get frequency of the peak
    startFreq = sweepObj.GetFrequencyMHZ(0)
    endFreq = sweepObj.GetFrequencyMHZ(sweepObj.TotalSteps)

    sResult = str(startTime)
    sResult += ", start freq," + str(startFreq) + ", end freq, " + str(endFreq) + " MHz, Peak, " + "{0:.3f}".format(fCenterFreq) + " MHz, " + str(fAmplitudeDBM) + " dBm, "
    for nStep in range(sweepObj.TotalSteps):
        if (nStep > 0):
            sResult += ","
        sResult += str('{:04.1f}'.format(sweepObj.GetAmplitudeDBM(nStep, None, False)+120))
    return sResult + "\n"

#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

SERIALPORT = "/dev/ttyUSB0"    #serial port identifier, use None to autodetect
#SERIALPORT = None    #serial port identifier, use None to autodetect
BAUDRATE = 500000

objRFE = RFExplorer.RFECommunicator()     #Initialize object and thread
RPT_INTERVAL = 10           #Initialize time span to display activity
fseq = 0;

#---------------------------------------------------------
# Main processing loop
#---------------------------------------------------------

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
            w = objRFE.SweepData.MaxHoldData.TotalSteps
            h = 60
            pdata=np.zeros((h,w,3),dtype=np.uint8)
            
            # wait for start of interval
            while (True):
                startTime=datetime.now()
                if (startTime.second % RPT_INTERVAL) == 0:
                    break
                time.sleep(0.5)

            fname = "scans.csv"
            logfile = open(fname, 'w')

            # run forever
            while (True):
                # collect data for RPT_INTERVAL
                while ((datetime.now() - startTime).seconds<RPT_INTERVAL):    
                    objRFE.ProcessReceivedString(True)
                startTime=datetime.now()
                                     
                sweepObj = objRFE.SweepData.MaxHoldData
                print("displaying record %4d, peak dBm: %04d" % (fseq, sweepObj.GetAmplitude_DBM(sweepObj.GetPeakStep())))                                     
                for nStep in range(w):
                    pdata[fseq,nStep] = sweepObj.GetAmplitude_DBM(nStep)+120

                plt.close()
                plt.figure(1)
                plt.imshow(pdata,interpolation='nearest')
                plt.show(block=False)
                
                # transfer and reset the maxhold array 
                record = PrintPeak(objRFE, startTime)
                objRFE.SweepData.m_MaxHoldData = None                 
                logfile.write(record)
                time.sleep(1)
                fseq += 1
                if (fseq >= 59): fseq = 0
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
