import sys
import logging
from pathlib import Path
from typing import List, Optional, Callable
from ..utils.checkpoint import CheckpointManager

def get_pipeline_runner(pipeline_type: str) -> Callable:
    """Dynamically import and return the appropriate pipeline runner function."""
    if pipeline_type == 'preprocessing':
        from ..preprocessing.pipeline_runner import run_preprocessing_pipeline as pipeline_runner
    elif pipeline_type == 'postprocessing':
        from ..postprocessing.pipeline_runner import run_postprocessing_pipeline as pipeline_runner
    else:
        raise ValueError(f"Unknown pipeline type: {pipeline_type}")
    return pipeline_runner

def create_step_args(step: str, config: dict) -> list:
    """Create command-line arguments for each step."""
    threads = 8  # Fixed to 8 threads
    
    if step == "qc":
        return [
            '--step', 'qc',
            '--input', config['input']['fastq_dir'],
            '--output', config['output']['qc_dir']
        ]
    elif step == "fastqc":  # Add a specific step for FastQC
        return [
            '--step', 'fastqc',
            '--input', config['input']['fastq_dir'],
            '--output', config['output']['qc_dir'],
            '--pattern', config['input'].get('fastq_pattern', '*.fq.gz')
        ]
    elif step == "alignment":
        return [
            '--step', 'alignment',
            '--input', config['input']['fastq_dir'],
            '--output', config['output']['aligned_dir'],
            '--hisat2-index', config['aligners']['hisat2']['index_prefix'],
            '--threads', str(threads)
        ]
    elif step == "quantification":
        # Get the correct BAM file path
        aligned_dir = Path(config['output']['aligned_dir'])
        
        # List all BAM files in the aligned directory
        bam_files = list(aligned_dir.glob("*.bam"))
        if not bam_files:
            raise FileNotFoundError(f"No BAM files found in {aligned_dir}")
        
        # Use the first BAM file found
        bam_file = bam_files[0]
        
        # Create output directory if it doesn't exist
        counts_dir = Path(config['output']['counts_dir'])
        counts_dir.mkdir(parents=True, exist_ok=True)
        
        return [
            '--step', 'quant',
            '--input', str(bam_file),
            '--output', str(counts_dir),
            '--annotation', config['genome']['gtf_file'],
            '--threads', str(threads)
        ]

def run_pipeline_step(
    step: str,
    config: dict,
    logger: logging.Logger,
    checkpoint_mgr: CheckpointManager,
    pipeline_type: str = 'preprocessing'
) -> None:
    """Run a single pipeline step with checkpoint tracking."""
    try:
        if checkpoint_mgr.should_skip_step(step):
            logger.info(f"[yellow]Skipping {step} (already completed successfully)[/]")
            return

        logger.info(f"[blue]Starting {step} step[/]")
        checkpoint_mgr.save_checkpoint(step, 'running')

        # Verify input/output directories exist
        if step == "quantification":
            aligned_dir = Path(config['output']['aligned_dir'])
            counts_dir = Path(config['output']['counts_dir'])
            
            if not aligned_dir.exists():
                raise FileNotFoundError(f"Alignment directory not found: {aligned_dir}")
            
            counts_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Input directory: {aligned_dir}")
            logger.info(f"Output directory: {counts_dir}")

        # Get the appropriate pipeline runner
        pipeline_runner = get_pipeline_runner(pipeline_type)
        
        # Run the pipeline
        sample_name = config.get('sample', {}).get('name')
        success = pipeline_runner(config, checkpoint_mgr, sample_name)

        
        if not success:
            raise RuntimeError(f"Pipeline step {step} failed")
        
        checkpoint_mgr.save_checkpoint(step, 'completed')
        logger.info(f"[green]Successfully completed {step} step[/]")

    except Exception as e:
        checkpoint_mgr.save_checkpoint(step, 'failed', {'error': str(e)})
        logger.error(f"[red]Error in {step} step: {str(e)}[/]")
        raise 