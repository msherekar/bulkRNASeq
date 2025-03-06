#!/usr/bin/env python3

import logging
from pathlib import Path
import os

# Import local modules
try:
    from .qc import run_fastqc, setup_logger
    from ..utils.config_handler import ConfigHandler
    from .input_processor import InputProcessor
    from .aligner_factory import AlignerFactory
    from .reporting import ReportManager
except ImportError:
    # Fallback imports for direct module execution
    from bulkRNASeq.preprocessing.qc import run_fastqc, setup_logger
    from bulkRNASeq.utils.config_handler import ConfigHandler
    from bulkRNASeq.preprocessing.input_processor import InputProcessor
    from bulkRNASeq.preprocessing.aligner_factory import AlignerFactory
    from bulkRNASeq.preprocessing.reporting import ReportManager

logger = logging.getLogger(__name__)

def run_preprocessing_pipeline(config, checkpoint_mgr=None, sample_name=None):
    """
    Main function to run the RNA-seq preprocessing pipeline.
    
    Args:
        config (dict): Configuration dictionary
        checkpoint_mgr: Checkpoint manager (not used currently)
        sample_name (str): Optional sample name to process
        
    Returns:
        bool: Success status
    """
    try:
        # Initialize configuration handler
        config_handler = ConfigHandler(config)
        
        # Get input and output paths
        input_paths = config_handler.get_input_paths()
        output_paths = config_handler.get_output_paths()
        
        # Initialize input processor
        input_processor = InputProcessor(
            input_paths['fastq_dir'],
            input_paths['fastq_pattern']
        )
        
        # Discover and filter input files
        input_files = input_processor.discover_input_files()
        filtered_files = input_processor.filter_by_sample(input_files, sample_name)
        
        if not filtered_files:
            logger.error("No input files found after filtering")
            return False
        
        # Get pipeline parameters
        params = config_handler.get_pipeline_parameters()
        
        # Determine which steps to execute
        restart_from = params.get('restart_from', None)
        skip_fastqc = params.get('skip_fastqc', False)
        
        run_fastqc_step = True
        run_alignment_step = True
        run_quantification_step = True
        
        # Apply restart-from logic
        if restart_from:
            logger.info(f"Restarting pipeline from the '{restart_from}' step")
            if restart_from == 'alignment':
                run_fastqc_step = False
            elif restart_from == 'quantification':
                run_fastqc_step = False
                run_alignment_step = False
            elif restart_from == 'multiqc':
                run_fastqc_step = False
                run_alignment_step = False
                run_quantification_step = False
        
        # Initialize stats dictionary
        stats = {
            'fastqc_dir': str(output_paths['fastqc_dir']),
            'processed_files': [str(f) for f in filtered_files],
            'aligners': {}
        }
        
        # Run FastQC if needed
        if run_fastqc_step and not skip_fastqc:
            for input_file in filtered_files:
                logger.info(f"Running FastQC on {input_file}")
                run_fastqc(str(input_file), str(output_paths['fastqc_dir']))
        
        # Run alignment and quantification if needed
        if run_alignment_step:
            # Get selected aligners using factory
            selected_aligners = AlignerFactory.get_available_aligners(config_handler)
            
            # Run alignments
            for aligner_name in selected_aligners:
                # Create aligner instance using factory
                aligner = AlignerFactory.create_aligner(
                    aligner_name,
                    config_handler,
                    output_paths['results_dir']
                )
                
                if not aligner:
                    logger.warning(f"Could not create aligner: {aligner_name}")
                    continue
                
                # Run for each input file
                for input_file in filtered_files:
                    logger.info(f"Running {aligner_name} on {input_file}")
                    
                    result = aligner.run(
                        str(input_file),
                        run_quantification=run_quantification_step
                    )
                    
                    if result:
                        # Add to stats
                        if aligner_name not in stats['aligners']:
                            stats['aligners'][aligner_name] = {}
                        
                        file_key = input_file.stem
                        stats['aligners'][aligner_name][file_key] = result
        
        # Generate reports
        report_manager = ReportManager(output_paths['results_dir'])
        report_manager.save_pipeline_stats(stats)
        
        # Run MultiQC only if needed
        try:
            # Use the sample_name parameter directly
            if sample_name:
                logger.info(f"Using provided sample name '{sample_name}' for MultiQC report")
            else:
                # Fallback to extracting from input_file if sample_name not provided
                sample_name = Path(input_file).stem.split('.')[0]
                logger.info(f"Extracted sample name '{sample_name}' for MultiQC report")
            
            # Initialize the ReportManager
            multiqc_output_dir = os.path.join(output_paths['results_dir'], "multiqc_report")
            report_manager = ReportManager(output_dir=multiqc_output_dir)
            
            # Call run_multiqc with the directory and sample name
            multiqc_report = report_manager.run_multiqc(
                directory=output_paths['results_dir'],
                sample_name=sample_name
            )
            
            if multiqc_report:
                logger.info(f"MultiQC report generated at {multiqc_report}")
            else:
                logger.warning("MultiQC report generation failed")
        except Exception as e:
            logger.error(f"Error running MultiQC: {str(e)}")
            logger.warning("Continuing pipeline despite MultiQC error")
            # Don't fail the entire pipeline for a MultiQC error
        
        logger.info("Preprocessing pipeline completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in preprocessing pipeline: {str(e)}")
        return False
