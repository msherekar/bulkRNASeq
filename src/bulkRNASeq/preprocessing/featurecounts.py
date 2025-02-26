import argparse
import subprocess
import sys
import logging
import os

def setup_logger(prefix, output_dir):
    """
    Sets up a logger that writes to a file with the given prefix in the output directory,
    and also logs to the console.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    log_filename = os.path.join(output_dir, f"{prefix}_featureCounts.log")
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

def run_featurecounts(bam_file, output_dir, annotation_file, threads=8):
    """
    Runs featureCounts to quantify gene expression from a sorted BAM file.
    """
    # Expect the input bam_file to be something like: pranay_hisat2_sorted.bam
    prefix = os.path.basename(bam_file).replace("_hisat2_sorted.bam", "")
    
    logger = setup_logger(prefix, output_dir)
    
    # Define the output counts file
    output_counts = os.path.join(output_dir, f"{prefix}_counts.tsv")

    
    cmd = [
        "featureCounts",   # Updated: using the correct case
        "-T", str(threads),
        "-a", annotation_file,
        "-o", output_counts,
        bam_file
    ]
    
    logger.info("Running featureCounts with command: " + " ".join(cmd))
    print("Running featureCounts...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        success_msg = "featureCounts completed successfully."
        logger.info(success_msg)
        logger.info("featureCounts output:\n" + result.stdout)
        print(success_msg)
        print("Output counts file:", output_counts)
    except subprocess.CalledProcessError as e:
        error_msg = "featureCounts encountered an error:"
        logger.error(error_msg)
        logger.error(e.stderr)
        print(error_msg, e.stderr, file=sys.stderr)
        sys.exit(e.returncode)
