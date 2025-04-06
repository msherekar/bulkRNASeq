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
    logger = logging.getLogger(prefix)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
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

def get_completed_sample_ids(output_dir):
    """
    Scans the output directory for existing featureCounts results and returns
    a set of sample IDs that have already been processed.
    
    Args:
        output_dir (str): Directory containing featureCounts output files
    
    Returns:
        set: Set of sample IDs that have already been processed
    """
    completed_ids = set()
    output_path = Path(output_dir)
    
    # Skip if output directory doesn't exist
    if not output_path.exists():
        return completed_ids
    
    # Look for files matching SRR*_counts.tsv pattern
    for counts_file in output_path.glob("SRR*_counts.tsv"):
        # Check if the file is complete (non-empty and has a summary file)
        if counts_file.stat().st_size > 0:
            summary_file = Path(str(counts_file) + ".summary")
            if summary_file.exists() and summary_file.stat().st_size > 0:
                # Extract sample ID (remove _counts.tsv from filename)
                sample_id = counts_file.stem.replace("_counts", "")
                completed_ids.add(sample_id)
                print(f"Found existing results for sample: {sample_id}")
    
    print(f"Found {len(completed_ids)} already processed samples in {output_dir}")
    return completed_ids

def run_featurecounts(bam_file, output_dir, annotation_file, threads=8):
    """
    Runs featureCounts to quantify gene expression from a sorted BAM file.
    Automatically detects if the reads are paired-end or single-end.
    
    Args:
        bam_file (str): Path to the BAM file
        output_dir (str): Directory where output files will be stored
        annotation_file (str): Path to the genome annotation file (GTF/GFF)
        threads (int): Number of threads to use
        
    Returns:
        bool: True if featureCounts ran successfully, False on error
    """
    # Expect BAM filenames like: SRR16101435.bam
    prefix = os.path.basename(bam_file).replace(".bam", "")
    
    logger = setup_logger(prefix, output_dir)
    
    # Define the output counts file
    output_counts = os.path.join(output_dir, f"{prefix}_counts.tsv")

    # Check if the BAM file contains paired-end reads using samtools
    check_paired_cmd = ["samtools", "view", "-c", "-f", "1", bam_file]
    try:
        paired_count = int(subprocess.check_output(check_paired_cmd, text=True).strip())
        is_paired = paired_count > 0
        logger.info(f"Detected {'paired-end' if is_paired else 'single-end'} reads in {bam_file}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Could not determine if reads are paired-end: {e}")
        is_paired = False

    # Start base command
    cmd = [
        "featureCounts",
        "-T", str(threads),
    ]

    # Add -p flag only for paired-end reads
    if is_paired:
        cmd.append("-p")

    # Add remaining required arguments
    cmd += [
        "-a", annotation_file,
        "-o", output_counts,
        bam_file
    ]

    

    
    logger.info(f"Running featureCounts for {prefix}...")
    logger.info("Command: " + " ".join(cmd))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        success_msg = f"featureCounts completed successfully for {prefix}."
        logger.info(success_msg)
        logger.info("featureCounts output:\n" + result.stdout)
        print(success_msg)
        print("Output counts file:", output_counts)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = f"featureCounts encountered an error for {prefix}:"
        logger.error(error_msg)
        logger.error(e.stderr)
        print(error_msg, e.stderr, file=sys.stderr)
        return False

def run_featurecounts_on_directory(input_dir, output_dir, annotation_file, threads=8, force_rerun=False):
    """
    Traverses the input directory for BAM files and runs featureCounts on each one.
    Skips files that have already been processed.
    
    Args:
        input_dir (str): Directory containing input BAM files
        output_dir (str): Directory where output files will be stored
        annotation_file (str): Path to the genome annotation file (GTF/GFF)
        threads (int): Number of threads to use
        force_rerun (bool): If True, rerun featureCounts even if output exists
    """
    input_dir_path = Path(input_dir)
    
    # First, get the list of samples that have already been processed
    completed_sample_ids = set()
    if not force_rerun:
        completed_sample_ids = get_completed_sample_ids(output_dir)
    
    # Find all BAM files matching SRR pattern
    all_bam_files = [f for f in input_dir_path.glob("SRR*.bam") if "tmp" not in f.name]
    
    if not all_bam_files:
        print(f"[ERROR] No SRR*.bam files found in {input_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Filter out BAM files that have already been processed
    bam_files_to_process = []
    for bam_file in all_bam_files:
        # Extract sample ID from BAM filename
        sample_id = bam_file.stem  # removes .bam extension
        
        # Skip this file if it's already been processed
        if not force_rerun and sample_id in completed_sample_ids:
            print(f"Skipping {sample_id}: already processed")
            continue
        
        bam_files_to_process.append(bam_file)
    
    # Check if we have any files to process
    if not bam_files_to_process:
        print(f"All {len(all_bam_files)} BAM files have already been processed. Nothing to do.")
        return
    
    print(f"Found {len(bam_files_to_process)} BAM files to process out of {len(all_bam_files)} total.")
    
    # Process the remaining BAM files
    successes = 0
    failures = 0
    for bam_file in bam_files_to_process:
        if run_featurecounts(str(bam_file), output_dir, annotation_file, threads):
            successes += 1
        else:
            failures += 1
    
    print(f"featureCounts processing complete. Successfully processed {successes} files with {failures} failures.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run featureCounts on all BAM files in a directory")
    parser.add_argument("--input_dir", required=True, help="Directory containing BAM files")
    parser.add_argument("--output_dir", required=True, help="Directory for output count files")
    parser.add_argument("--annotation_file", required=True, help="Path to the annotation GTF/GFF file")
    parser.add_argument("--threads", type=int, default=8, help="Number of threads to use")
    parser.add_argument("--force", action="store_true", help="Force rerun of featureCounts even if output exists")

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    run_featurecounts_on_directory(args.input_dir, args.output_dir, args.annotation_file, args.threads, args.force)
