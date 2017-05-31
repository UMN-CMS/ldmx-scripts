#!bin/bash

LDMXBASE="${HOME}/Projects/LDMX/"
ROOTDIR="/local/cms/other/root"
G4DIR="/local/cms/other/geant4"
CVMFSDIR="/cvmfs/cms.cern.ch/slc6_amd64_gcc493/external"

source /cvmfs/cms.cern.ch/slc6_amd64_gcc493/external/cmake/3.5.2/etc/profile.d/init.sh
source /cvmfs/cms.cern.ch/slc6_amd64_gcc493/external/xerces-c/3.1.3/etc/profile.d/init.sh
source /cvmfs/cms.cern.ch/slc6_amd64_gcc493/external/bz2lib/1.0.5/etc/profile.d/init.sh
source /cvmfs/cms.cern.ch/slc6_amd64_gcc493/external/python/2.7.11/etc/profile.d/init.sh
source /cvmfs/cms.cern.ch/slc6_amd64_gcc493/external/zlib/1.2.8/etc/profile.d/init.sh
source /cvmfs/cms.cern.ch/slc6_amd64_gcc493/external/gcc/4.9.3/etc/profile.d/init.sh

source /local/cms/other/root/6.06.08/bin/thisroot.sh
source /local/cms/other/geant4/geant4.10.02.p02/setup.sh

export G4ENSDFSTATEDATA=${G4DIR}/geant4.10.02.p02/share/Geant4-10.2.2/data/G4ENSDFSTATE1.2.3

export LD_LIBRARY_PATH=${LDMXBASE}/ldmx-sw/ldmx-sw-install/lib:${ROOTDIR}/6.06.08/lib:${G4DIR}/geant4.10.02.p02/lib64:${CVMFSDIR}/xerces-c/3.1.3/lib:${CVMFSDIR}/gcc/4.9.3/lib:${CVMFSDIR}/gcc/4.9.3/lib64:${LD_LIBRARY_PATH}

export PYTHONPATH=${LDMXBASE}/ldmx-sw/ldmx-sw-install/lib/python:$PYTHONPATH

export PATH=${LDMXBASE}/ldmx-sw/ldmx-sw-install/bin:$PATH
