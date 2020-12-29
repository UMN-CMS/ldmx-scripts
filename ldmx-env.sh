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

if ! source ${LDMX_ENV_DIR}/ldmx-setup-deps.sh "geant4.10.02.p03_v0.3-gcc821" "6.20.00-gcc821-cxx17"
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

# total remake command
# nuclear option
#   deletes ldmx install
#   goes to build directory, completely deletes old build, 
#   re-executes cmake and make, returns to prior directory
ldmx-remake() {
  rm -rf $LDMX_INSTALL_PREFIX &&
  cd $LDMX_BASE/ldmx-sw/build &&
  rm -r * &&
  ldmxcmake &&
  make install -j8 &&
  cd -
}

# setup the condor batch environemtn
alias ldmx-condor-env='source $LDMX_ENV_DIR/batch/condor_env.sh'

