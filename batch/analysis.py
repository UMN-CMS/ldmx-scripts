
import argparse
parser = argparse.ArgumentParser(description='')

parser.add_argument('input_files',type=str,nargs='+',help='List of input files for this run to analyze.')

args = parser.parse_args() 

from LDMX.Framework import ldmxcfg

p=ldmxcfg.Process("ana")

p.inputFiles = arg.input_files

p.histogramFile = 'hist_%s'%(os.path.basename(p.inputFiles[0]))

from LDMX.DQM import dqm
p.sequence = [ dqm.TrigScintSimDQM() ]

