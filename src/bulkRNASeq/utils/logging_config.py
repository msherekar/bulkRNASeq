import sys
from pathlib import Path
from .checkpoint import CheckpointManager
import logging
from .logger import setup_logging

def run_pipeline_step(
    step: str,
    config: dict,
    logger: logging.Logger,
    checkpoint_mgr: CheckpointManager
) -> None:
    """Run a single pipeline step with checkpoint tracking."""
    try:
        if checkpoint_mgr.should_skip_step(step):
            logger.info(f"[yellow]Skipping {step} (already completed successfully)[/]")
            return

        logger.info(f"[blue]Starting {step} step[/]")
        checkpoint_mgr.save_checkpoint(step, 'running')

        # Run the step based on the pipeline type
        if step == 'preprocessing':
            from ..preprocessing.main import main as preprocessing_main
            preprocessing_main(config)
        elif step == 'postprocessing':
            from ..postprocessing.main import main as postprocessing_main
            postprocessing_main(config)
        
        # Mark step as completed
        checkpoint_mgr.save_checkpoint(step, 'completed')
        logger.info(f"[green]Successfully completed {step} step[/]")

    except Exception as e:
        checkpoint_mgr.save_checkpoint(step, 'failed', {'error': str(e)})
        logger.error(f"[red]Error in {step} step: {str(e)}[/]")
        raise

def create_step_args(step: str, config: dict) -> list:
    """Create command-line arguments for each step."""
    if step == "qc":
        return [
            '--step', 'qc',
            '--input', config['input']['fastq_dir'],
            '--output', config['output']['qc_dir']
        ]
    elif step == "alignment":
        return [
            '--step', 'alignment',
            '--input', config['input']['fastq_dir'],
            '--output', config['output']['aligned_dir'],
            '--hisat2-index', config['aligners']['hisat2']['index_prefix'],
            '--threads', str(config['parameters']['threads'])
        ]
    elif step == "quantification":
        sample_name = Path(config['input']['fastq_dir']).stem
        if sample_name.endswith(('.fq', '.fastq', '.fq.gz', '.fastq.gz')):
            sample_name = sample_name.split('.')[0]
        
        bam_file = Path(config['output']['aligned_dir']) / f"{sample_name}.bam"
        
        if not bam_file.exists():
            raise FileNotFoundError(f"BAM file not found: {bam_file}")
        
        return [
            '--step', 'quant',
            '--input', str(bam_file),
            '--output', config['output']['counts_dir'],
            '--annotation', config['genome']['gtf_file'],
            '--threads', str(config['parameters']['threads'])
        ]
