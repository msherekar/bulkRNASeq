import argparse
import subprocess
import sys
import logging
import json
import os
import zipfile
from pathlib import Path
# TODO: file path and name for pranay_qc like why two folders

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def setup_logger(prefix, output_dir):
    """
    Sets up a logger that writes to a file with the given prefix in the output directory,
    and also logs to the console.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    log_filename = os.path.join(output_dir, f"{prefix}_fastqc_pipeline.log")
    # File handler for logging to a file
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Stream handler for logging to the console
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
    return logger

def run_fastqc(input_path: str, output_dir: str) -> None:
    """
    Run FastQC on input FASTQ file.
    
    Args:
        input_path: Path to FASTQ file
        output_dir: Directory for FastQC output
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Construct and run FastQC command
        cmd = f"fastqc {input_path} -o {output_dir}"
        logging.info(f"Running FastQC with command: {cmd}")
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logging.error("FastQC encountered an error:")
            logging.error(result.stderr)
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
            
        logging.info("FastQC analysis completed successfully")
        
    except Exception as e:
        logging.error(f"Error running FastQC: {str(e)}")
        raise
