#!/bin/bash

# installation prefix for ldmx-sw
export LDMX_INSTALL_PREFIX="INSTALL_DIR"

## Setup LDMX dependencies
#   The two arguments are the versions of geant4 and root you want.
#   The options can be found at
#     /local/cms/user/eichl008/install-test/local/cms/other/{geant4,root}
#
#   Geant4
#     "geant4.10.02.p03_v0.3-gcc821-cxx17" 
#     "geant4.10.02.p03_v0.3-gcc821"
#     "geant4.10.05.p01-gcc821" 
#
#   root
#     "6.16.00-gcc821"
#     "6.16.00-gcc821-cxx17"
#     "6.20.00-gcc821-cxx17"
#     "6.22.00-gcc821-cxx17"

if ! source ${LDMX_INSTALL_PREFIX}/ldmx-setup-deps.sh "geant4.10.02.p03_v0.3-gcc821" "6.20.00-gcc821-cxx17"
then
  echo "Error setting up dependencies."
  return 1
fi

