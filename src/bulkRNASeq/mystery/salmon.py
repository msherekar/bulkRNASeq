import os
import subprocess
import sys
import logging

def setup_logger(prefix, output_dir):
    """
    Sets up a logger that writes to a file with the given prefix in the output directory,
    and also logs to the console.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    log_filename = os.path.join(output_dir, f"{prefix}_salmon_quant.log")
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

def run_salmon_quant(input_file, output_dir, salmon_index, threads=8):
    """
    Runs Salmon quantification on the given input FASTQ file using a pre-built Salmon index.
    
    Parameters:
      input_file: Path to the raw (or trimmed) FASTQ file (can be gzipped).
      output_dir: Directory where the Salmon output folder will be written.
      salmon_index: Path to the Salmon index directory.
      threads: Number of threads to use.
    """
    input_basename = os.path.basename(input_file)
    prefix = input_basename.split('.')[0]
    
    logger = setup_logger(prefix, output_dir)
    
    # Salmon creates its own output folder; here we define one using the prefix.
    salmon_out = os.path.join(output_dir, f"{prefix}_salmon")
    
    cmd = [
        "salmon", "quant",
        "-i", salmon_index,
        "-l", "A",         # Automatically detect library type
        "-r", input_file,
        "-p", str(threads),
        "-o", salmon_out
    ]
    
    logger.info("Running Salmon quantification with command: " + " ".join(cmd))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Salmon quantification completed successfully.")
        logger.info("Salmon output:\n" + result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Salmon quantification encountered an error:")
        logger.error(e.stderr)
        print("Salmon quantification encountered an error:", e.stderr, file=sys.stderr)
        sys.exit(e.returncode)
