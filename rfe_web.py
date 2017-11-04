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
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter

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
    deltaFreq = (endFreq - startFreq) / (sweepObj.TotalSteps-1)

    sResult = str(startTime)
    sResult += ", start freq, {0:.1f}, MHz".format(startFreq)
    sResult += ", end freq, {0:.1f}, MHz".format(endFreq)
    sResult += ", Peak, {0:.1f}, MHz".format(fCenterFreq)
    sResult += ", {0:.1f}, dBm".format(fAmplitudeDBM)

##    date = str(startTime).split(' ')[0]
    #time = str(startTime).split(' ')[1].split('.')[0]
    #print("{:s}: Peak {:.1f} dBm at {:.1f} MHz".format(time, fAmplitudeDBM, fCenterFreq))
    
    for nStep in range(sweepObj.TotalSteps):
        sResult += ","
        sResult += str('{0:4.1f}'.format(sweepObj.GetAmplitude_DBM(nStep)))
    return (sResult + "\n", fAmplitudeDBM, fCenterFreq, startFreq, deltaFreq)
    
def GetMaxHold(objRFE):
    """This function returns an array of max hold data values
    """
    sweepObj = objRFE.SweepData.MaxHoldData
    data = np.zeros((sweepObj.TotalSteps, 1)) 
    for nStep in range(sweepObj.TotalSteps):
        data[nStep] = sweepObj.GetAmplitude_DBM(nStep)
    return data.flatten()
    
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

# approximately 6 maxhold scans per minute
maxscans = 180
nscans = -1

try:
    #Connect to specified port
    if (objRFE.ConnectPort(SERIALPORT, BAUDRATE)):
        ResetRFE()
        
        #If object is an analyzer, we can scan for received sweeps
        if (objRFE.IsAnalyzer()):
            print("Initialized...")

            startTime=datetime.now()
            print(str(startTime))
            
            nFreqs = objRFE.SweepData.MaxHoldData.TotalSteps

            fprefix = str(startTime).split('.')[0].replace(' ','_').replace(':','-')
            fname = fprefix + ".csv"
            logfile = open(fname, 'w')
            print("logging to file: " + fname)
            
            fname_t = fprefix + "_T.csv"
            logfile_t = open(fname_t, 'w')
            print("logging cpu temp to file: " + fname_t)

            while (True):
                
                # collect RFE_Common.CONST_MAX_ELEMENTS scans
                while (objRFE.SweepData.Count < RFE_Common.CONST_MAX_ELEMENTS):
                    objRFE.ProcessReceivedString(True)
                    
                    # each scan takes about 0.1 seconds, so check for data at 20Hz max
                    time.sleep(0.05)
                    
                scanTime=datetime.now()
                #print(str(scanTime))

                # get new maxhold data                
                maxHold = GetMaxHold(objRFE)
                
                # init plotdata to minimum amplitude of first scan
                if (nscans == -1):
                    nscans += 1
                    minAmp = maxHold[0]
                    for col in range(nFreqs):
                        if (minAmp > maxHold[col]):
                            minAmp = maxHold[col]
                            
                        plotdata = np.full((maxscans,nFreqs), minAmp)
                
                # slide image down one scanline
                peakAmp = -200
                peakRec = 0
                for row in range(maxscans-2, -1, -1):
                    for col in range(nFreqs):
                        amp = plotdata[row, col]
                        plotdata[row+1, col] = amp
                        if (peakAmp < amp):
                            peakAmp = amp
                            peakCol = col
                            peakRec = rec
                        if (minAmp > amp):
                            minAmp = amp
                
                # add maxhold data at top of image
                for col in range(nFreqs):
                    amp = maxHold[col]
                    plotdata[0, col] = amp
                    if (peakAmp < amp):
                        peakAmp = amp
                        peakCol = col
                        peakRec = rec
                    if (minAmp > amp):
                        minAmp = amp
                                     
                # log to file and reset the maxhold array 
                (record, scanPeak, scanPeakFreq, startFreq, deltaFreq) = FormatMaxHold(objRFE, scanTime)
                objRFE.SweepData.CleanAll()
                logfile.write(record)

                with open('/sys/class/thermal/thermal_zone0/temp','r') as f:
                    tstring = f.read()
                tempc = float(tstring) / 1000
                logfile_t.write("{0:s}, {1:.1f}\n".format(str(scanTime).split('.')[0], tempc))

                plt.close()
                plt.figure(num=1, figsize=(8,4))
                fig, ax = plt.subplots()
                plt.imshow(plotdata,interpolation='nearest',cmap="hot")
                plt.xlabel('MHz')
                plt.ylabel('minutes')
                
                locs,labels = plt.xticks()                
                labels = ['{0:.1f}'.format(startFreq+locs[iTick]*deltaFreq) for iTick in range(len(labels))]
                ax.set_xticklabels(labels)

                tickIntvl = maxscans // 30
                locs = range(0,maxscans,tickIntvl)
                ax.set_yticks(locs)
                labels = ['{0:d}'.format(iTick) for iTick in range(len(locs))]
                ax.set_yticklabels(labels)
                
                peakFreq = startFreq + (peakCol * deltaFreq)
                plt.title('{2:s} T:{3:.1f}C\npeak amp: {0:.1f}, freq: {1:.1f}, time: {4:.1f}'.format(peakAmp, peakFreq, str(scanTime).split('.')[0], tempc, peakRec/6.0))
                
                #plt.show(block=False)
                plt.savefig("RFimage.png")
                
                # send the current file to the server and reset every 10 minutes
                resetTime = datetime.now()
                nscans += 1
                if (nscans >= maxscans): #((resetTime-startTime).seconds >= 1 * 60):
                    nscans = 0
                    logfile.close()
                                       
                    #print("reset at " + str(resetTime))                    
                    ResetRFE()
                    startTime = datetime.now()
                    #print("reset took " + str(startTime-resetTime))
                    
                    fprefix = str(startTime).split('.')[0].replace(' ','_').replace(':','-')
                    fname = fprefix + ".csv"
                    logfile = open(fname, 'w')
                    #print("logging to file: " + fname)
                    
                    logfile_t.close()
                    fname_t = fprefix + "_T.csv"
                    logfile_t = open(fname_t, 'w')
                    #print("logging cpu temp to file: " + fname_t)

        else:
            print("Error: Device connected is a Signal Generator. \nPlease, connect a Spectrum Analyzer")
    else:
        print("Not Connected")
except Exception as obEx:
    print("Error: " + str(obEx))

#---------------------------------------------------------
# Close object and release resources
#---------------------------------------------------------

objRFE.Close()    #Finish the thread and close port
objRFE = None 
