import subprocess
import logging
from pathlib import Path
import sys
import time
import argparse
import os
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

def run_trim_single(input_file: Path, output_dir: Path, trimmomatic_jar: str,
                    threads: int = 8, phred: str = "phred33",
                    trimming_options: str = "TRAILING:10", logger: logging.Logger = None) -> None:
    """
    Run Trimmomatic in single-end mode.
    Command example:
    trimmomatic SE -threads 4 data/demo.fastq data/demo_trimmed.fastq TRAILING:10 -phred33
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    # Use the sample name (remove _1 or _2 suffix if present) for naming outputs.
    sample_name = input_file.stem
    if sample_name.endswith("_1") or sample_name.endswith("_2"):
        sample_name = sample_name[:-2]
    output_file = output_dir / f"{sample_name}_trimmed.fastq.gz"
    log_file = output_dir / f"{sample_name}_trimming.log"
    
    cmd = [
         "trimmomatic",
         "SE",
         "-threads", str(threads),
         str(input_file),
         str(output_file),
         trimming_options,
         f"-{phred}"
    ]
    if logger:
         logger.info("Running single-end trimming:\n" + " ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
         message = f"Single-end trimming failed for {input_file}:\n{result.stderr}"
         if logger:
             logger.error(message)
         else:
             print(message)
    else:
         message = f"Single-end trimming completed for {input_file}."
         if logger:
             logger.info(message)
         else:
             print(message)

def run_trim_paired(forward_file: Path, reverse_file: Path, output_dir: Path, trimmomatic_jar: str,
                    threads: int = 4, phred: str = "phred33",
                    trimming_options: str = "TRAILING:10",
                    logger: logging.Logger = None) -> None:
    """
    Run Trimmomatic in paired-end mode.
    Command structure:
    trimmomatic PE -threads 4 <input 1> <input 2> <paired output 1> <unpaired output 1>
         <paired output 2> <unpaired output 2> -trimlog <log_file> <trimming_options> -phred33
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_name = forward_file.stem
    # Remove the _1 suffix (assumes paired file ends with _1 and _2)
    if sample_name.endswith("_1"):
         sample_name = sample_name[:-2]
    paired_forward_output = output_dir / f"{sample_name}_1_trimmed.fastq.gz"
    unpaired_forward_output = output_dir / f"{sample_name}_1_unpaired.fastq.gz"
    paired_reverse_output = output_dir / f"{sample_name}_2_trimmed.fastq.gz"
    unpaired_reverse_output = output_dir / f"{sample_name}_2_unpaired.fastq.gz"
    log_file = output_dir / f"{sample_name}_trimming.log"
    
    cmd = [
         "trimmomatic",
         "PE",
         "-threads", str(threads),
         str(forward_file),
         str(reverse_file),
         str(paired_forward_output),
         str(unpaired_forward_output),
         str(paired_reverse_output),
         str(unpaired_reverse_output)
    ]
    # Append trimming options (splitting on whitespace)
    cmd.extend(trimming_options.split())
    cmd.append(f"-{phred}")
    
    if logger:
         logger.info("Running paired-end trimming:\n" + " ".join(cmd))
    result = subprocess.run(
    cmd,
    stdout=open(output_dir / "trimmomatic_summary.log", "w"),  # Save summary log
    stderr=subprocess.PIPE,  # Capture only errors
    text=True
)

    if result.returncode != 0:
         message = (f"Paired-end trimming failed for {forward_file} and {reverse_file}:\n"
                    f"{result.stderr}")
         if logger:
             logger.error(message)
         else:
             print(message)
    else:
         message = f"Paired-end trimming completed for {forward_file} and {reverse_file}."
         if logger:
             logger.info(message)
         else:
             print(message)

