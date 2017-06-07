#!/usr/bin/env python

import os,sys
import math
import argparse
import commands
import random
import subprocess
from time import strftime

myTime = strftime("%H%M%S")
date_and_time=strftime("%Y_%b_%d_%H%M%S")
random.seed()

usage = "usage: %prog [options]"
parser = argparse.ArgumentParser(usage)
parser.add_argument("--doPileup"  , dest="doPileup"  , help="Inject n additional particles into event", default=0, type=int)
parser.add_argument("--enablePoisson" , dest="enablePoisson" , help="Poisson distribute number of e per event", default=False, action="store_true")
parser.add_argument("--geometry"  , dest="geometry"  , help="specify geometry version to use", default="v0", type=str)
parser.add_argument("--lheDir"    , dest="lheDir"    , help="directory containing .lhe files", default="/default/")
parser.add_argument("--noLogging" , dest="noLogging" , help="disable logging capabilities", default=False, action="store_true")
parser.add_argument("--noSubmit"  , dest="noSubmit"  , help="do not submit to cluster", default=False, action="store_true")
parser.add_argument("--numEvents" , dest="numEvents" , help="number of events per job"      , default=100, type=int)
parser.add_argument("--numJobs"   , dest="numJobs"   , help="number of jobs to run"         , default=1, type=int)
parser.add_argument("--outputDir" , dest="outputDir" , help="output directory for root files", default="/local/cms/user/%s/LDMX"%(os.environ['USER']))
parser.add_argument("--jobname", dest="jobname", help="job name to be used for directories and root files", required=True)
parser.add_argument("--particle"  , dest="particle"  , help="choose beam particle via pdgID (not pileup!)", default=0, type=int)
parser.add_argument("--smearBeam" , dest="smearBeam" , help="smear the beamspot", default=False, action="store_true")
arg = parser.parse_args()

outputDir = arg.outputDir+"/"+arg.jobname
workingDir = "/export/scratch/users/%s"%(os.environ['USER'])

print os.path.expanduser("LDMX")

beamEnergy = 4.0 # In GeV

# Do some basic checks on integer arguments
if arg.numEvents < 0:
    print "\nNumber of events per job must be a positive integer!"
    print "Exiting..."
    quit()

if arg.numJobs < 0:
    print "\nNumber of jobs must be a positive integer!"
    print "Exiting..."
    quit()

if arg.doPileup < 0:
    print "\nNumber of particles per event must be a positive integer!"
    print "Exiting..."
    quit()

# Check that the output directory exist
os.makedirs(outputDir)
if not os.path.exists(outputDir):
    print "\nUnable to create output directory \"%s\""%(outputDir)
    print "Exiting..."
    quit()

# Check for trailing slash on outputDir and delete
if arg.outputDir.split("/")[-1] == "": outputDir = arg.outputDir[:-1]

if arg.lheDir != "/default/":

    # Check that the input .lhe directory exists
    if not os.path.exists(arg.lheDir):
        print "\nProvided input .lhe directory \"%s\" does not exist!"%(arg.lheDir)
        print "Exiting..."
        quit()
    
    # Strip trailing slash from .lhe directory
    if arg.lheDir.split("/")[-1] == "": lheDir = arg.lheDir[:-1]

outTag = "%d_%gGeV_%s_electrons"%(arg.numEvents,beamEnergy,arg.geometry)

if not arg.noLogging:
# Check for existence of logs directory and create one if none is found
	if not os.path.exists("%s/logs"%(workingDir)): os.mkdir("%s/logs"%(workingDir))

