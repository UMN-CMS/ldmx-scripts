"""Submitting jobs for ldmx to Condor batch submission

This python script is intended to be used with the running script 'run_fire.sh' in this current directory.
"""

import os
import argparse
from umn_htcondor.utility import local_dir, hdfs_dir
from umn_htcondor.submit import JobInstructions

parser = argparse.ArgumentParser('ldmx-submit-jobs',
    description="Submit batches of jobs running the ldmx-sw application.",
    formatter_class=argparse.RawDescriptionHelpFormatter)

# required args
parser.add_argument("-c",metavar='CONFIG',dest='config',required=True,type=str,help="CONFIG is python configuration script to run.")
parser.add_argument("-o",metavar='OUT_DIR',dest='out_dir',required=True,type=str,help="OUT_DIR is directory to copy output to. If the path given is relative (i.e. does not begin with '/'), then we assume it is relative to your hdfs directory: %s"%hdfs_dir())

environment = parser.add_mutually_exclusive_group(required=True)
environment.add_argument('-s',metavar='SING_IMG',dest='singularity_img',type=str,help="Image to run inside of.")
environment.add_argument('-d',metavar='DOCKER_TAG',dest='docker_tag',type=str,help="Full docker tag of image to run inside of. Will download if doesn't already exist.")

how_many_jobs = parser.add_mutually_exclusive_group(required=True)
how_many_jobs.add_argument('-i',metavar='INPUT_DIR',dest='input_dir',type=str,nargs='+',help="Directory containing input files to run over. If the path given is relative (i.e. does not begin with '/'), then we assume it is relative to your hdfs directory: %s"%hdfs_dir())
how_many_jobs.add_argument('-n',metavar='NUM_JOBS',dest='num_jobs',type=int,help="Number of jobs to run (if not input directory given).")
how_many_jobs.add_argument('-r','--refill',dest='refill',action='store_true',help="Look through the output directory and re-run any run numbers that are missing.")

# optional args for configuring how the job runs
parser.add_argument("--input_arg_name",type=str,default='',help='Name of argument that should go before the input file or run number when passing it to the config script.')
parser.add_argument("--start_job",type=int,default=0,help="Starting number to use when run numbers. Only used if NOT running over items in a directory.")
parser.add_argument("--files_per_job",type=int,default=10,help="If running over an input directory, this argument defines how many files to group together per job.")

# rarely-used optional args
full_path_to_dir_we_are_in=os.path.dirname(os.path.realpath(__file__))
parser.add_argument("--run_script",type=str,help="Script to run jobs on worker nodes with.",default='%s/run_ldmx.sh'%full_path_to_dir_we_are_in)
parser.add_argument("--program",type=str,help="Program to run inside the container.",default="fire")
parser.add_argument("--config_args",type=str,default='',help="Extra arguments to be passed to the configuration script. Passed after the run_number or input_file.")
parser.add_argument("--nocheck",action='store_true',help="Don't pause to look at job details before submitting.")
parser.add_argument("--nonice",action='store_true',dest="nonice",help="Do not run this at nice priority.")
parser.add_argument("--sleep",type=int,help="Time in seconds to sleep before starting the next job.",default=5)
parser.add_argument("--max_memory",type=str,default='4G',help='Maximum amount of memory to give jobs. Can use \'K\', \'M\', \'G\' as suffix specifiers.')
parser.add_argument("--max_disk",type=str,default='1G',help='Maximum amount of disk space to give jobs. Can use \'K\', \'M\', \'G\' as suffix specifiers.')
parser.add_argument("--periodic_release",action='store_true',help="Periodically release any jobs that exited because the worker node was not connected to cvmfs or hdfs.")
parser.add_argument("--priority",type=int,help='Define this job as higher priority than the default of zero. Provide an integer to rank relative to other jobs. (Higher == More Urgent)')
parser.add_argument("--broken_machines",type=str,nargs='+',help="Extra list of machines that should be avoided, usually because they are not running your jobs for whatever reason. For example: --broken_machines scorpion34 scorpion17")

machine_choice = parser.add_mutually_exclusive_group()
machine_choice.add_argument("--useable_machines",type=str,nargs='+',help="List of machines that should be used, no other machines are allowed. For example: --useable_machines scorpion{1..9}")
machine_choice.add_argument("--production",action='store_true',help='Use the scorpions with the higher scratch space available.')
machine_choice.add_argument("--analysis",action='store_true',help='Use the scorpions with the lower scratch space available.')

arg = parser.parse_args()

if arg.singularity_img is not None :
    singularity_img = os.path.realpath(arg.singularity_img)
else :
    img_name = arg.docker_tag.replace(':','_').replace('/','_')
    singularity_img = f'{local_dir()}/{img_name}.sif'
    # singularity will prompt user if image already exists
    os.system(f'singularity build {singularity_img} docker://{arg.docker_tag}')

job_instructions = JobInstructions(arg.run_script, arg.out_dir, singularity_img, arg.config, 
    input_arg_name = arg.input_arg_name, extra_config_args = arg.config_args, program = arg.program)

job_instructions.memory(arg.max_memory)
job_instructions.disk(arg.max_disk)
job_instructions.nice(not arg.nonice)
job_instructions.sleep(arg.sleep)

if arg.priority is not None :
    job_instructions.priority(arg.priority)

scorpions_with_small_scratch = [1,3,5,6,9,10,11,12,14,16,17,18,20,21,22,23,24]

# update list of requirements for our machine choice
if arg.useable_machines is not None :
    # Reset requirements
    job_instructions['requirements'] = 'False'
    for m in arg.useable_machines :
        job_instructions.use_machine(m)
elif arg.production :
    for s in scorpions_with_small_scratch :
        job_instructions.ban_machine(f'scorpion{s}')
elif arg.analysis :
    job_instructions['requirements'] = 'False'
    for s in scorpions_with_small_scratch :
        job_instructions.use_machine(f'scorpion{s}')

# include any 'broken' machines as banned machines
if arg.broken_machines is not None :
    # Add additional machines to avoid using
    for m in arg.broken_machines :
        job_instructions.ban_machine(m)

# run_fire.sh exits with code 99 if the worker is not connected to cvmfs or hdfs
#   in this case, we want to retry and hopefully find a worker that is correctly connected
#
# The period of this release depends on our specific configuration of HTCondor.
#   The default is 60s, but our configuration may be different (and I can't figure it out).
if arg.periodic_release :
    job_instructions.periodic_release()

if arg.input_dir is not None :
    job_instructions.run_over_input_dirs(arg.input_dir, arg.files_per_job)
elif arg.refill :
    job_instructions.run_refill()
else :
    job_instructions.run_numbers(arg.start_job, arg.num_jobs)
#input directory or not

if arg.nocheck :
    job_instructions.submit()
else :
    job_instructions.submit_interactive()
