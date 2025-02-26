import os
import subprocess
import logging
from pathlib import Path

def run_featurecounts(
    input_bam: str,
    output_dir: str,
    gtf_file: str,
    threads: int = 8,
    logger: logging.Logger = None
) -> None:
    """
    Run featureCounts on aligned BAM file.
    
    Args:
        input_bam: Path to input BAM file
        output_dir: Directory for output files
        gtf_file: Path to GTF annotation file
        threads: Number of threads to use
        logger: Logger instance
    """
    try:
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get sample name from BAM file
        sample_name = Path(input_bam).stem
        if sample_name.endswith('.bam'):
            sample_name = sample_name[:-4]
        
        # Define output files with proper paths
        counts_file = output_dir / f"{sample_name}_counts.txt"
        log_file = output_dir / f"{sample_name}_featureCounts.log"
        
        if logger:
            logger.info(f"Running featureCounts for {sample_name}")
            logger.info(f"Input BAM: {input_bam}")
            logger.info(f"Output file: {counts_file}")
            logger.info(f"Log file: {log_file}")
        
        # Construct featureCounts command
        cmd = [
            'featureCounts',
            '-T', str(threads),
            '-a', str(gtf_file),
            '-o', str(counts_file),
            str(input_bam)
        ]
        
        # Run featureCounts and capture output
        with open(log_file, 'w') as log:
            result = subprocess.run(
                cmd,
                stdout=log,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        
        # Verify output files exist
        if not counts_file.exists():
            raise RuntimeError(f"Counts file not created: {counts_file}")
            
        if logger:
            logger.info(f"Quantification completed for {sample_name}")
            logger.info(f"Output file: {counts_file}")
            
    except subprocess.CalledProcessError as e:
        error_msg = f"featureCounts failed: {e.stderr}"
        if logger:
            logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    except Exception as e:
        error_msg = f"Error during quantification: {str(e)}"
        if logger:
            logger.error(error_msg)
        raise RuntimeError(error_msg) 