"""Submitting jobs for ldmx to Condor batch submission

This python script is intended to be used with the running script 'run_fire.sh' in this current directory.
"""

import os,sys, stat
import argparse
import htcondor
import classad
from subprocess import Popen

def hdfs_dir() :
    return '/hdfs/cms/user/%s/ldmx'%os.environ['USER']

def local_dir() :
    return '/local/cms/user/%s/ldmx'%os.environ['USER']

parser = argparse.ArgumentParser('ldmx-submit-jobs',
    description="Submit batches of jobs running the ldmx-sw application.",
    formatter_class=argparse.RawDescriptionHelpFormatter)

# required args
parser.add_argument("-c",metavar='CONFIG',dest='config',required=True,type=str,help="CONFIG is python configuration script to run.")
parser.add_argument("-o",metavar='OUT_DIR',dest='out_dir',required=True,type=str,help="OUT_DIR is directory to copy output to. If the path given is relative (i.e. does not begin with '/'), then we assume it is relative to your hdfs directory: %s"%hdfs_dir())

environment = parser.add_mutually_exclusive_group(required=True)
environment.add_argument('-e',metavar='ENV_SCRIPT',dest='env_script',type=str,help="Environment script to run before running fire.")
environment.add_argument('-l',metavar='LDMX_VERSION',dest='ldmx_version',type=str,help="LDMX Version to pick a pre-made environment script.")

how_many_jobs = parser.add_mutually_exclusive_group(required=True)
how_many_jobs.add_argument('-i',metavar='INPUT_DIR',dest='input_dir',type=str,help="Directory containing input files to run over. If the path given is relative (i.e. does not begin with '/'), then we assume it is relative to your hdfs directory: %s"%hdfs_dir())
how_many_jobs.add_argument('-n',metavar='NUM_JOBS',dest='num_jobs',type=int,help="Number of jobs to run (if not input directory given).")
how_many_jobs.add_argument('-r','--refill',dest='refill',action='store_true',help="Look through the output directory and re-run any run numbers that are missing.")

# optional args for configuring how the job runs
parser.add_argument("--run_arg_name",type=str,default='',help='Name of argument that should go before the run number when passing it to the config script. Only used if NOT running over items in a directory.')
parser.add_argument("--start_job",type=int,default=0,help="Starting number to use when run numbers. Only used if NOT running over items in a directory.")

parser.add_argument("--input_arg_name",type=str,default='',help='Name of argument that should go before the input file when passing it to the config script. Only used if running over the items in a directory.')
parser.add_argument("--files_per_job",type=int,default=10,help="If running over an input directory, this argument defines how many files to group together per job.")
parser.add_argument("--max_num_jobs",type=int,default=1000,help="If running over an input directory, this argument defines the maximum number of jobs to submit at once.")

# rarely-used optional args
full_path_to_dir_we_are_in=os.path.dirname(os.path.realpath(__file__))
parser.add_argument("--run_script",type=str,help="Script to run jobs on worker nodes with.",default='%s/run_fire.sh'%full_path_to_dir_we_are_in)
parser.add_argument("--config_args",type=str,default='',help="Extra arguments to be passed to the configuration script. Passed after the run_number or input_file.")
parser.add_argument("--nocheck",action='store_true',help="Don't pause to look at job details before submitting.")
parser.add_argument("--test",action='store_true',help="Just print Job details to terminal, don't actually submit.")
parser.add_argument("--save_output",type=str,help="Save terminal output to the input directory. Only use for debugging purposes. This can over-burden the filesystem is used with too many (>10) jobs.")
parser.add_argument("--nonice",action='store_true',dest="nonice",help="Do not run this at nice priority.")
parser.add_argument("--sleep",type=int,help="Time in seconds to sleep before starting the next job.",default=2)
parser.add_argument("--max_memory",type=str,default='4G',help='Maximum amount of memory to give jobs. If \'G\' is the last character, assume GB, othersie assume MB and convert to integer.')
parser.add_argument("--periodic_release",action='store_true',help="Periodically release any jobs that exited because the worker node was not connected to cvmfs or hdfs.")
parser.add_argument("--broken_machines",type=str,nargs='+',default=[],help="Extra list of machines that should be avoided, usually because they are not running your jobs for whatever reason. For example: --broken_machines scorpion34 scorpion17")

