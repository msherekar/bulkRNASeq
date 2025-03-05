import os
import subprocess
import sys
import logging

def setup_logger(prefix, output_dir):
    """
    Sets up a logger that writes to a file with the given prefix in the output directory,
    and also logs to the console.
    """
    os.makedirs(output_dir, exist_ok=True)  # Ensure directory exists before writing logs

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    log_filename = os.path.join(output_dir, f"{prefix}_kallisto_quant.log")
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

def run_kallisto_quant(input_file, output_dir, kallisto_index, threads=8, bootstrap=100):
    """
    Runs Kallisto quantification on the given input FASTQ file using a pre-built Kallisto index.
    
    Parameters:
      input_file: Path to the raw (or trimmed) FASTQ file (can be gzipped).
      output_dir: Directory where the Kallisto output folder will be written.
      kallisto_index: Path to the Kallisto index file.
      threads: Number of threads to use.
      bootstrap: Number of bootstrap samples for estimating uncertainty.
    """
    input_basename = os.path.basename(input_file)
    prefix = input_basename.split('.')[0]

    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists
    logger = setup_logger(prefix, output_dir)

    # Kallisto output folder
    kallisto_out = os.path.join(output_dir, f"{prefix}_kallisto")
    os.makedirs(kallisto_out, exist_ok=True)

    cmd = [
        "kallisto", "quant",
        "-i", kallisto_index,
        "-o", kallisto_out,
        "-t", str(threads),
        "-b", str(bootstrap),
        "--single", "-l", "200", "-s", "20",  # Modify if paired-end
        input_file
    ]
    
    logger.info("Running Kallisto quantification with command: " + " ".join(cmd))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Kallisto quantification completed successfully.")
        logger.info("Kallisto output:\n" + result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Kallisto quantification encountered an error:")
        logger.error(e.stderr)
        print("Kallisto quantification encountered an error:", e.stderr, file=sys.stderr)
        sys.exit(e.returncode)


if __name__ == "__main__":
    input = "/Users/mukulsherekar/pythonProject/bulkRNASeq-Project/tests/data/raw_fastq/mukul.fq.gz"
    output = "/Users/mukulsherekar/pythonProject/bulkRNASeq-Project/tests/data/results/preprocessing/aligned_reads_kallisto"
    index = "/Users/mukulsherekar/pythonProject/bulkRNASeq-Project/genome/kallisto_index"
    run_kallisto_quant(input, output, index)