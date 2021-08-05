# hgcroc
Helper environment script for running our test HGC ROC setup.

## Usage
This helper script is designed to be run in three steps.

1. Open the connection `hgcroc open`
   - Here we check that mylittledt is compiled and we chain a series of `sshfs` connections back to your computer so you can look at the data locally without having to copy across the connection.
2. Launch the servers and interactive terminal `hgcroc launch`
   - Start a `tmux` session with the three servers launched on one side and an interactive terminal started for running tests.
3. Close the connection `hgcroc close`
   - Dismount the `sshfs` connections

## First-Use Documentation
The start-up is very delicate. I assume that you have the following requirements.

1. Have ssh access to the computer connected to the HGC ROC from a computer on the lab intranet
2. Have Public-Key authentication set-up from the lab computer to the HGC ROC computer
3. Have ssh access to a interactive computer to the computer on the lab intranet
4. Have public-key authentication set-up between these two computers as well
5. Have sudo-access on the HGC ROC computer for compiling some of the code (`mylittledt`)
6. `tmux` is installed on your interactive computer

### ssh config
It is helpful to define some "aliases" within ssh. 
For our purposes, we have to modify the ssh configuration of the interactive computer and the lab computer.

```
# e.g. on my personal laptop
Host cmslab
    HostName cmslab1.spa.umn.edu
    User eichl008


# and on the lab computer

#hexa-board testing computer
Host hgcroc
    HostName 192.168.23.12
```

This allows us to use the names `cmslab` and `hgcroc` in the bash functions rather than typing out the whole name everytime.

### Environment Set-Up
The computer connected to the HGC ROC needs to have certain environment setup done automatically whenever we are connecting to it.
We do this by inserting some code into the `~/.bashrc` of the HGC ROC computer.

```bash
# Manual Copy of hexactrl-sw and hexactrl-script env.sh
#    Translating paths to full paths
export PATH=$HOME/hexactrl-sw/bin:/opt/cactus/bin:$PATH
export LD_LIBRARY_PATH=$HOME/hexactrl-sw/lib:/opt/cactus/lib:$LD_LIBRARY_PATH
export UHAL_ENABLE_IPBUS_MMAP=1

waiting() {
  while true; do sleep 1; done
}

# Helper function for server that needs to be in a specific directory
open-py-zmq-server() {
  echo "py-zmq-server"
  cd $HOME/hexactrl-sw/zmq_i2c
  python3 -u zmq_server.py
  waiting
  exit
}

# Helper function for server in specific directory
open-zmq-server() {
  echo "zmq-server"
  cd $HOME/hexactrl-sw
  zmq-server
  waiting
  exit
}

# Helper function for last server
open-zmq-client() {
  echo "zmq-client"
  cd $HOME/hexactrl-sw
  zmq-client
  waiting
  exit
}

# Helper to compile mylittledt remotely if needed
compile-mylittledt() {
  cd /home/lpgbt/mylittledt
  sudo make te0803
}
```

Additionally, for some reason I don't understand, the TCP ports do not get closed when exiting the `tmux` session holding the various servers.
We can crudely get around this issue by closing them manually in `~/.bash_logout`.

```bash
# fancy schmancy command to kill servers listening to ports if they are up
#  pipe-by-pipe explanation:
#    netstat - get list of TCP ports listening
#    awk     - print the column of processes attached to these ports
#    grep    - filter out rows that actually have process numbers
#    sed     - get the process id number
#    xargs   - kill those processes
netstat -tlnp 2> /dev/null | awk '{print $7}' | grep "[0-9]*/.*" | sed 's:/.*::' | xargs -r kill
```
