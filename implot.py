#pylint: disable=trailing-whitespace, line-too-long, bad-whitespace, invalid-name, R0204, C0200
#pylint: disable=superfluous-parens, missing-docstring, broad-except
#pylint: disable=too-many-lines, too-many-instance-attributes, too-many-statements, too-many-nested-blocks
#pylint: disable=too-many-branches, too-many-public-methods, too-many-locals, too-many-arguments

#============================================================================
# plot CSV file generated by rfe.py
#============================================================================

import numpy as np
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import os

fignum = 0

# find CSV files with names in the form YYYY-MM-DD_HH:MM:SS 
# signal strength measurements are appended with ".csv"
# and cpu temp files are appended with "_T.csv"
files = os.listdir('.')
sigfiles = []
tfiles = []
for fname in sorted(files):
  print(fname)
  index = fname.find('.csv')
  if (index == 19):
      sigfiles.append(fname)
  elif (index == 21):
      tfiles.append(fname)

# print the list and have user select the plot range
index = 0
for fname in sigfiles:
  print('{0:02d}: {1:s}'.format(index, fname.split('.')[0]))
  index += 1        

# concatenate all cputemp files into strtemp
# assuming the local directory contains all the csv files for a single day,
# skip the last file since it probably spans midnight
strtemp = ''
for index in range(len(tfiles)-1):
  print(tfiles[index])
  infile = open(tfiles[index], 'r')
  strtemp += infile.read()
  
# plot cpu temps
templines = strtemp.split('\n')
ntemps = len(templines)-1
tempc = np.zeros(ntemps)

# construct x axis
starthms = templines[0].split(',')[0].split(' ')[1].split(':')
endhms = templines[ntemps-1].split(',')[0].split(' ')[1].split(':')
startsec = int(starthms[0])*3600 + int(starthms[1])*60 + int(starthms[2])
endsec = int(endhms[0])*3600 + int(endhms[1])*60 + int(endhms[2])

xvals = np.linspace(startsec/3600, endsec/3600, ntemps)

for rec in range(ntemps):
  tempc[rec] = float(templines[rec].split(',')[1])
fignum += 1
fig, ax = plt.subplots(num=fignum, figsize=(8,4))
ax.plot(xvals,tempc)
#plt.xticks(np.linspace(ntemps/360,24))
plt.xlabel('hours')
plt.ylabel('degC')
plt.title('CPU temp {0:s}'.format(templines[0].split(',')[0]))
plt.savefig("cpuTemp.png")
plt.show(block=False)

while (True):
  nscans = -1
  instr = input("starting, ending index (return to quit): ").split(',')
  if (instr[0] == ''): break
  istart = instr[0]
  iend = instr[1]

  # concatenate selected signal files into strsig
  strsig = ''
  for index in range(int(istart), int(iend)+1):
    print(sigfiles[index])
    infile = open(sigfiles[index], 'r')
    strsig += infile.read()
    
  # get number of freq bins from first record
  strlines = strsig.split('\n')
  fields = strlines[0].split(',')
  nfreq = len(fields) - 12
  print('{0:d} frequency bins'.format(nfreq))

  # the split results in an empty line at the end of strlines
  nrecs = len(strlines) - 1
  print('{0:d} scans'.format(nrecs))

  # get start/end date, time and freq from first and last records
  data = np.zeros(nfreq)
  scanTime = fields[0].split('.')[0]
  datetime = fields[0].split(' ')
  startdate = datetime[0]
  starttime = datetime[1].split('.')[0]
  startFreq = float(fields[2])
  endFreq = float(fields[5])

  fields = strlines[nrecs-1].split(',')
  datetime = fields[0].split(' ')
  enddate = datetime[0]
  endtime = datetime[1].split('.')[0]

  # construct image
  plotdata = np.full((nrecs,nfreq), -120)
  peakAmp = -120
  peakBin = 0
  peakRec = 0
  for rec in range(nrecs):
    fields = strlines[rec].split(',')
    nfreq = len(fields) - 12
    
    for bin in range(nfreq):
      amp = float(fields[12+bin])
      plotdata[rec,bin] = amp
      if (peakAmp < amp):
          peakAmp = amp
          peakBin = bin
          peakRec = rec


  # create plot
  deltaFreq = (endFreq - startFreq) / nfreq
  fignum += 1
  fig, ax = plt.subplots(num=fignum, figsize=(8,8))
  plt.imshow(plotdata,interpolation='nearest',cmap="hot")
  plt.xlabel('MHz')
  plt.ylabel('minutes')

  locs,labels = plt.xticks()                
  labels = ['{0:.1f}'.format(startFreq+locs[iTick]*deltaFreq) for iTick in range(len(labels))]
  ax.set_xticklabels(labels)

  tickIntvl = 6
  locs = range(0,nrecs,tickIntvl)
  ax.set_yticks(locs)
  labels = ['{0:d}'.format(iTick) for iTick in range(len(locs))]
  ax.set_yticklabels(labels)

  peakFreq = startFreq + (peakBin * deltaFreq)
  plt.title('{2:s}\npeak amp: {0:.1f}, freq: {1:.1f}, time: {3:.1f}'.format(peakAmp, peakFreq, str(scanTime).split('.')[0],peakRec/6.0))

  plt.savefig("RFimage.png")

  plt.show(block=False)
  

