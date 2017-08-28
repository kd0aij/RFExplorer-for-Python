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
import RFExplorer
import matplotlib.pyplot as plt
import numpy as np

from ftplib import FTP

#---------------------------------------------------------
# Helper functions
#---------------------------------------------------------

def PrintPeak(objRFE):
    """This function prints the amplitude and frequency peak of the latest received sweep
	"""
    nInd = objRFE.SweepData.Count-1
    objSweepTemp = objRFE.SweepData.GetData(nInd)
    nStep = objSweepTemp.GetPeakStep()      #Get index of the peak
    fAmplitudeDBM = objSweepTemp.GetAmplitude_DBM(nStep)    #Get amplitude of the peak
    fCenterFreq = objSweepTemp.GetFrequencyMHZ(nStep)   #Get frequency of the peak

    print("Sweep[" + str(nInd)+"]: Peak: " + "{0:.3f}".format(fCenterFreq) + "MHz  " + 
     str(fAmplitudeDBM) + "dBm")
    #print(objSweepTemp.Dump())
    print("maxhold " + objRFE.SweepData.MaxHoldData.Dump())
    x=np.arange(objSweepTemp.StartFrequencyMHZ, objSweepTemp.EndFrequencyMHZ, objSweepTemp.StepFrequencyMHZ)
    print(x)
    y=np.empty(objSweepTemp.TotalSteps)
    for i in range(objSweepTemp.TotalSteps):
      y[i] = objSweepTemp.GetAmplitude_DBM(i)
    plt.plot(x,y)
    plt.show()

#---------------------------------------------------------
# global variables and initialization
#---------------------------------------------------------

SERIALPORT = "/dev/ttyUSB0"    #serial port identifier, use None to autodetect
BAUDRATE = 500000

objRFE = RFExplorer.RFECommunicator()     #Initialize object and thread
TOTAL_SECONDS = 10           #Initialize time span to display activity

#---------------------------------------------------------
# Main processing loop
#---------------------------------------------------------

#ftp = FTP('ftp.arvadamodelers.com')
#pwd = input("password: ")
#ftp.login(user='wxupload@arvadamodelers.com', passwd=pwd)
#print(ftp.getwelcome())

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
            print("Receiving data...")
            #Process until we complete scan time
            nLastDisplayIndex=0
            startTime=datetime.now()
            seq = 0
            while (seq<5):    
                print("start interval at " + str(startTime))
                while ((datetime.now() - startTime).seconds<TOTAL_SECONDS):    
                    #Process all received data from device 
                    objRFE.ProcessReceivedString(True)
                    #Print data if received new sweep only
                    #if (objRFE.SweepData.Count>nLastDisplayIndex):
                    #    PrintPeak(objRFE)      
                    
                    nLastDisplayIndex=objRFE.SweepData.Count
                print("end interval at " + str(datetime.now()))
                PrintPeak(objRFE)
                with open('tmpfile', 'w') as tmpfile:
                    tmpfile.write(str(startTime) + '\n')
                    tmpfile.write(objRFE.SweepData.MaxHoldData.Dump())
                #with open('tmpfile', 'rb') as tmpfile:
                #    ftp.storbinary('STOR rfscan.csv', tmpfile)
                
                objRFE.SweepData.CleanAll()
                startTime=datetime.now()
                seq = seq+1
                
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