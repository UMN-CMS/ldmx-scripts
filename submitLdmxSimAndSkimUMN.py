#!/usr/bin/env python

import os,sys
import math
import argparse
import commands
import random
import subprocess
from time import strftime

random.seed()

usage = "usage: %prog [options]"
parser = argparse.ArgumentParser(usage)
parser.add_argument("--doPileup"  , dest="doPileup"  , help="Inject n additional particles into event", default=0, type=int)
parser.add_argument("--enablePoisson" , dest="enablePoisson" , help="Poisson distribute number of e per event", default=False, action="store_true")
parser.add_argument("--geometry"  , dest="geometry"  , help="specify geometry version to use", default="v3", type=str)
parser.add_argument("--lheDir"    , dest="lheDir"    , help="directory containing .lhe files", default="/default/")
parser.add_argument("--noLogging" , dest="noLogging" , help="disable logging capabilities", default=False, action="store_true")
parser.add_argument("--noSubmit"  , dest="noSubmit"  , help="do not submit to cluster", default=False, action="store_true")
parser.add_argument("--numEvents" , dest="numEvents" , help="number of events per job"      , required=True, type=int)
parser.add_argument("--numJobs"   , dest="numJobs"   , help="number of jobs to run"         , default=-1, type=int)
parser.add_argument("--jobname", dest="jobname", help="job name to be used for directories and root files", required=True)
parser.add_argument("--smearBeam" , dest="smearBeam" , help="smear the beamspot", action="store_true")
parser.add_argument("--noPN" , dest="noPN" , help="disable the photonNuclear, electronNulcear, and positronNuclear processes", action="store_true")
parser.add_argument("--nonice" , dest="nonice" , help="Do not run this at nice priority", action="store_true")
arg = parser.parse_args()

print "Using %s geometry"%(arg.geometry)

workingDir = "/export/scratch/users/%s"%(os.environ['USER'])

# Do some basic checks on integer arguments
if arg.numEvents < 0:
    print "\nNumber of events per job must be a positive integer!"
    print "Exiting..."
    quit()

if arg.doPileup < 0:
    print "\nNumber of particles per event must be a positive integer!"
    print "Exiting..."
    quit()

# make the output directory
outputDir = "/local/cms/user/%s/LDMX/simulation"%(os.environ['USER'])+arg.jobname
os.makedirs(outputDir)
if not os.path.exists(outputDir):
    print "\nUnable to create output directory \"%s\""%(outputDir)
    print "Exiting..."
    quit()

if arg.lheDir != "/default/":
    # Check that the input .lhe directory exists
    if not os.path.exists(arg.lheDir):
        print "\nProvided input .lhe directory \"%s\" does not exist!"%(arg.lheDir)
        print "Exiting..."
        quit()
    # Strip trailing slash from lhe directory
    if arg.lheDir.split("/")[-1] == "": lheDir = arg.lheDir[:-1]

# make condor, logs, and mac directories
condorDir="%s/condor"%(outputDir)
os.makedirs(condorDir)
logDir="%s/logs"%(outputDir)
os.makedirs(logDir)
macDir="%s/mac"%(outputDir)
os.makedirs(macDir)

# Write .sh script to be run by Condor
scriptFile = open("%s/runJob.sh"%(condorDir), "w")
scriptFile.write("#!/bin/bash\n\n")
scriptFile.write("STUBNAME=$1\n")
scriptFile.write("OUTPATH=$2\n")

# write the runJob.sh script
scriptFileName=scriptFile.name
scriptFile.write("mkdir -p %s;cd %s\nmkdir ${STUBNAME}\ncd ${STUBNAME}\n"%(workingDir,workingDir))
scriptFile.write("hostname > ${STUBNAME}.log\n")
scriptFile.write("source ${HOME}/bin/ldmx-sw_setup.sh >> ${STUBNAME}.log 2>>${STUBNAME}.err\n")
scriptFile.write("ln -s ${LDMXBASE}/ldmx-sw/BmapCorrected3D_13k_unfolded_scaled_1.15384615385.dat .\n")
scriptFile.write("ln -s ${LDMXBASE}/ldmx-sw/Detectors/data/ldmx-det-full-%s-fieldmap/* .\n"%(arg.geometry))
scriptFile.write("date >> ${STUBNAME}.log\n")
scriptFile.write("ldmx-sim ${OUTPATH}/mac/${STUBNAME}.mac >> ${STUBNAME}.log 2>>${STUBNAME}.err\n")
scriptFile.write("date >> ${STUBNAME}.log\n")
scriptFile.write("ldmx-app ${OUTPATH}/mac/skim.py >> ${STUBNAME}.log 2>>${STUBNAME}.err\n")
scriptFile.write("date >> ${STUBNAME}.log\n")
scriptFile.write("cp ldmx_skim_events.root ${OUTPATH}/${STUBNAME}.root >> ${STUBNAME}.log 2>>${STUBNAME}.err\n")
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
if not (arg.nonice):
    condorSubmit.write("nice_user = True\n")
