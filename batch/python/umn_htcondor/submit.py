"""Specializations of the HTCondor Python API for use at UMN

Here we define some helpful funcitons you can run from within the python3 interpreter to submit and manage the jobs.
"""

import htcondor #HTCondor Python API
import classad  #HTCondor internal data structure
import getpass  #Gets current user name
import os # for path joining and directory listing
import shutil # for copying files
import sys # for exiting after check failure
from umn_htcondor import utility 

class JobInstructions(htcondor.Submit) :
    """Specialization of htcondor.Submit that has some helper functions for us."""

    def __init__(self,executable_path, output_dir, environment_script,
        input_arg_name = '', extra_config_args = '') :

        self.__full_out_dir_path = utility.full_dir(output_dir)

        if 'hdfs' not in self.__full_out_dir_path :
            print(f' WARN You are writing output files to a directory that is *not* in {utility.hdfs_dir()}.')

        self.__full_detail_dir_path = utility.full_dir(os.path.join(self.__full_out_dir_path, 'detail'))

        utility.check_exists(environment_script)

        super().__init__({
            'universe' : 'vanilla',
            # The +CondorGroup (I believe) is telling Condor to include this job submission
            #   under the accounting for the 'cmsfarm' group
            '+CondorGroup' : classad.quote('cmsfarm'),
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
            'nice_user' : True,
            # Now our job specific information
            #   'executable' is required by condor and that variable name cannot be changed
            #   the other variable names are ours and can be changed and used in the rest of this file
            'output_dir' : self.__full_out_dir_path,
            'env_script' : environment_script,
            'scratch_root' : f'/export/scratch/users/{getpass.getuser()}',
            # assume config script is in output directory
            'config_script' : '$(output_dir)/detail/config.py',
            'executable' : utility.full_file(executable_path),
            # This needs to match the correct order of the arguments in the run_fire.sh script
            #   The input file and any extra config arguments are optional and come after the
            #   three required arguments
            # We will be adding to this entry in the dictionary as we determine arguments to the config script
            'arguments' : f'$(scratch_root)/$(Cluster)-$(Process) $(env_script) $(config_script) $(output_dir) {extra_config_args} {input_arg_name}'
          })

        self['requirements'] = utility.dont_use_machine('caffeine')
        for m in ['zebra01','zebra02','zebra03','zebra04'] :
            self.ban_machine(m)            

        self.__items_to_loop_over = None

    def memory(self,max_mem_str) :
        """Set the max memory requested for these jobs"""

        self['request_memory'] = utility.convert_memory(max_mem_str)

    def nice(self,be_nice) :
        """Set the nice-ness of these jobs

        Parameters
        ----------
        be_nice : bool
            True if we should be nice
        """

        self['nice_user'] = bool(be_nice)

    def ban_machine(self,m) :
        """Don't allow the jobs to run on the input machine.

        We assume that there is already at least one
        requirement defined, so the first requirement
        will need to be defined in the constructor.
        """

        self['requirements'] = classad.ExprTree(self['requirements']).and_(utility.dont_use_machine(m))

    def sleep(self,time) :
        """Sleep for the input number of seconds between starting jobs.

        It is helpful to have some lag time so that transferring large files
        or reading from executable files can happen without overloading
        the filesystem.
        """
        self['next_job_start_delay'] = time

    def config(self,conf) :
        """Set the configuration script that these jobs should run.

        We make a copy of the config and put it in the output
        directory so that jobs can have a stable copy of it.
        """

        full_config_path = utility.full_file(conf)
        shutil.copy2(full_config_path, os.path.join(self.__full_detail_dir_path,'config.py'))

    def periodic_release(self) :
        """Tell this HTCondor to release all jobs that returned an exit code of 99 and were then held.

        The run_fire.sh script that runs the jobs returns a failure status of 99 when the worker node
        it is assigned to is not connected to hdfs and/or cvmfs (both of which are required for our jobs).
        This is helpful for trying to get jobs that failed this way back into the submission queue.
        
        If a machine is not reconnected to hdfs/cvmfs automatically, you may with to ban it.
        """

        self['periodic_release'] = '(HoldReasonSubCode == 99) && (HoldReasonCode == 3)'

    def save_output(self, out_dir) :
        """Tell HTCondor to save the terminal output of **all** jobs in this batch to files in the input directory."""
        terminal_output_file = os.path.join(full_dir(out_dir),'$(Cluster)-$(Process).out')
        self['output'] = terminal_output_file
        self['error' ] = terminal_output_file

    def run_over_input_dirs(self, input_dirs, num_files_per_job, input_arg_name) :
        """Have the config script run over num_files_per_job files taken from input_dirs, generating jobs
        until all of the files in input_dirs are included.

        Parameters
        ----------
        input_dirs : list of str
            List of input directories to run over
        num_files_per_job : int
            Number of files for each job to have (maximum, could be less)
        input_arg_name : str
            Name of argument to give to python configuration before the list of files
        """

        if self.__items_to_loop_over is not None :
            raise Exception('Already defined how these jobs should run.')
    
        input_file_list = []
        for input_dir in arg.input_dir :
            # submitting the whole directory
            full_input_dir = utility.full_dir(input_dir,False)
            if 'hdfs' not in full_input_dir :
                print(' WARN You are running jobs over files in a directory *not* in %s.'%hdfs_dir())
    
            input_file_list.extend(
                [os.path.join(full_input_dir,f) for f in os.listdir(full_input_dir) if f.endswith('.root')]
                )
        #end loop over input directories
    
        # we need to define a list of dictionaries that htcondor submission will loop over
        #   we partition the list of input files into space separate lists of maximum length arg.files_per_job
        def partition(l, n) :
            chunks = []
            for i in range(0,len(l),n):
                space_sep = ''
                for p in l[i:i+n] :
                    space_sep += f'{p} '
                #loop over sub list
                chunks.append(space_sep) 
            #loop over full list
            return chunks
        #end def of partition

        self['arguments'] += ' $(input_files)'
        self.__items_to_loop_over = [{'input_files' : i} for i in partition(input_file_list, num_files_per_job)]

    def run_refill(self) :
        """Get missing run numbers from output directory and submit those."""

        if self.__items_to_loop_over is not None :
            raise Exception('Already defined how these jobs should run.')

        runs = []
        for f in os.listdir(self.__full_out_dir_path) :
            parameters = f[:-5].split('_')
            if 'run' in parameters :
                runs.append(int(parameters[parameters.index('run')+1]))
            #end if run is in parameter list
        #end loop over directory

        if len(runs) == 0 :
            raise Exception('No run numbers listed in output directory. Cant refill!')

        runs.sort()

        self['arguments'] += ' $(run_number)'
        self.__items_to_loop_over = [{'run_number' : str(r)} for r in range(runs[0],runs[-1]+1) if r not in runs]

    def run_numbers(self, start, number):
        """Run over iterated run numbers"""

        if self.__items_to_loop_over is not None :
            raise Exception('Already defined how these jobs should run.')

        self['arguments'] += ' $(run_number)'
        self.__items_to_loop_over = [{'run_number' : str(r)} for r in range(start, start+number)]

    def _pause_before(next_thing) :
        answer = input('[Q/q+Enter] to quit or [Enter] to '+next_thing+'... ')
        if answer.capitalize().startswith('Q') :
            sys.exit()

    def __str__(self) :
        """Return a printed version of this object."""
        return super().__str__()

    def _check(self) :
        """Print configuration to screen and pause for confirmation."""

        print(self)
        JobInstructions._pause_before('see Queue-ing list')
        print(self.__items_to_loop_over)
        JobInstructions._pause_before('submit')

    def _log_submission(self, f) :
        """Log the job configurations to the input file (assumed open)"""
        print(self, file=f)
        f.write("\nFull List of Jobs:\n")
        for j in self.jobs(itemdata=iter(self.__items_to_loop_over)) :
            f.write(j.printJson())
            f.write('\n')
    
    def submit(self, check = True) :
        """Actually submit the job instructions to the batch system."""

        if check :
            self._check()

        schedd = htcondor.Schedd()
        with schedd.transaction() as txn :
          submit_result = self.queue_with_itemdata(txn, itemdata=iter(self.__items_to_loop_over))
          print(f'Submitted to Cluster {submit_result.cluster()}')
          with open(f'{self.__full_detail_dir_path}/submit.{submit_result.cluster()}.log','w') as log :
              self._log_submission(log)

    
