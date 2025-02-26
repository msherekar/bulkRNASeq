import argparse
import subprocess
import sys
import logging
import os

def setup_logger(prefix, output_dir):
    """ Sets up logging for BAM processing. """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    log_filename = os.path.join(output_dir, f"{prefix}_bam_processing.log")
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

def run_bam_processing(input_sam, output_dir):
    """ Converts SAM to BAM, sorts, and indexes the BAM file using multi-threading where applicable. """
    prefix = os.path.basename(input_sam).replace("_hisat2.sam", "")
    logger = setup_logger(prefix, output_dir)

    bam_file = os.path.join(output_dir, f"{prefix}_hisat2.bam")
    sorted_bam = os.path.join(output_dir, f"{prefix}_hisat2_sorted.bam")

    try:
        logger.info("Converting SAM to BAM...")
        subprocess.run(["samtools", "view", "-bS", input_sam, "-o", bam_file], check=True)
        
        logger.info("Sorting BAM file using 8 cores...")
        subprocess.run(["samtools", "sort", "-@", "8", "-o", sorted_bam, bam_file], check=True)

        logger.info("Indexing BAM file...")
        subprocess.run(["samtools", "index", sorted_bam], check=True)

        logger.info("BAM processing completed successfully.")
        print(f"[INFO] BAM file processed: {sorted_bam}")
    
    except subprocess.CalledProcessError as e:
        logger.error("BAM processing encountered an error:")
        logger.error(e.stderr)
        print("BAM processing encountered an error:", e.stderr, file=sys.stderr)
        sys.exit(e.returncode)

 


