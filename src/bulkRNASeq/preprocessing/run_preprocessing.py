# This code will respond to the preprocessing.run_preprocessing(args.config) call from the main.py file
# It will run the preprocessing pipeline step by step 
# (qc->trimming->qc->allignment->qc of kallisto alignment->kallisto quantification->qc of kallisto quantification)

# It will also save the results in the results/preprocessing directory
# It will also save the logs in the logs/preprocessing directory
# It will also save the reports in the reports/preprocessing directory

import argparse, logging, os, sys, time, yaml, subprocess, pathlib
from bulkRNASeq.utils.check import check_config, check_preprocessing_directories
from bulkRNASeq.preprocessing.qc import run_fastqc
from bulkRNASeq.preprocessing.trim import run_trim_pipeline
from bulkRNASeq.preprocessing.kallisto import run_kallisto_quant
from bulkRNASeq.preprocessing.hisat2 import traverse_and_align
from bulkRNASeq.preprocessing.featurecounts import run_featurecounts
# import create directories
# import qc

def run_preprocessing(config):
    """
    Run the preprocessing pipeline step by step
    Args:
        config: Path to the config file
    Returns:
            Preprocessing pipeline results in the results/preprocessing directory
            Preprocessing pipeline logs in the logs/preprocessing directory
            Preprocessing pipeline reports in the reports/preprocessing directory
    """
    # Load the config file
    with open(config, 'r') as f:
        config = yaml.safe_load(f)

    # Do the basic checks on config file
    check_config(config)

    # Create the directories if they don't exist
    check_preprocessing_directories(config)

    # if config file passes all the checks and directories exist
    # Run qc on the fastq files
    run_fastqc(config['input']['fastq_dir'], config['output']['qc_dir'])
    
    # if given fasttq files pass qc, then trim successfull fastq files
    run_trim_pipeline(config['input']['fastq_dir'], config['output']['qc_trimmed_dir'], "trimmomatic")

    # Run qc on the trimmed fastq files
    run_fastqc(config['output']['qc_trimmed_dir'], config['output']['trimmed_fastq_dir']) # double check if this is correct

    # Run kalliston allignment on the trimmed fastq files
    #run_kallisto_quant(config['output']['trimmed_fastq_dir'], config['output']['aligned_dir'], config['input']['kallisto_index'])

    # Run hisat2 allignment on the trimmed fastq files
    traverse_and_align(config['output']['trimmed_fastq_dir'], config['output']['aligned_dir'], config['input']['hisat2_index'])

    # Run featurecounts on the aligned files
    run_featurecounts(config['output']['aligned_dir'], config['output']['counts_dir'], config['input']['annotation_file'])

    # TODO: QC on kallisto allignment, check if feaa=ture counts is necessary, what is output of kallisto and is this it for kallisto allignment.
    # TODO: how to incorporate other allligners here.
    # Basically, output file of one be the input for the next.


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the preprocessing pipeline")
    parser.add_argument("--config", type=str, required=True, help="Path to the config file")
    args = parser.parse_args()
    run_preprocessing(args.config)

