#!/bin/bash

###################################################################################################
# hgcroc.sh - start up interaction with HGC ROC
#
#   ASSUMPTIONS
#   - cmslab is a ssh 'alias' for the cmslab computer the user has access to.
#   - hgcroc is an ssh 'alias' on cmslab for the computer connected to the HGC ROC.
#   - Environmental setup is for the hexactrl-sw and hexactrl-script repositories has been
#     inserted into the '~/.bashrc' on hgcroc for the user using this script.
#   - User can connect to cmslab and hgcroc with PubKeyAuthentication.
#   - User has sudo-access on hgcroc (for compiling mylittledt if needed)
###################################################################################################

# __hgcroc_count_uio__ - determine number of uio in /sys/class/uio directory
#   internal function
#   count the number of files in the /sys/class/uio directory.
__hgcroc_count_uio__() {
  ssh cmslab 'ssh hgcroc "ls -1 /sys/class/uio | wc -l"'
}

# __hgcroc_open__ - initialize the connection with the hgc roc computer
#   If the number of files in the /sys/class/uio directory is >= 10,
#     then we assume the mylittledbt software is already compiled and installed
#     otherwise, go to the hgcroc-test-computer and compile it
#   We also mount the data directory back through our ssh tree,
#     so we can see the output data here. This mounting assumes specific (empty)
#     directories already exist here and on cmslab.
__hgcroc_open__() {
  if [[ $(__hgcroc_count_uio__) -lt 10 ]]; then
    # need to compile
    echo "Need to compile mylittledt (you will be prompted for your password)."
    if ! ssh cmslab -t -t 'ssh hgcroc -t -t compile-mylittledt || exit 1'; then
      echo "ERROR: Could not compile mylittledt!"
      return 1
    fi
  fi

#  # make sure directories we want to mount to exist (and are empty)
#  if ! ssh cmslab 'mkdir -p hgcroc/data_mount && [ ! -z "$(ls -A hgcroc/data_mount)" ] && echo "ERROR: cmslab data_mount non-empty!" && exit 1'; then
#    return 1
#  fi
#  mkdir -p $HOME/ldmx/hgcroc/data_mount && [ ! -z "$(ls -A $HOME/ldmx/hgcroc/data_mount)" ] && echo "ERROR: our data_mount non-empty!" && return 1

  # mounting
  if ! ssh cmslab 'sshfs hgcroc:hexactrl-sw/hexactrl-script/data hgcroc/data_mount || echo "ERROR: Could not mount cmslab to hgcroc!"'; then
    echo "Could not connect to cmslab!"
    return 1
  fi
  sshfs cmslab:hgcroc/data_mount $HOME/ldmx/hgcroc/data_mount || echo "ERROR: Could not mount us to cmslab!"
}

# __hgcroc_close__ - Undo mounting when closing connection
#   We disconnect ourselves from the sshfs file mounts,
#   so we can leave without error.
#   TODO: Attach this as a handle so that it can happen automagically.
__hgcroc_close__() {
  ssh cmslab 'fusermount -u hgcroc/data_mount'
  fusermount -u $HOME/ldmx/hgcroc/data_mount  
  return 0
}

# __hgcroc_launch__ - Launch the interactive tmux window
#
# Assumex hexactrl-sw and hexactrl-script
#   environments are loaded automatically
#   via the '.bashrc' on the HGCROC computer.
#
# TODO: Close TCP ports when closing servers so we can launch more than
#       once while the HGC ROC computer is on.
#
# tmux layout
# |===================|
# |         |         |
# |         | _server |
# |         |=========|
# | ssh     | -server |
# |         |=========|
# |         | -client |
# |===================|
__hgcroc_launch__() {
  tmux new -s hgcroc \
    ssh cmslab -t -t 'ssh hgcroc' ';' \
    split -h ssh cmslab 'ssh hgcroc open-py-zmq-server' ';' \
    split ssh cmslab 'ssh hgcroc open-zmq-server' ';' \
    split ssh cmslab 'ssh hgcroc open-zmq-client' ';'
  return $?
}

# __hgcroc_attach__ - Attach to the HGCROC computer without any frills
__hgcroc_attach__() {
  ssh -t -t cmslab "ssh hgcroc"
  return $?
}

# __hgcroc_help__ - Print help for this CLI
__hgcroc_help__() {
  cat <<\HELP
 USAGE:
  hgcorc <command>

 COMMANDS
  help    Print this help message and exit

  open    Initialize connection between HGC ROC test computer and us

  close   De-initialize connection
          good practice to make sure connections are cleaned up

  launch  Start tmux server with HGC ROC servers running and a terminal
          on the hgcroc machine running for you to have access

  attach  ssh directly to the HGCROC computer

  EXAMPLES
    hgcroc help
    hgcroc open
    hgcroc close
    hgcroc launch
    hgcroc attach
HELP
}

# hgcroc - CLI for connecting to hgcroc test computer
#
# Just parsing parameters here, nothing special.
hgcroc() {
  case "$1" in
    help)
      __hgcroc_help__
      return 0
      ;;
    open)
      __hgcroc_open__ ${@:2}
      return $?
      ;;
    close)
      __hgcroc_close__ ${@:2}
      return $?
      ;;
    launch)
      __hgcroc_launch__ ${@:2}
      return $?
      ;;
    attach)
      __hgcroc_attach__ ${@:2}
      return $?
      ;;
    *)
      echo "ERROR: Command '$1' not recognized."
      return 1
      ;;
  esac
}

# Tab completion for subcommands
complete -W "help open close launch attach" hgcroc
