#!/usr/bin/env python

import os,sys
import math
import argparse
import commands
import random
import subprocess
from time import strftime

myTime = strftime("%H%M%S")
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
parser.add_argument("--outputDir" , dest="outputDir" , help="output directory for root files", required=True)
parser.add_argument("--particle"  , dest="particle"  , help="choose beam particle via pdgID (not pileup!)", default=0, type=int)
parser.add_argument("--smearBeam" , dest="smearBeam" , help="smear the beamspot", default=False, action="store_true")
arg = parser.parse_args()

outputDir = arg.outputDir
ldmxBase = "/home/hiltbran/Projects/LDMX"
workingDir = os.path.dirname(sys.argv[0])

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
if not os.path.exists(outputDir):
    print "\nProvided output directory \"%s\" does not exist!"%(outputDir)
    print "Exiting..."
    quit()

# Check for trailing slash on outputDir and delete
if arg.outputDir.split("/")[-1] == "": outputDir = arg.outputDir[:-1]

# Check for existence of temp directory and create one if none is found
if not os.path.exists("%s/temp"%(workingDir)): os.mkdir("%s/temp"%(workingDir))

if arg.lheDir != "/default/":

    # Check that the input .lhe directory exists
    if not os.path.exists(arg.lheDir):
        print "\nProvided input .lhe directory \"%s\" does not exist!"%(arg.lheDir)
        print "Exiting..."
        quit()
    
    # Strip trailing slash from .lhe directory
    if arg.lheDir.split("/")[-1] == "": lheDir = arg.lheDir[:-1]

outTag = "%d_%gGeV_%s_electrons"%(arg.numEvents,beamEnergy,arg.geometry)

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
scriptFile = open("%s/runJob_%s.sh"%(workingDir,myTime), "w")
scriptFile.write("#!/bin/bash\n\n")
if arg.lheDir != "/default/":
    scriptFile.write("NAME=$1\n")
    scriptFile.write("UNIQUEDIR=${NAME}_%s\n"%(myTime))
    scriptFile.write("OUTFILENAME=${NAME}\n")
   
else:
    scriptFile.write("JOB=$1\n")
    scriptFile.write("NAME=$2\n")
    scriptFile.write("UNIQUEDIR=${NAME}_${JOB}_%s\n"%(myTime))
    scriptFile.write("OUTFILENAME=%s_${JOB}_%s\n"%(outTag, myTime))

scriptFile.write("LDMXDIR=\"%s\"\n"%(ldmxBase))
scriptFile.write("hostname\n")
scriptFile.write("source ${LDMXDIR}/ldmx-sw_setup.sh\n")
scriptFile.write("cd temp && mkdir ${UNIQUEDIR} && cd ${UNIQUEDIR}\n")
scriptFile.write("ln -s ${LDMXDIR}/ldmx-sw/BmapCorrected3D_13k_unfolded_scaled_1.15384615385.dat .\n")
scriptFile.write("ln -s ${LDMXDIR}/ldmx-sw/Detectors/data/ldmx-det-full-%s-fieldmap/* .\n"%(arg.geometry))
scriptFile.write("ln -s ${LDMXDIR}/ldmx-sw/ldmx-sw-install/bin/ldmx-sim .\n")
scriptFile.write("mv %s/../../ldmxsteer_${UNIQUEDIR}.mac ldmxsteer.mac\n"%(workingDir))
scriptFile.write("./ldmx-sim ldmxsteer.mac\n")
scriptFile.write("cp ldmx_sim_events.root %s/${OUTFILENAME}.root && cd .. && rm -r ${UNIQUEDIR}\n"%(outputDir))
scriptFile.write("cd ../..\n")
scriptFile.close()

# Write Condor submit file 
condorSubmit = open("%s/condorSubmit_%s"%(workingDir,myTime), "w")
condorSubmit.write("Executable          =  %s\n"%(scriptFile.name))
condorSubmit.write("Universe            =  vanilla\n")
condorSubmit.write("Requirements        =  Arch==\"X86_64\"  &&  (Machine  !=  \"zebra01.spa.umn.edu\")  &&  (Machine  !=  \"zebra02.spa.umn.edu\")  &&  (Machine  !=  \"zebra03.spa.umn.edu\")  &&  (Machine  !=  \"zebra04.spa.umn.edu\")\n")
condorSubmit.write("+CondorGroup        =  \"cmsfarm\"\n")
condorSubmit.write("getenv              =  True\n")
condorSubmit.write("Request_Memory      =  1 Gb\n")

if arg.lheDir != "/default/":
    for file in os.listdir(lheDir):
        filename = file.split(".lhe")[0]

        condorSubmit.write("Arguments       = %s\n"%(filename))
        condorSubmit.write("Queue\n")

        g4Macro = open("%s/ldmxsteer_%s_%s.mac"%(workingDir,filename,myTime),"w")
        g4Macro.write("/persistency/gdml/read detector.gdml\n")
        g4Macro.write("/run/initialize\n")
        g4Macro.write("\n/ldmx/generators/lhe/open %s/%s\n"%(lheDir,file))

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
                g4Macro.write("/ldmx/generators/beamspot/sizeX 20.0\n")
                g4Macro.write("/ldmx/generators/beamspot/sizeY 10.0\n")

        g4Macro.write("\n/random/setSeeds %d %d\n"%(random.uniform(0,100000000),random.uniform(0,100000000)))
        g4Macro.write("/run/beamOn %d\n"%(arg.numEvents))
        g4Macro.close()
    
else:
    for job in xrange(0, arg.numJobs):
    
        # Append jobs to Condor submit file 
        if not arg.noLogging:
            condorSubmit.write("error               =  %s/logs/%s.err\n"%(workingDir,job))
            condorSubmit.write("output              =  %s/logs/%s.out\n"%(workingDir,job))
            condorSubmit.write("Log                 =  %s/logs/%s.log\n"%(workingDir,job))
    
        condorSubmit.write("Arguments       = %d %s\n"%(job,outTag))
        condorSubmit.write("Queue\n")
    
        # Write GEANT4 macro for each job
        g4Macro = open("%s/ldmxsteer_%s_%d_%s.mac"%(workingDir,outTag,job,myTime), "w")
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
            g4Macro.write("/ldmx/generators/beamspot/sizeX 20.0\n")
            g4Macro.write("/ldmx/generators/beamspot/sizeY 10.0\n")

        g4Macro.write("\n/random/setSeeds %d %d\n"%(random.uniform(0,100000000),random.uniform(0,100000000)))
        g4Macro.write("/run/beamOn %d\n"%(arg.numEvents))
        g4Macro.close()

condorSubmit.close()

os.system("chmod u+rwx %s/runJob_%s.sh"%(workingDir,myTime))

if arg.noSubmit:
    quit()

command = "condor_submit " + condorSubmit.name + "\n"
subprocess.call(command.split())