#if arg.doPileup >= 0 and arg.particle != 0:
#    outTag = "%d_%gGeV_%s_electrons"%(arg.numEvents,beamEnergy,arg.geometry)
#
#    # Determine which particle the user selected, NOT USED FOR NOW!!
#    if arg.particle == 11:
#        fileoutBase = "electrons"
#        outTag      = outTag+"electrons"
#        p           = math.pow((math.pow(beamEnergy,2) - math.pow(0.000510999,2)),0.5)
#    elif arg.particle == 13:
#        fileoutBase = "muons"
#        outTag      = outTag+"muons"
#        p           = math.pow((math.pow(beamEnergy,2) - math.pow(0.10565837,2)),0.5) 
#    elif arg.particle == 12:
#        fileoutBase = "neutrinos"
#        outTag      = outTag+"neutrinos"
#        p           = beamEnergy
#    elif arg.particle == 2112:
#        fileoutBase = "neutrons"
#        outTag      = outTag+"neutrons"
#        p           = math.pow((math.pow(beamEnergy,2) - math.pow(0.9395654,2)),0.5) 
#    elif arg.particle == 22:
#        fileoutBase = "photons"
#        outTag      = outTag+"photons"
#        p           = beamEnergy
#    else:
#        print "\nInvalid particle selected.\n"
#        print "Usage can include:\n"
#        print "11   for electron"
#        print "12   for neutrino"
#        print "13   for muon"
#        print "2112 for neutron"
#        print "22   for photon\n"
#        quit()
#    
#    px = p*math.sin(math.radians(4.5))*math.cos(math.radians(0))
#    py = p*math.sin(math.radians(4.5))*math.sin(math.radians(0))
#    pz = p*math.cos(math.radians(4.5))
  
# Write .sh script to be run by Condor
condorDir="%s/condor"%(outputDir)
os.makedirs(condorDir) # make the script and condor directory

scriptFile = open("%s/runJob.sh"%(condorDir), "w")
scriptFile.write("#!/bin/bash\n\n")
scriptFile.write("STUBNAME=$1\n")
scriptFile.write("OUTPATH=$2\n")

# Create directories to save log, submit, and mac files if they don't already exist
#if not os.path.exists("${HOME}/../../local/cms/user/${USER}/LDMX/condor_jobs/%s/condor_submits"%(date_and_time)): scriptFile.write("mkdir ${HOME}/../../local/cms/user/${USER}/LDMX/condor_jobs/%s/condor_submits\n"%(date_and_time))
#if not os.path.exists("${HOME}/../../local/cms/user/${USER}/LDMX/condor_jobs/%s/macs"%(date_and_time)): scriptFile.write("mkdir ${HOME}/../../local/cms/user/${USER}/LDMX/condor_jobs/%s/macs\n"%(date_and_time))
logDir="%s/logs"%(outputDir)
os.makedirs(logDir) # make the log directory
macDir="%s/mac"%(outputDir)
os.makedirs(macDir) # make the mac directory

scriptFileName=scriptFile.name
scriptFile.write("mkdir -p %s;cd %s\nmkdir ${STUBNAME}\ncd ${STUBNAME}\n"%(workingDir,workingDir))
scriptFile.write("hostname > ${STUBNAME}.log\n")
scriptFile.write("source ${HOME}/bin/ldmx-sw_setup.sh >> ${STUBNAME}.log 2>>${STUBNAME}.err\n")
scriptFile.write("ln -s ${LDMXBASE}/ldmx-sw/BmapCorrected3D_13k_unfolded_scaled_1.15384615385.dat .\n")
scriptFile.write("ln -s ${LDMXBASE}/ldmx-sw/Detectors/data/ldmx-det-full-%s-fieldmap/* .\n"%(arg.geometry))
scriptFile.write("ldmx-sim ${OUTPATH}/mac/${STUBNAME}.mac >> ${STUBNAME}.log 2>>${STUBNAME}.err\n")
scriptFile.write("cp ldmx_sim_events.root ${OUTPATH}/${STUBNAME}.root >> ${STUBNAME}.log 2>>${STUBNAME}.err\n")
scriptFile.write("xz *.log *.err\n")
scriptFile.write("cp *.xz ${OUTPATH}/logs\n")
scriptFile.write("#cd .. && rm -r ${STUBNAME}\n")
scriptFile.close()

# Write Condor submit file 
condorSubmit = open("%s/condorSubmit"%(condorDir), "w")
condorSubmit.write("Executable          =  %s\n"%(scriptFile.name))
condorSubmit.write("Universe            =  vanilla\n")
condorSubmit.write("Requirements        =  Arch==\"X86_64\"  &&  (Machine  !=  \"scorpion6.spa.umn.edu\")  &&  (Machine  !=  \"zebra02.spa.umn.edu\")  &&  (Machine  !=  \"zebra03.spa.umn.edu\")  &&  (Machine  !=  \"zebra04.spa.umn.edu\")\n")
condorSubmit.write("+CondorGroup        =  \"cmsfarm\"\n")
condorSubmit.write("getenv              =  True\n")
condorSubmit.write("Request_Memory      =  1 Gb\n")

