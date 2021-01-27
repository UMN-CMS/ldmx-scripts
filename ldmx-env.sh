#!/bin/bash

# SUGGESTION:
#   Put the following command in your .bashrc file to make setting up
#   the ldmx environment easier
#   alias ldmx-env='source <path-to-this-file>/ldmx-env.sh'

# get the directory of this script
export LDMX_ENV_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"

# This is the full path to the directory containing ldmx-sw
export LDMX_BASE="$( cd "${LDMX_ENV_DIR}/../" &>/dev/null && pwd)"

# installation prefix for ldmx-sw
export LDMX_INSTALL_PREFIX="$LDMX_BASE/ldmx-sw/install"

## Setup LDMX dependencies
if ! source ${LDMX_ENV_DIR}/ldmx-setup-deps.sh
then
  echo "Error setting up dependencies."
  return 1
fi

### Helpful Aliases and Bash Functions
# cmake command required to be done before make to build ldmx-sw
# WARNING: must be in $LDMX_BASE/ldmx-sw/build directory when you run cmake
#   if you run it outside of build directory and it completes, 
#   you will need to git reset and git clean to remove
#   the build files that are mixed with the source files
function ldmx-cmake {
  (set -x; cmake -DCMAKE_INSTALL_PREFIX=$LDMX_INSTALL_PREFIX "$@" ../;)
}

function ldmx-ana-cmake {
  (set -x; cmake -DLDMXSW_INSTALL_PREFIX=$LDMX_INSTALL_PREFIX "$@" ../;)
}

# prepends fire with valgrind to check for memory leaks
alias ldmx-val='valgrind --tool=memcheck --leak-check=yes --suppressions=$ROOTSYS/etc/root/valgrind-root.supp --log-file=memcheck.log fire'

# skips directories that aren't modules
#   now run 'grepmodules <pattern>' in ldmx-sw/ to search for a <pattern> in the module source files
alias grepmodules='grep --exclude-dir=build --exclude-dir=docs --exclude-dir=install --exclude-dir=.git -rHn'

# setup the condor batch environemtn
alias ldmx-condor-env='source $LDMX_ENV_DIR/batch/condor_env.sh'

# remove all the files listed in install_manifest.txt
alias ldmx-clean-install='xargs rm < install_manifest.txt'