arg = parser.parse_args()

def check_exists(path) :
    if not os.path.exists(path) :
        raise Exception("'%s' does not exist."%path)

def full_dir(path, make=True) :
    if not path.startswith('/') :
        path = hdfs_dir()+'/'+path
    full_path = os.path.realpath(path)
    if make :
        os.makedirs(full_path, exist_ok=True)
    check_exists(full_path)
    return full_path

def full_file(path) :
    full_path = os.path.realpath(path)
    check_exists(full_path)
    return full_path

def copy(source,dest) :
    p = Popen(['cp','-p',source,dest])
    p.wait()

# make the output directory
full_out_dir_path = full_dir(arg.out_dir)

if 'hdfs' not in full_out_dir_path :
    print(' WARN You are writing output files to a directory that is *not* in %s.'%hdfs_dir())

full_config_path = full_file(arg.config)
full_run_path = full_file(arg.run_script)

full_detail_dir_path = full_dir(os.path.join(full_out_dir_path,'detail'))
copy(full_config_path,'%s/config.py'%full_detail_dir_path)

if arg.env_script is not None :
    env_script = os.path.realpath(arg.env_script)
else :
    env_script = '%s/stable-installs/%s/setup.sh'%(local_dir(),arg.ldmx_version)

check_exists(env_script)

def convert_memory(mem_str) :
    if mem_str.endswith('G') :
        mem_str = mem_str[:-1]
        return 1024*int(mem_str)
    else :
        return int(mem_str)

# HTCondor submit object takes a dictionary of parameters as an input
#   And further modifications can be made to the parameters as if it was a dictionary
job_instructions = htcondor.Submit({
  'universe' : 'vanilla',
# The +CondorGroup (I believe) is telling Condor to include this job submission
#   under the accounting for the 'cmsfarm' group
  '+CondorGroup' : classad.quote('cmsfarm'),
# How much memory does this job require?
#   This is somewhat hard to determine since one does not normally track memory usage of one's programs.
#   4 Gb of RAM is a high upper limit, so this probably mean that less jobs will run in parallel, BUT
#   it helps make sure no jobs slow down due to low amount of available memory.
  'request_memory' : convert_memory(arg.max_memory),
# This line keeps any jobs in a 'hold' state return a failure exit status
#   If you are developing a new executable (run script), this might need to be removed
#   until you get your exit statuses defined properly
  'on_exit_hold' : classad.Attribute('ExitCode') != 0,
# This line passes the ExitCode from the application as the hold subcode
  'on_exit_hold_subcode' : classad.Attribute('ExitCode'),
# And we explain that the hold was because run_fire failed
  'on_exit_hold_reason' : classad.quote('run_fire.sh returned non-zero exit code (stored in HoldReasonSubCode)'),
# This line tells condor whether we should be 'nice' or not.
#   Niceness is a way for condor to help determine how 'urgent' this job is
#   Please default to alwasy being nice
  'nice_user' : not arg.nonice,
# Now our job specific information
#   'executable' is required by condor and that variable name cannot be changed
#   the other variable names are ours and can be changed and used in the rest of this file
  'output_dir' : full_out_dir_path,
  'env_script' : env_script,
  'scratch_root' : '/export/scratch/users/%s'%os.environ['USER'],
  'config_script' : '$(output_dir)/detail/config.py',
  'executable' : full_run_path,
# This is the number of seconds to pause between starting jobs
#   It is helpful to have some lag time so that transferring large files can happen
#   without overloading the file system
  'next_job_start_delay' : arg.sleep,
# This needs to match the correct order of the arguments in the run_fire.sh script
#   The input file and any extra config arguments are optional and come after the
#   three required arguments
# We will be adding to this entry in the dictionary as we determine arguments to the config script
  'arguments' : '$(scratch_root)/$(Cluster)-$(Process) $(env_script) $(config_script) $(output_dir)'
})

def dont_use(machine) :
    return '(Machine != "%s.spa.umn.edu")'%machine

# Add additional machines to avoid using
job_instructions['requirements'] = dont_use('caffeine')
for m in ['zebra01','zebra02','zebra03','zebra04']+arg.broken_machines :
    job_instructions['requirements'] += ' && ' + dont_use(m)

