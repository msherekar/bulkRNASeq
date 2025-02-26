#!/usr/bin/env python3

import os
import logging
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Import local modules
try:
    from .workflow import run_preprocessing_workflow
    from .qc import run_fastqc, setup_logger
    from .alignment import align_reads, generate_counts
except ImportError:
    # Fallback imports for direct module execution
    from bulkRNASeq.preprocessing.workflow import run_preprocessing_workflow
    from bulkRNASeq.preprocessing.qc import run_fastqc, setup_logger
    from bulkRNASeq.preprocessing.alignment import align_reads, generate_counts

logger = logging.getLogger(__name__)

def run_preprocessing_pipeline(config, checkpoint_mgr=None):
    """
    Main function to run the RNA-seq preprocessing pipeline.
    
    Args:
        config (dict): Configuration dictionary containing:
            - input: Dictionary with input file paths
            - output: Dictionary with output directory paths
            - parameters: Dictionary with processing parameters
            - qc: Dictionary with quality control parameters
    """
    try:
        # Get configuration parameters
        fastq_dir = config['input']['fastq_dir']
        fastq_pattern = config['input'].get('fastq_pattern', '*.fq.gz')
        output_dir = config['output'].get('results_dir', 'results/preprocessing')
        params = config.get('parameters', {})
        qc_params = config.get('qc', {})
        
        # Get list of FASTQ files
        fastq_path = Path(fastq_dir)
        logger.info(f"Looking for FASTQ files in {fastq_dir} with pattern {fastq_pattern}")
        input_fastq_files = list(fastq_path.glob(fastq_pattern))
        
        if not input_fastq_files:
            # Try both common patterns
            input_fastq_files = list(fastq_path.glob('*.fq.gz')) + list(fastq_path.glob('*.fastq.gz'))
            if not input_fastq_files:
                raise FileNotFoundError(f"No FASTQ files found in {fastq_dir} with pattern {fastq_pattern}")
            
        logger.info(f"Found FASTQ files: {[f.name for f in input_fastq_files]}")

        
        # Convert paths to strings
        input_fastq_files = [str(f) for f in input_fastq_files]
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Run initial quality control
        logger.info("Running initial FastQ quality control")
        qc_output_dir = os.path.join(output_dir, 'fastqc_results')
        Path(qc_output_dir).mkdir(parents=True, exist_ok=True)
        
        # Run FastQC on input file
        input_file = input_fastq_files[0]  # Just use the first file for now
        logger.info(f"Running FastQC on {input_file}")
        run_fastqc(input_file, qc_output_dir)
        
        # Setup logging for QC steps
        qc_logger = setup_logger('qc', qc_output_dir)
        
        # Run alignment
        logger.info("Aligning reads to reference genome")
        alignment_dir = os.path.join(output_dir, 'aligned_reads')
        Path(alignment_dir).mkdir(parents=True, exist_ok=True)
        
        # Get HISAT2 index path
        hisat2_index = config['aligners']['hisat2']['index_prefix']
        logger.info(f"Using HISAT2 index: {hisat2_index}")
        
        # Align the raw FASTQ file (no trimming)
        bam_file = align_reads(
            input_file,
            reference_genome=hisat2_index,
            output_dir=alignment_dir,
            threads=params.get('threads', 4)
        )
        
        # Generate counts
        counts_dir = os.path.join(output_dir, 'counts')
        Path(counts_dir).mkdir(parents=True, exist_ok=True)
        
        # Get base name from original FASTQ for consistent naming
        base_name = os.path.basename(input_file).replace('.fq.gz', '').replace('.fastq.gz', '')
        counts_file = generate_counts(
            bam_file,
            gtf_file=config['genome']['gtf_file'],
            output_dir=counts_dir,
            base_name=base_name
        )
        
        # Save pipeline run statistics
        stats = {
            'fastqc_dir': qc_output_dir,
            'bam_file': bam_file,
            'counts_file': counts_file,
            'processed_files': [input_file]
        }
        
        with open(os.path.join(output_dir, 'pipeline_stats.json'), 'w') as f:
            json.dump(stats, f, indent=4)
        
        logger.info("Preprocessing pipeline completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in preprocessing pipeline: {str(e)}")
        return False

