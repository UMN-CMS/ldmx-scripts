#!/bin/bash

# installation prefix for ldmx-sw
export LDMX_INSTALL_PREFIX="INSTALL_DIR"

## Setup LDMX dependencies
if ! source ${LDMX_INSTALL_PREFIX}/ldmx-setup-deps.sh 
then
  echo "Error setting up dependencies."
  return 1
fi

