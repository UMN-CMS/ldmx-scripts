#!/bin/bash

################################################################################
# Setup "Container" environment for ldmx-sw
################################################################################

# Setup dependencies, point everything to the installs in the "container"
source $LDMX_ENV_DIR/container/setup.sh

# Pack container currently in LDMX_CONTAINER_DIR
ldmx-container-pack() {
  _old_pwd=$OLDPWD
  _pwd=$PWD
  cd $LDMX_CONTAINER_DIR/../
  find ldmx-container/ \
    -path "*/lib/*" -o \
    -path "*/lib64/*" -o \
    -path "*/bin/*" -o \
    -path "*root/include*" -o \
    -path "*root/etc*" -o \
    -path "*ldmx-sw/include*" -o \
    -path "*ldmx-sw/python*" -o \
    -path "*ldmx-det-v12*" -o \
    -path "*fieldmap*" -o \
    -name "setup.sh" -o \
    -name "run_fire.sh" | tar czvf ldmx-container.tar.gz -T -
  mv ldmx-container.tar.gz $(realpath $_pwd/"$1")
  cd $_pwd
  export OLDPWD=$_old_pwd
}

# Deploy the input container to the input host
deploy() {
  _container=$(realpath "$1")
  _host="$2"
  ssh -q $_host "mkdir -p /export/scratch/users/eichl008 && cd /export/scratch/users/eichl008 && tar xf $_container"
}
