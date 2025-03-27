import os
import subprocess
import sys
import logging
import argparse
import time

def setup_logger(prefix, output_dir):
    os.makedirs(output_dir, exist_ok=True)
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

def run_kallisto_quant(input_dir, output_dir, kallisto_index, threads=8, bootstrap=100, timeout_seconds=3600):
    input_basename = os.path.basename(input_dir)
    prefix = input_basename.split('.')[0]

    os.makedirs(output_dir, exist_ok=True)
    logger = setup_logger(prefix, output_dir)

    kallisto_out = os.path.join(output_dir, f"{prefix}_kallisto")
    os.makedirs(kallisto_out, exist_ok=True)

    # Find paired-end FASTQ files
    fastq_files = sorted([f for f in os.listdir(input_dir) if f.endswith(".fastq.gz")])

    if len(fastq_files) < 2:
        logger.error(f"Not enough FASTQ files found in {input_dir}. Expected paired-end files.")
        return None

    fastq_1 = os.path.join(input_dir, fastq_files[0])
    fastq_2 = os.path.join(input_dir, fastq_files[1])

    cmd = [
        "kallisto", "quant",
        "-i", kallisto_index,
        "-o", kallisto_out,
        "-t", str(threads),
        "-b", str(bootstrap),
        "--paired",
        fastq_1, fastq_2
    ]
    
    logger.info("Running Kallisto quantification with command: " + " ".join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout_seconds)
        logger.info("Kallisto quantification completed successfully.")
        logger.info("Kallisto output:\n" + result.stdout)
    except subprocess.TimeoutExpired as e:
        logger.error(f"Kallisto quantification timed out after {timeout_seconds} seconds.")
        os.system(f"pkill -f kallisto")  # Kill Kallisto if needed
        return None
    except subprocess.CalledProcessError as e:
        logger.error(e.stderr)
        return None

    # Check all expected files exist
    expected_files = ["abundance.tsv", "run_info.json", "abundance.h5"]
    for file in expected_files:
        if not os.path.exists(os.path.join(kallisto_out, file)):
            logger.warning(f"Missing expected Kallisto output file: {file}")
            return None

    return os.path.join(kallisto_out, "abundance.tsv")

if __name__ == "__main__":
    start_time = time.time()
    
    parser = argparse.ArgumentParser(description="Kallisto quantification")
    parser.add_argument("--input_dir", required=True, help="Directory containing paired-end FASTQ files")
    parser.add_argument("--output_dir", required=True, help="Directory for Kallisto output")
    parser.add_argument("--kallisto_index", required=True, help="Path to the Kallisto index file")
    parser.add_argument("--threads", type=int, default=8, help="Number of threads to use")
    parser.add_argument("--bootstrap", type=int, default=100, help="Number of bootstrap samples for estimating uncertainty")
    parser.add_argument("--timeout_seconds", type=int, default=3600, help="Maximum number of seconds to wait for kallisto to complete")
    
    args = parser.parse_args()
    
    run_kallisto_quant(args.input_dir, args.output_dir, args.kallisto_index, args.threads, args.bootstrap, args.timeout_seconds)

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")
 