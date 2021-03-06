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
from RFExplorer import RFE_Common 
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
            #objRFE.SweepData.m_bAutogrow = False # changed in RFExplorer.py           
            
            ## wait for start of interval
            #while (True):
                #startTime=datetime.now()
                #if (startTime.second % RPT_INTERVAL) == 0:
                    #break
                #time.sleep(0.5)

            fname = "scans.csv"
            logfile = open(fname, 'w')

            # run forever
            while (True):
                # collect RFE_Common.CONST_MAX_ELEMENTS scans
                while (objRFE.SweepData.Count < RFE_Common.CONST_MAX_ELEMENTS):
                    objRFE.ProcessReceivedString(True)
                    
                startTime=datetime.now()
                                     
                maxHold = objRFE.SweepData.MaxHoldData
                print("displaying interval %4d, peak freq  %.1f, dBm: %04d" % (fseq, maxHold.GetFrequencyMHZ(maxHold.GetPeakStep()), maxHold.GetAmplitude_DBM(maxHold.GetPeakStep())))                                     

                scan = objRFE.SweepData.GetData(0)
                w = scan.TotalSteps
                h = objRFE.SweepData.Count
                pdata=np.zeros((h,w,3),dtype=np.uint8)
                
                startFreq = scan.GetFrequencyMHZ(0)
                endFreq = scan.GetFrequencyMHZ(scan.TotalSteps)
                sResult = str(startTime)
                sResult += ", start freq," + str(startFreq) + ", end freq, " + str(endFreq)  + " MHz"
                logfile.write(sResult + "\n")
                
                for row in range(h):
                    scan = objRFE.SweepData.GetData(row)
                    
                    peakIndex = scan.GetPeakStep()      #Get index of the peak
                    fAmplitudeDBM = scan.GetAmplitude_DBM(peakIndex)    #Get amplitude of the peak
                    fCenterFreq = scan.GetFrequencyMHZ(peakIndex)   #Get frequency of the peak
                    
                    sResult = "scan, " + str(row)
                    sResult += ", Peak, " + "{0:.3f}".format(fCenterFreq) + " MHz, " 
                    sResult += str(fAmplitudeDBM) + " dBm"
                    for nStep in range(w):
                        pdata[row,nStep] = 2 * (scan.GetAmplitude_DBM(nStep)+120)
                        sResult += ","
                        sResult += str('{:04.1f}'.format(scan.GetAmplitude_DBM(nStep)))

                    logfile.write(sResult + "\n")
                        
                plt.close()
                plt.figure(num=fseq, figsize=(8,4))
                plt.imshow(pdata,interpolation='nearest')
                plt.show(block=False)
                
                # transfer and reset the maxhold array 
                #record = PrintPeak(objRFE, startTime)
                #objRFE.SweepData.m_MaxHoldData = None                 
                objRFE.SweepData.CleanAll()
                #logfile.write(record)
                time.sleep(1)
                fseq += 1
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
