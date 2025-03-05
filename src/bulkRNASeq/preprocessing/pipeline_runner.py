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
    from .kallisto import run_kallisto_quant
    from .histat2 import run_hisat2_alignment
    from .salmon import run_salmon_quant
except ImportError:
    # Fallback imports for direct module execution
    from bulkRNASeq.preprocessing.workflow import run_preprocessing_workflow
    from bulkRNASeq.preprocessing.qc import run_fastqc, setup_logger
    from bulkRNASeq.preprocessing.alignment import align_reads, generate_counts
    from bulkRNASeq.preprocessing.kallisto import run_kallisto_quant
    from bulkRNASeq.preprocessing.histat2 import run_hisat2_alignment
    from bulkRNASeq.preprocessing.salmon import run_salmon_quant

logger = logging.getLogger(__name__)

def run_preprocessing_pipeline(config, checkpoint_mgr=None, sample_name=None):
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
        # Get the base directory where the script is located
        # Calculate the path to the workspace root from the current file
        SCRIPT_DIR = Path(__file__).resolve().parent
        PACKAGE_DIR = SCRIPT_DIR.parent  # bulkRNASeq
        WORKSPACE_ROOT = PACKAGE_DIR.parent.parent  # Workspace root
        
        # Setup logging first
        logger.info(f"Workspace root is {WORKSPACE_ROOT}")
        
        # Handle path resolution properly
        def resolve_path(path_str):
            """Resolve a path relative to workspace root if not absolute"""
            path = Path(path_str)
            if path.is_absolute():
                return path
            return WORKSPACE_ROOT / path
        
        # Get configuration parameters, using relative paths
        fastq_dir = resolve_path(config['input']['fastq_dir'])
        fastq_pattern = config['input'].get('fastq_pattern', '*.fq.gz')
        output_dir = resolve_path(config['output'].get('results_dir', 'results/preprocessing'))
        params = config.get('parameters', {})
        qc_params = config.get('qc', {})
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Resolve genome paths
        gtf_file = resolve_path(config['genome']['gtf_file']) if 'gtf_file' in config['genome'] else None
        
        # Check if we should restart from a specific step
        restart_from = params.get('restart_from', None)
        
        # Get list of FASTQ files
        logger.info(f"Looking for FASTQ files in {fastq_dir} with pattern {fastq_pattern}")
        input_fastq_files = list(fastq_dir.glob(fastq_pattern))
        
        # Log all found files
        logger.info(f"Found FASTQ files: {[f.name for f in input_fastq_files]}")

        # Filter input files based on sample name
        if sample_name:
            expected_file = f"{sample_name}.fq.gz"
            input_fastq_files = [f for f in input_fastq_files if f.name == expected_file]
            if not input_fastq_files:
                raise FileNotFoundError(f"No FASTQ files found for sample '{sample_name}' in {fastq_dir}")

        # Log the name of the selected FASTQ file
        logger.info(f"Using FASTQ file: {input_fastq_files[0].name}")  # Access the first file's name

        # Convert paths to strings
        input_fastq_files = [str(f) for f in input_fastq_files]
        
        # Set up FastQC output directory
        qc_output_dir = str(output_dir / 'fastqc_results')
        Path(qc_output_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize flags for step execution
        run_fastqc_step = True
        run_alignment_step = True
        run_quantification_step = True
        
        # Apply restart-from logic
        if restart_from:
            logger.info(f"Restarting pipeline from the '{restart_from}' step")
            # Skip steps before the restart point
            if restart_from == 'alignment':
                run_fastqc_step = False
                logger.info("Skipping FastQC step due to restart point")
            elif restart_from == 'quantification':
                run_fastqc_step = False
                run_alignment_step = False
                logger.info("Skipping FastQC and alignment steps due to restart point")
            elif restart_from == 'multiqc':
                run_fastqc_step = False
                run_alignment_step = False
                run_quantification_step = False
                logger.info("Skipping all steps except MultiQC due to restart point")
        
        # Check if we should skip FastQC
        skip_fastqc = params.get('skip_fastqc', False)
        fastqc_already_done = False
        
        # Check if FastQC files already exist
        input_file = input_fastq_files[0]  # Use the filtered file
        expected_fastqc_html = os.path.join(qc_output_dir, os.path.basename(input_file).replace('.fq.gz', '_fastqc.html'))
        expected_fastqc_zip = os.path.join(qc_output_dir, os.path.basename(input_file).replace('.fq.gz', '_fastqc.zip'))
        
        if skip_fastqc and (os.path.exists(expected_fastqc_html) or os.path.exists(expected_fastqc_zip)):
            logger.info(f"Skipping FastQC as outputs already exist and --skip-fastqc was specified")
            fastqc_already_done = True
        
        # Run initial quality control with parameters if available
        if qc_params:
            min_quality = qc_params.get('min_quality', 20)  # Default value if not set
            min_length = qc_params.get('min_length', 36)    # Default value if not set
            logger.info(f"Quality control parameters: min_quality={min_quality}, min_length={min_length}")
        
        # Run FastQC on the filtered input file if not skipped
        if run_fastqc_step and not fastqc_already_done:
            logger.info(f"Running FastQC on {input_file}")
            run_fastqc(input_file, qc_output_dir)
        
        # Setup logging for QC steps
        qc_logger = setup_logger('qc', qc_output_dir)
        
        # Determine which aligners to run
        run_multi_aligner = params.get('multi_aligner', False)
        selected_aligners = []
        
        if run_multi_aligner:
            # Run all available aligners defined in config
            available_aligners = list(config.get('aligners', {}).keys())
            logger.info(f"Multi-aligner mode: Running all available aligners: {available_aligners}")
            selected_aligners = available_aligners
        else:
            # Run only the single specified aligner
            default_aligner = 'hisat2'
            selected_aligner = params.get('aligner', default_aligner)
            logger.info(f"Running single aligner: {selected_aligner}")
            selected_aligners = [selected_aligner]
        
        # Create stats to track all outputs
        stats = {
            'fastqc_dir': qc_output_dir,
            'processed_files': input_fastq_files,  # Log all processed files
            'aligners': {}
        }
        
        # Run selected aligners if alignment step is enabled
        if run_alignment_step:
            # Run selected aligners
            for aligner_name in selected_aligners:
                logger.info(f"Running alignment with: {aligner_name}")
                
                # Create aligner-specific output directory
                alignment_dir = str(output_dir / f'aligned_reads_{aligner_name}')
                Path(alignment_dir).mkdir(parents=True, exist_ok=True)
                
                # Get aligner-specific parameters
                aligner_config = config.get('aligners', {}).get(aligner_name, {})
                if not aligner_config:
                    logger.warning(f"No configuration found for aligner {aligner_name}, skipping")
                    continue
                
                try:
                    # Run the appropriate aligner with proper path resolution
                    if aligner_name == 'hisat2':
                        hisat2_index = resolve_path(aligner_config.get('index_prefix'))
                        if not hisat2_index:
                            logger.warning("HISAT2 index not specified, skipping")
                            continue
                        
                        logger.info(f"Using HISAT2 index: {hisat2_index}")
                        
                        # Verify that the HISAT2 index files exist
                        index_file_1 = Path(f"{hisat2_index}.1.ht2")
                        if not index_file_1.exists():
                            logger.warning(f"HISAT2 index file not found: {index_file_1}")
                            logger.warning("Make sure the index prefix is correct (without .*.ht2 extension)")
                            # List files in the directory to help debug
                            index_dir = Path(hisat2_index).parent
                            if index_dir.exists():
                                logger.info(f"Files in {index_dir}:")
                                for file in index_dir.glob("*"):
                                    logger.info(f"  - {file.name}")
                            continue
                        
                        bam_file = align_reads(
                            input_file,
                            reference_genome=str(hisat2_index),
                            output_dir=alignment_dir,
                            threads=params.get('threads', 4)
                        )
                    
                    elif aligner_name == 'kallisto':
                        # Resolve kallisto index path
                        kallisto_index_path = resolve_path(aligner_config.get('index'))
                        if not kallisto_index_path:
                            logger.warning("Kallisto index not specified, skipping")
                            continue
                        
                        logger.info(f"Using Kallisto index: {kallisto_index_path}")
                        bam_file = run_kallisto_quant(
                            input_file,
                            output_dir=alignment_dir,
                            kallisto_index=str(kallisto_index_path),  # Changed parameter name to match function
                            threads=params.get('threads', 4),
                            bootstrap=aligner_config.get('bootstrap', 100)
                        )
                    
                    elif aligner_name == 'salmon':
                        salmon_index_path = resolve_path(aligner_config.get('index'))
                        if not salmon_index_path:
                            logger.warning("Salmon index not specified, skipping")
                            continue
                        
                        logger.info(f"Using Salmon index: {salmon_index_path}")
                        bam_file = run_salmon_quant(
                            input_file,
                            output_dir=alignment_dir,
                            index=str(salmon_index_path),  # Keep as index since that's what the function expects
                            threads=params.get('threads', 4),
                            library_type=aligner_config.get('library_type', 'A')
                        )
                    
                    else:
                        logger.warning(f"Unsupported aligner: {aligner_name}, skipping")
                        continue
                    
                    # Add alignment results to stats
                    stats['aligners'][aligner_name] = {
                        'bam_file': bam_file
                    }
                    
                    # Generate counts for this aligner if quantification step is enabled
                    if run_quantification_step and gtf_file:
                        counts_dir = str(output_dir / f'counts_{aligner_name}')
                        Path(counts_dir).mkdir(parents=True, exist_ok=True)
                        
                        # Get base name from original FASTQ for consistent naming
                        base_name = os.path.basename(input_file).replace('.fq.gz', '').replace('.fastq.gz', '')
                        counts_file = generate_counts(
                            bam_file,
                            gtf_file=str(gtf_file),
                            output_dir=counts_dir,
                            base_name=f"{base_name}_{aligner_name}"
                        )
                        
                        # Add quantification results to stats
                        stats['aligners'][aligner_name]['counts_file'] = counts_file
                    
                    logger.info(f"Completed {aligner_name} alignment and quantification")
                    
                except Exception as e:
                    logger.error(f"Error running {aligner_name}: {str(e)}")
                    # Continue with other aligners even if one fails
        
        # Save pipeline run statistics
        with open(os.path.join(output_dir, 'pipeline_stats.json'), 'w') as f:
            json.dump(stats, f, indent=4)
        
        logger.info("Preprocessing pipeline completed successfully")

        # Run MultiQC at the end if enabled in the config
        if "multiqc" in config.get('pipeline_steps', []):
            multiqc_output_dir = os.path.join(output_dir, "multiqc_report")
            Path(multiqc_output_dir).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Running MultiQC on {output_dir}")
            multiqc_cmd = f"multiqc {output_dir} -o {multiqc_output_dir}"
            os.system(multiqc_cmd)  # Execute MultiQC command
            
            logger.info(f"MultiQC report generated at {multiqc_output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error in preprocessing pipeline: {str(e)}")
        return False