def run_trim_pipeline(input_dir: Path, output_dir: Path, trimmomatic_jar: str,
                      threads: int = 8, phred: str = "phred33",
                      single_trim_options: str = "TRAILING:10",
                      paired_trim_options: str = "TRAILING:10",
                      logger: logging.Logger = None) -> None:
    """
    Scan the input directory for FASTQ files (assumed to end with .fastq.gz).
    For each sample, detect if both paired files exist:
      - Files ending with _1.fastq.gz are assumed to be the forward reads.
      - The corresponding _2.fastq.gz file is searched for in the same directory.
    If both exist, run paired-end trimming; otherwise, run single-end trimming.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    processed_samples = set()
    
    fastq_files = list(input_dir.glob("*.fastq.gz"))
    if logger:
        logger.info(f"Found {len(fastq_files)} FASTQ files in {input_dir}.")
    else:
        print(f"Found {len(fastq_files)} FASTQ files in {input_dir}.")
    
    for fastq_file in fastq_files:
         fname = fastq_file.name
         if fname.endswith("_1.fastq.gz"):
              sample = fname.replace("_1.fastq.gz", "")
              if sample in processed_samples:
                  continue
              reverse_file = fastq_file.with_name(f"{sample}_2.fastq.gz")
              if reverse_file.exists():
                   if logger:
                       logger.info(f"Found paired files for sample {sample}.")
                   run_trim_paired(fastq_file, reverse_file, output_dir, trimmomatic_jar,
                                   threads=threads, phred=phred, trimming_options=paired_trim_options, logger=logger)
              else:
                   if logger:
                       logger.info(f"No pair found for {fastq_file}; processing as single-end.")
                   run_trim_single(fastq_file, output_dir, trimmomatic_jar,
                                   threads=threads, phred=phred, trimming_options=single_trim_options, logger=logger)
              processed_samples.add(sample)
         elif fname.endswith("_2.fastq.gz"):
              sample = fname.replace("_2.fastq.gz", "")
              paired_candidate = fastq_file.with_name(f"{sample}_1.fastq.gz")
              if paired_candidate.exists():
                  if sample not in processed_samples:
                      if logger:
                          logger.info(f"Found paired files for sample {sample} (detected in _2 branch).")
                      run_trim_paired(paired_candidate, fastq_file, output_dir, trimmomatic_jar,
                                      threads=threads, phred=phred, trimming_options=paired_trim_options, logger=logger)
                      processed_samples.add(sample)
              else:
                   if logger:
                       logger.info(f"Processing {fastq_file} as single-end (no corresponding _1 found).")
                   run_trim_single(fastq_file, output_dir, trimmomatic_jar,
                                   threads=threads, phred=phred, trimming_options=single_trim_options, logger=logger)
                   processed_samples.add(sample)
         else:
              sample = fastq_file.stem
              if sample in processed_samples:
                  continue
              if logger:
                  logger.info(f"Processing {fastq_file} as single-end (non-standard naming).")
              run_trim_single(fastq_file, output_dir, trimmomatic_jar,
                              threads=threads, phred=phred, trimming_options=single_trim_options, logger=logger)
              processed_samples.add(sample)

# Main Execution
if __name__ == "__main__":
    start_time = time.time()
    
    parser = argparse.ArgumentParser(description="Trimming pipeline")
    parser.add_argument("--input_dir", required=True, help="Directory containing FASTQ files")
    parser.add_argument("--output_dir", required=True, help="Directory for trimmed files")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads for Trimmomatic")
    parser.add_argument("--phred", choices=["phred33", "phred64"], default="phred33", help="Phred score encoding")
    parser.add_argument("--trimmomatic_jar", required=True, help="Path to the Trimmomatic JAR file")
    parser.add_argument("--single_trim_options", default="TRAILING:10", help="Trimmomatic options for single-end trimming")
    parser.add_argument("--paired_trim_options", default="TRAILING:10", help="Trimmomatic options for paired-end trimming")
    
    args = parser.parse_args()
    
    # Set up the logger (logs will be written to the output directory)
    logger = setup_logger("trimming_pipeline", args.output_dir)
    
    run_trim_pipeline(args.input_dir, args.output_dir, args.trimmomatic_jar,
                      threads=args.threads, phred=args.phred,
                      single_trim_options=args.single_trim_options,
                      paired_trim_options=args.paired_trim_options,
                      logger=logger)

    end_time = time.time()
    print(f"Time taken to run the script: {end_time - start_time:.2f} seconds")
