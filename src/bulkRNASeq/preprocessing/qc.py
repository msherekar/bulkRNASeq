import argparse
import subprocess
import sys
import logging
import os
from pathlib import Path
import time
# Configure basic logging (this only sets a base format, individual loggers may override)
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

def run_fastqc(input_dir: str, output_dir: str) -> None:
    """
    Scan the input directory for FASTQ files (*.fastq.gz) and run FastQC on them.
    
    Args:
        input_dir: Directory containing FASTQ files.
        output_dir: Directory for FastQC output.
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        input_dir_path = Path(input_dir)

        # Scan for FASTQ files
        fastq_files = list(input_dir_path.glob("*.fastq.gz"))
        print(len(fastq_files), "files found")
        if not fastq_files:
            logging.warning(f"No FASTQ files found in {input_dir}")
            return
        
        # Convert list of paths to space-separated string
        fastq_files_str = " ".join(str(f) for f in fastq_files)
        
        cmd = f"fastqc --threads 8 {fastq_files_str} -o {output_dir}"
        print("Running command:", cmd)  # Debugging
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        # Handle command output
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


if __name__ == "__main__":
    # count time taken to run the script
    start_time = time.time()
    parser = argparse.ArgumentParser(description="FastQC pipeline")
    parser.add_argument("--input_dir", required=True, help="Directory containing FASTQ files")
    parser.add_argument("--output_dir", required=True, help="Directory for FastQC output")
    args = parser.parse_args()
    
    # Set up the logger (logs will be written to the output directory)
    logger = setup_logger("fastqc_pipeline", args.output_dir)
    
    # Run FastQC on the entire folder of FASTQ files
    run_fastqc(args.input_dir, args.output_dir)
    end_time = time.time()
    print(f"Time taken to run the script: {end_time - start_time} seconds")

#TODO: change output directory such that each fastqc file goes to its respective sample folder