# run_fire.sh exits with code 99 if the worker is not connected to cvmfs or hdfs
#   in this case, we want to retry and hopefully find a worker that is correctly connected
#
# The period of this release depends on our specific configuration of HTCondor.
#   The default is 60s, but our configuration may be different (and I can't figure it out).
if arg.periodic_release :
  job_instructions['periodic_release'] = '(HoldReasonSubCode == 99) && (HoldReasonCode == 3)'

# If 'save_output' is defined on the command line
#   use the passed string as the directory to dump terminal output files
# ONLY GOOD FOR DEBUGGING
#   This *will* overload the file system if you run a full scale number of jobs
#   will trying to save all the terminal output to one directory.
if arg.save_output is not None :
    job_instructions['output'] = os.path.join(full_dir(arg.save_output),'$(Cluster)-$(Process).out')
    job_instructions['error' ] = os.path.join(full_dir(arg.save_output),'$(Cluster)-$(Process).out')

if arg.input_dir is not None :
    # submitting the whole directory
    full_input_dir = full_dir(arg.input_dir,False)
    if 'hdfs' not in full_input_dir :
        print(' WARN You are running jobs over files in a directory *not* in %s.'%hdfs_dir())

    # we need to define a list of dictionaries that htcondor submission will loop over
    #   we partition the list of input files into space separate lists of maximum length arg.files_per_job
    input_file_list = os.listdir(full_input_dir)
    def partition(l, n) :
        chunks = []
        for i in range(0,len(l),n):
            space_sep = ''
            for p in l[i:i+n] :
                space_sep += '%s/%s '%(full_input_dir,p)
            #loop over sub list
            chunks.append(space_sep) 
        #loop over full list
        return chunks
    #end def of partition

    inputs = partition(input_file_list, arg.files_per_job)

    # attach input argument to config args
    job_instructions['arguments'] += ' ' + arg.input_arg_name + ' $(input_files)'
    items_to_loop_over = [{'input_files' : i} for i in inputs]

else :
    if arg.refill :
        def list_missing_runs(file_listing) :
            """List the run numbers of the input file list."""
        
            runs = []
            for f in file_listing :
                parameters = f[:-5].split('_') #remove '.root' and split by underscore
                if 'run' in parameters :
                    #run number is parameter after name 'run'
                    runs.append(int(parameters[parameters.index('run')+1]))
                #end if run is in parameter list
            #end loop over files

            if len(runs) == 0 :
                return None

            runs.sort()
        
            return [m for m in range(runs[0],runs[-1]+1) if m not in sorted_number_list]
    
        run_numbers = list_missing_runs(os.listdir(full_output_dir))
    
        if run_numbers is None :
            raise Exception('Output directory has no files with "<stuff>_run_<run_number>_<stuff>" in it.')
    else :
        run_numbers = range(arg.start_job,arg.start_job+arg.num_jobs)
    #refill or not

    # attach the run number to the list of arguments
    job_instructions['arguments'] += ' ' + arg.run_arg_name + ' $(run_number)'
    items_to_loop_over = [{'run_number' : str(r)} for r in run_numbers]
#input directory or not

job_instructions['arguments'] += ' ' + arg.config_args

# Now the instructions have been written,
#   we can either printout the jobs that would have been submitted
#   or actually submit them
def log_submission(f) :
    print(job_instructions, file=f)
    f.write("\nFull List of Jobs:\n")
    for j in job_instructions.jobs(itemdata=iter(items_to_loop_over)) :
        f.write(j.printJson())
        f.write('\n')

def pause_before(next_thing) :
    answer = input('[Q/q] to quit or anything else to '+next_thing+'... ')
    if answer.capitalize().startswith('Q') :
        sys.exit()

if arg.test :
    log_submission(sys.stdout)
else :
    if not arg.nocheck :
        print('Job File:')
        print(job_instructions)
        pause_before('see Queue-ing list')
        print(items_to_loop_over)
        pause_before('submit')

    schedd = htcondor.Schedd()
    with schedd.transaction() as txn :
        submit_result = job_instructions.queue_with_itemdata(txn, itemdata=iter(items_to_loop_over))
        print("Submitted to Cluster %d"%submit_result.cluster())
        with open('%s/submit.%d.log'%(full_detail_dir_path,submit_result.cluster()),'w') as log :
            log_submission(log)
