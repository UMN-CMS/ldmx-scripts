"""Utility functions for use within the HTCondor UMN specialization"""

import htcondor #HTCondor Python API
import classad #HTCondor internal data structure
import os #full paths and directory making
import getpass #user name

def hdfs_dir() :
    """Get the current users ldmx directory in hdfs"""
    return f'/hdfs/cms/user/{getpass.getuser()}/ldmx'

def local_dir() :
    """Get the current users ldmx directory in local"""
    return f'/local/cms/user/{getpass.getuser()}/ldmx'

def convert_memory(mem_str) :
    """Convert <mem>G or <mem> to mega-bytes integer."""

    if mem_str.endswith('G') :
        mem_str = mem_str[:-1]
        return 1024*int(mem_str)
    else :
        return int(mem_str)

def check_exists(path) :
    """Check that the input path exists on the file system.

    Does not check if the path is a file or directory.
    """

    if not os.path.exists(path) :
        raise Exception("'%s' does not exist."%path)

def full_dir(path, make=True) :
    """Get the full path to the input directory
    and (maybe) create it if it doesn't exist.

    Make sure that it exists and if not,
    completely exit the script.
    """

    if not path.startswith('/') :
        path = hdfs_dir()+'/'+path
    full_path = os.path.realpath(path)
    if make :
        os.makedirs(full_path, exist_ok=True)
    check_exists(full_path)
    return full_path

def full_file(path) :
    """Get the full path to the input file.

    Make sure that it exists and throw and Exception if not.
    """

    full_path = os.path.realpath(path)
    check_exists(full_path)
    return full_path

def get_umn_host_name(full_machine_name) :
    """Get the UMN Host name from the full computer name

    Removes the slot number and the URL '.spa.umn.edu'
    """
    return full_machine_name.split('@')[1][:-12]

def dont_use_machine(m) :
    """Don't use the input SPA machine for jobs."""
    return classad.Attribute('Machine') != classad.quote(f'{m}.spa.umn.edu')

def job_is_mine() :
    """Expression that is true when current user owns the job."""
    return classad.Attribute('Owner') == getpass.getuser()

def job_status_is_held() :
    """Returns an expression that is true when the Job is in the HELD state.""" 
    return classad.Attribute('JobStatus') == htcondor.JobStatus.HELD

def job_status_is_running() :
    """Returns an expression that is true when the Job is in the RUNNING state."""
    return classad.Attribute('JobStatus') == htcondor.JobStatus.RUNNING
    
