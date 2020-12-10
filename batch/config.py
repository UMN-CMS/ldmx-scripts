
import argparse
parser = argparse.ArgumentParser(description='')

parser.add_argument('--run_number',type=int,help='ID number for this run.')
parser.add_argument('--input_file',type=str,help='Input file to process.')

args = parser.parse_args() 

from LDMX.Framework import ldmxcfg

p=ldmxcfg.Process("sim")
p.run = args.run_number
p.maxEvents = 10

from LDMX.SimCore import examples
p.sequence = [ examples.inclusive_single_e() ]

p.outputFiles = [ 'inclusive_single_e_output_10_events_r%04d.root'%(p.run) ]
