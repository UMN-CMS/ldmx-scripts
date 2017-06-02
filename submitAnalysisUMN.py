#! /usr/bin/env python

import os,sys
import argparse
import commands
import random
import subprocess

from time import strftime

myTime = strftime("%H%M%S")
random.seed()

usage = "usage: %prog [options]"
parser = argparse.ArgumentParser(usage)
parser.add_argument("--endLayer"  , dest="endLayer"    , help="last layer of layer sum"       , default=16, type=int)
parser.add_argument("--inputDir"  , dest="inputDir"    , help="directory containing files"    , required=True)
parser.add_argument("--mode"      , dest="mode"        , help="trigger mode"                  , default=0, type=int)
parser.add_argument("--noLogging" , dest="noLogging"   , help="disable logging capabilities"  , default=False, action="store_true")
parser.add_argument("--noSubmit"  , dest="noSubmit"    , help="do not submit to cluster"      , default=False, action="store_true")
parser.add_argument("--numFiles"  , dest="numFiles"    , help="number of files to process"    , default=-1, type=int)
parser.add_argument("--outputDir" , dest="outputDir"   , help="directory to output ROOT files", required=True)
parser.add_argument("--perJob"    , dest="perJob"      , help="files per job"                 , default=1, type=int)
parser.add_argument("--startLayer", dest="startLayer"  , help="first layer of layer sum"      , default=1, type=int)
parser.add_argument("--threshold" , dest="threshold"   , help="layer energy sum cut"          , default=24) # Units of sim-MeV
arg = parser.parse_args()

inputDir    = arg.inputDir
numPerJob   = arg.perJob
inFileList  = os.listdir(inputDir)
outputDir   = arg.outputDir

# Figure number of files to process
if arg.numFiles == -1:
    numFiles = len(inFileList)
else:
    numFiles = arg.numFiles

# Check that the input and output directories exist
if not os.path.exists(inputDir):
    print "Provided root directory \"%s\" does not exist!"%(inputDir)
    print "Exiting..."
    quit()

if not os.path.exists(outputDir):
    print "Provided output directory \"%s\" does not exist!"%(outputDir)
    print "Exiting..."
    quit()

# Check that the input directory is not empty
if not os.listdir(inputDir):
    print "Provided input directory \"%s\" is empty!"%(inputDir)
    print "Exiting..."
    quit()

# Check for trailing slash on input and output directory and delete
if arg.inputDir.split("/")[-1] == "": inputDir = arg.inputDir[:-1]
if arg.outputDir.split("/")[-1] == "": outputDir = arg.outputDir[:-1]

# Check for temp directory and create one if none exists 
if not os.path.exists("./temp"): os.mkdir("temp")

workingDir = os.path.dirname(sys.argv[0])

# Write .sh file to be submitted to Condor
scriptFile = open("%s/runAnalysisJob_%s.sh"%(workingDir,myTime), "w")
scriptFile.write("#!/bin/bash\n\n")
scriptFile.write("hostname\n")
scriptFile.write("OUTPUTDIR=$1\n")
scriptFile.write("shift\n")
scriptFile.write("JOBNUM=$1\n")
scriptFile.write("shift\n")
scriptFile.write("INFILES=$@\n")
scriptFile.write("source ${HOME}/bin/ldmx-sw_setup.sh\n")
scriptFile.write("ldmx-app ${LDMXBASE}/ldmx-sw/ldmx-sw-install/my_standalone.py %s %s %s %s ${OUTPUTDIR} ${JOBNUM} ${INFILES}\n"%(arg.threshold,arg.startLayer,arg.endLayer,arg.mode))
scriptFile.close()
    
# Write Condor submit file
condorSubmit = open("%s/condorSubmit_%s"%(workingDir,myTime), "w")
condorSubmit.write("Executable          =  %s\n"%(scriptFile.name))
condorSubmit.write("Universe            =  vanilla\n")
condorSubmit.write("Requirements        =  Arch==\"X86_64\"  &&  (Machine  !=  \"zebra01.spa.umn.edu\")  &&  (Machine  !=  \"zebra02.spa.umn.edu\")  &&  (Machine  !=  \"zebra03.spa.umn.edu\")  &&  (Machine  !=  \"zebra04.spa.umn.edu\")\n")
condorSubmit.write("+CondorGroup        =  \"cmsfarm\"\n")
condorSubmit.write("getenv              =  True\n")
condorSubmit.write("Request_Memory      =  1 Gb\n")

numFilesProc = 0
jobNum = 0
iterator = 0
inFileStr = ""
for file in inFileList:

    if numFilesProc == numFiles:
        break

    inFileStr += "%s/%s "%(inputDir,file)
    numFilesProc += 1
    iterator += 1
    if iterator == numPerJob or numFilesProc == numFiles:

        if not arg.noLogging:
            condorSubmit.write("error  = %s/logs/%s.err\n"%(workingDir,jobNum))
            condorSubmit.write("output = %s/logs/%s.out\n"%(workingDir,jobNum))
            condorSubmit.write("Log    = %s/logs/%s.log\n"%(workingDir,jobNum))

        condorSubmit.write("Arguments = %s %s %s\n"%(outputDir+"/", jobNum, inFileStr))
        condorSubmit.write("Queue\n")

        jobNum += 1
        iterator = 0
        inFileStr = ""

condorSubmit.close()

os.system("chmod u+rwx %s/runAnalysisJob_%s.sh"%(workingDir,myTime))

if arg.noSubmit:
    quit()

command = "condor_submit " + condorSubmit.name + "\n"
subprocess.call(command.split())
