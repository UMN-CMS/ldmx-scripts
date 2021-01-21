#!/bin/bash

################################################################################
# Setup "Container" environment for ldmx-sw
################################################################################

# get the directory of this script
export LDMX_CONTAINER_ENV_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"

# Setup dependencies, 
#   Point everything to the installs in the "container"
#   Defines location of "container" to be LDMX_CONTAINER_DIR
source $LDMX_CONTAINER_ENV_DIR/setup.sh

# Pack container currently in LDMX_CONTAINER_DIR
ldmx-container-pack() {
  _old_pwd=$OLDPWD
  _pwd=$PWD
  cd $LDMX_CONTAINER_DIR
  cp $LDMX_CONTAINER_ENV_DIR/setup.sh .
  cp $LDMX_CONTAINER_ENV_DIR/../batch/run_fire.sh .
  cd ..
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
    -name "gabrielle.onnx" -o \
    -name "cellxy.txt" -o \
    -name "setup.sh" -o \
    -name "run_fire.sh" | \
    tar \
      --create \
      --file ldmx-container.tar.gz \
      -T -
  mv ldmx-container.tar.gz $(realpath $_pwd/"$1")
  cd $_pwd
  export OLDPWD=$_old_pwd
}

# Check host for container
#   Not working because tar does not preserve GID across different filesystems
ldmx-container-check() {
  _container=$(realpath "$1")
  _host="$2"
  echo -n "$_host..."
  if ssh -q $_host "cd /export/scratch/users/eichl008 && tar -df $_container ldmx-container/"; then
    echo "good"
  else
    echo "bad"
  fi
}

# Internal deploy command that is quiet
internal-ldmx-container-deploy() {
  _container=$(realpath "$1")
  _host="$2"
  if ssh -q $_host "mkdir -p /export/scratch/users/eichl008 && cd /export/scratch/users/eichl008 && if [[ -d ldmx-container ]]; then rm -rf ldmx-container; fi && tar xf $_container"; then
    return 0
  else
    export _failed_deployments="$_failed_deployments $_host"
    return 1
  fi
}

# Test that the input config can run on the input host
ldmx-container-test() {
  _host="$1"
  _config=$(realpath "$2")
  _args="{@:3}"
  ssh $_host $LDMX_CONTAINER_DIR/run_fire TEST $LDMX_CONTAINER_DIR/setup.sh $_config $(pwd) $_args
}

# Fully deploy the input container to all worker nodes
#   we assume container is on hdfs so multiple machines can read from it no problem
ldmx-container-deploy() {
  export _failed_deployments=""
  echo -n "deploying..."
  for _host in ${@:2}; do
    internal-ldmx-container-deploy $1 $_host &
    sleep 1
  done
  wait
  echo "done"
  if [[ ! -z "$_failed_deployments" ]]; then
    echo "Failed to deploy to:$_failed_deployments"
  fi
  unset _failed_deployments
}