ijob=0
if arg.lheDir != "/default/":
    for file in os.listdir(arg.lheDir):
    	stubname="%s_%04d"%(arg.jobname,ijob)
        filename = file.split(".lhe")[0]

        condorSubmit.write("Arguments       = %s %s\n"%(stubname,outputDir))
        condorSubmit.write("Queue\n")

        g4Macro = open("%s/%s.mac"%(macDir,stubname),"w")
        g4Macro.write("/persistency/gdml/read detector.gdml\n")
        g4Macro.write("/run/initialize\n")
        g4Macro.write("\n/ldmx/generators/lhe/open %s/%s\n"%(arg.lheDir,file))

        if arg.doPileup > 0:
            g4Macro.write("\n/ldmx/generators/mpgun/enable\n")
            if arg.enablePoisson:
                g4Macro.write("\n/ldmx/generators/mpgun/enablePoisson\n")

            g4Macro.write("/ldmx/generators/mpgun/nInteractions %s\n"%(arg.doPileup+1))
            g4Macro.write("/ldmx/generators/mpgun/pdgID 11\n")
            g4Macro.write("/ldmx/generators/mpgun/vertex -27.9260 5 -700 mm\n")
            g4Macro.write("/ldmx/generators/mpgun/momentum 0.31384 0 3.98766 GeV\n")

            if arg.smearBeam:
                g4Macro.write("\n/ldmx/generators/beamspot/enable\n")
                g4Macro.write("/ldmx/generators/beamspot/sizeX 15.0\n")
                g4Macro.write("/ldmx/generators/beamspot/sizeY 35.0\n")

        g4Macro.write("\n/random/setSeeds %d %d\n"%(random.uniform(0,100000000),random.uniform(0,100000000)))
        g4Macro.write("/run/beamOn %d\n"%(arg.numEvents))
        g4Macro.close()
	ijob=ijob+1
    
else:
    for job in xrange(0, arg.numJobs):
        stubname="%s_%04d"%(arg.jobname,job)
    
        condorSubmit.write("Arguments       = %d %s\n"%(stubname,outputDir))
        condorSubmit.write("Queue\n")
    
        # Write GEANT4 macro for each job
        g4Macro = open("%s/%s.mac"%(macDir,stubname), "w")
        g4Macro.write("/persistency/gdml/read detector.gdml\n")
        g4Macro.write("/run/initialize\n") 
        g4Macro.write("\n/ldmx/generators/mpgun/enable\n")

        if arg.enablePoisson:
            g4Macro.write("/ldmx/generators/mpgun/enablePoisson\n")

        g4Macro.write("/ldmx/generators/mpgun/nInteractions %s\n"%(arg.doPileup+1))
        g4Macro.write("/ldmx/generators/mpgun/pdgID 11\n")
        g4Macro.write("/ldmx/generators/mpgun/vertex -27.9260 5 -700 mm\n")
        g4Macro.write("/ldmx/generators/mpgun/momentum 0.31384 0 3.98766 GeV\n")

        # Beam spot dimensions are in mm
        if arg.smearBeam:
            g4Macro.write("\n/ldmx/generators/beamspot/enable\n")
            g4Macro.write("/ldmx/generators/beamspot/sizeX 15.0\n")
            g4Macro.write("/ldmx/generators/beamspot/sizeY 35.0\n")

        g4Macro.write("\n/random/setSeeds %d %d\n"%(random.uniform(0,100000000),random.uniform(0,100000000)))
        g4Macro.write("/run/beamOn %d\n"%(arg.numEvents))
        g4Macro.close()

condorSubmit.close()

os.system("chmod u+rwx %s"%(scriptFileName))

if arg.noSubmit:
    quit()

command = "condor_submit " + condorSubmit.name + "\n"
subprocess.call(command.split())
