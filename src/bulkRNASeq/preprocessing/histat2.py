import argparse
import subprocess
import sys
import logging
import os
from pathlib import Path


def setup_logger(prefix, output_dir):
    """
    Sets up a logger that writes to a file with the given prefix in the output directory,
    and also logs to the console.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    log_filename = os.path.join(output_dir, f"{prefix}_hisat2_alignment.log")
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger


def run_hisat2_alignment(
    input_file: str,
    output_dir: str,
    hisat2_index: str,
    threads: int = 4,
    logger: logging.Logger = None
) -> str:
    """
    Run HISAT2 alignment on input FASTQ file.
    
    Args:
        input_file: Path to input FASTQ file
        output_dir: Directory for output files
        hisat2_index: Path prefix to HISAT2 index files
        threads: Number of threads to use
        logger: Logger instance
    """
    try:
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define output files
        sample_name = Path(input_file).stem.split('.')[0]
        bam_file = output_dir / f"{sample_name}.bam"
        log_file = output_dir / f"{sample_name}_hisat2_alignment.log"
        
        # Construct HISAT2 command
        hisat2_cmd = [
            'hisat2',
            '-p', str(threads),
            '-x', hisat2_index,
            '-U', input_file,  # For single-end reads
            '--new-summary',  # More detailed summary
            '--dta',  # Downstream transcriptome assembly
            '2>', str(log_file),  # Redirect stderr to log file
            '|',  # Pipe to samtools
            'samtools',
            'sort',
            '-@', str(threads),
            '-o', str(bam_file)
        ]
        
        # Run alignment
        if logger:
            logger.info(f"Running HISAT2 alignment for {sample_name}")
            logger.info(f"Command: {' '.join(hisat2_cmd)}")
        
        # Execute command
        process = subprocess.run(
            ' '.join(hisat2_cmd),
            shell=True,
            capture_output=True,
            text=True
        )
        
        # Check if BAM file was created
        if not bam_file.exists():
            raise RuntimeError(f"BAM file not created: {bam_file}")
        
        # Index BAM file
        subprocess.run(
            ['samtools', 'index', str(bam_file)],
            check=True
        )
        
        if logger:
            logger.info(f"Alignment completed for {sample_name}")
            logger.info(f"Output BAM: {bam_file}")
            logger.info(f"Log file: {log_file}")
        
        # Make sure to return the BAM file path
        return str(bam_file)  # Convert to string explicitly
        
    except subprocess.CalledProcessError as e:
        error_msg = f"HISAT2 alignment failed: {e.stderr}"
        if logger:
            logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    except Exception as e:
        # Log error but don't return None
        error_msg = f"Error during alignment: {str(e)}"
        if logger:
            logger.error(error_msg)
        raise RuntimeError(error_msg)  # Raise exception rather than returning None