condorSubmit.write("Request_Memory      =  1 Gb\n")

# determine the number of jobs to run
if arg.numJobs > 0:
	numJobs = arg.numJobs
elif arg.lheDir != "/default/":
	numJobs = len(os.listdir(arg.lheDir))
else:
	numJobs = 1
# write the mac file
for job in range(numJobs):
    stubname="%s_%04d"%(arg.jobname,job)
    condorSubmit.write("Arguments       = %s %s\n"%(stubname,outputDir))
    condorSubmit.write("Queue\n")
    g4Macro = open("%s/%s.mac"%(macDir,stubname),"w")
    g4Macro.write("/persistency/gdml/read detector.gdml\n\n")
    if arg.noPN:
        g4Macro.write("/ldmx/plugins/load DisablePhotoNuclear libSimPlugins.so\n\n")
    g4Macro.write("/run/initialize\n\n")
    if arg.lheDir != "/default/":
        g4Macro.write("/ldmx/generators/lhe/open %s/%s\n\n"%(arg.lheDir,os.listdir(arg.lheDir)[job-job/len(os.listdir(arg.lheDir))]))
    if arg.smearBeam:
        g4Macro.write("/ldmx/generators/beamspot/enable\n")
        g4Macro.write("/ldmx/generators/beamspot/sizeX 15.0\n")
        g4Macro.write("/ldmx/generators/beamspot/sizeY 35.0\n\n")

    if arg.doPileup > 0 or arg.lheDir == "/default/":
        g4Macro.write("\n/ldmx/generators/mpgun/enable\n")
        if arg.enablePoisson:
            g4Macro.write("/ldmx/generators/mpgun/enablePoisson\n\n")

	g4Macro.write("/ldmx/generators/mpgun/nInteractions %s\n"%(arg.doPileup+1))
        g4Macro.write("/ldmx/generators/mpgun/pdgID 11\n")
        g4Macro.write("/ldmx/generators/mpgun/vertex 0 0 1 mm\n")
        g4Macro.write("/ldmx/generators/mpgun/momentum 0 0 3.9999999673 GeV\n")

    g4Macro.write("\n/random/setSeeds %d %d\n"%(random.uniform(0,100000000),random.uniform(0,100000000)))
    g4Macro.write("/run/beamOn %d\n"%(arg.numEvents))
    g4Macro.close()

#just one skim file!
skimPy=open("%s/skim.py"%(macDir),"w")
skimPy.write("""#!/usr/bin/python

import sys
import os

# we need the ldmx configuration package to construct the object
from LDMX.Framework import ldmxcfg

p = ldmxcfg.Process("recon")
p.libraries.append("libEventProc.so")

ecalDigiProd = ldmxcfg.Producer("ecalDigiProd", "ldmx::EcalDigiProducer")
triggerProd = ldmxcfg.Producer("triggerProd", "ldmx::TriggerProcessor")

ecalDigiProd.parameters["meanNoise"] = 0.015
ecalDigiProd.parameters["readoutThreshold"] = ecalDigiProd.parameters["meanNoise"]*3

numLayers = 33
triggerProd.parameters["threshold"]   = 2800.0
triggerProd.parameters["start_layer"] = 0
triggerProd.parameters["end_layer"]   = numLayers
triggerProd.parameters["mode"]        = 0
triggerProd.parameters["padThresh"]   = 0.1

p.sequence = [ecalDigiProd,triggerProd]

p.inputFiles.append("ldmx_sim_events.root")
p.outputFiles.append("ldmx_skim_events.root")

# drop the events by default
p.skimDefaultIsDrop()
# consider just this module for the decision
p.skimConsider("triggerProd")
""")
skimPy.close()
    
condorSubmit.close()

os.system("chmod u+rwx %s"%(scriptFileName))

if arg.noSubmit:
    quit()

command = "condor_submit " + condorSubmit.name + "\n"
subprocess.call(command.split())
