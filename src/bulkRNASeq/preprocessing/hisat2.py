import argparse
import subprocess
import sys
import logging
from pathlib import Path

def run_hisat2_alignment_pair(
    input_file_1: str,
    input_file_2: str,
    output_dir: str,
    hisat2_index: str,
    threads: int = 4,
    logger: logging.Logger = None
) -> str:
    """
    Run HISAT2 paired-end alignment on the given FASTQ files.
    
    Args:
        input_file_1: Path to the first FASTQ file (pair 1)
        input_file_2: Path to the second FASTQ file (pair 2)
        output_dir: Directory for output files
        hisat2_index: Path prefix to HISAT2 index files
        threads: Number of threads to use
        logger: Logger instance
        
    Returns:
        The path to the output BAM file as a string.
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Derive sample name from the first file name (assumes format: SAMPLE_1.fastq.gz)
        sample_name = Path(input_file_1).name.replace("_1.fastq.gz", "").replace("_1_trimmed.fastq.gz", "")
        bam_file = output_dir / f"{sample_name}.bam"
        log_file = output_dir / f"{sample_name}_hisat2_alignment.log"
        
        # Build the HISAT2 command for paired-end reads
        hisat2_cmd = (
            f"hisat2 -p {threads} -x {hisat2_index} "
            f"-1 {input_file_1} -2 {input_file_2} "
            f"--new-summary --dta 2> {log_file} | "
            f"samtools sort -@ {threads} -o {bam_file}"
        )
        
        if logger:
            logger.info(f"Running HISAT2 paired-end alignment for sample {sample_name}")
            logger.info(f"Command: {hisat2_cmd}")
        
        # Execute the command
        process = subprocess.run(
            hisat2_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        mapped_reads = 0
        unmapped_reads = 0

        try:
            with open(log_file, 'r') as log:
                for line in log:
                    if "aligned concordantly exactly 1 time" in line:
                        mapped_reads += int(line.split()[0])
                    elif "aligned concordantly >1 times" in line:
                        mapped_reads += int(line.split()[0])
                    elif "not aligned concordantly" in line:
                        unmapped_reads += int(line.split()[0])
                    elif "aligned discordantly 1 time" in line:
                        mapped_reads += int(line.split()[0])
                    elif "aligned 0 times" in line:  # Single-end mapping failure
                        unmapped_reads += int(line.split()[0])
            if logger:
                logger.info(f"Sample {sample_name}: {mapped_reads} reads mapped, {unmapped_reads} reads not mapped")
        except Exception as e:
            if logger:
                    logger.warning(f"Could not parse HISAT2 log for {sample_name}: {str(e)}")


        
        if process.returncode != 0:
            error_msg = f"HISAT2 alignment failed for sample {sample_name}: {process.stderr}"
            if logger:
                logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Verify that the BAM file was created
        if not bam_file.exists():
            raise RuntimeError(f"BAM file not created: {bam_file}")
        
        # Index the BAM file
        subprocess.run(
            ['samtools', 'index', str(bam_file)],
            check=True
        )
        
        if logger:
            logger.info(f"Alignment completed for sample {sample_name}")
            logger.info(f"Output BAM: {bam_file}")
            logger.info(f"Log file: {log_file}")
        
        return str(bam_file)
        
    except subprocess.CalledProcessError as e:
        error_msg = f"HISAT2 alignment failed for sample {sample_name}: {e.stderr}"
        if logger:
            logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    except Exception as e:
        error_msg = f"Error during alignment for sample {sample_name}: {str(e)}"
        if logger:
            logger.error(error_msg)
        raise RuntimeError(error_msg)

def run_hisat2_alignment_single(
    input_file: str,
    output_dir: str,
    hisat2_index: str,
    threads: int = 4,
    logger: logging.Logger = None
) -> str:
    """
    Run HISAT2 single-end alignment on the given FASTQ file.
    
    Args:
        input_file: Path to the FASTQ file
        output_dir: Directory for output files
        hisat2_index: Path prefix to HISAT2 index files
        threads: Number of threads to use
        logger: Logger instance
        
    Returns:
        The path to the output BAM file as a string.
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Derive sample name from the file name
        sample_name = Path(input_file).stem
        if sample_name.endswith('.fastq'):
            sample_name = sample_name[:-6]
        elif sample_name.endswith('_trimmed'):
            sample_name = sample_name[:-8]
            
        bam_file = output_dir / f"{sample_name}.bam"
        log_file = output_dir / f"{sample_name}_hisat2_alignment.log"
        
        # Build the HISAT2 command for single-end reads
        hisat2_cmd = (
            f"hisat2 -p {threads} -x {hisat2_index} "
            f"-U {input_file} "
            f"--new-summary --dta 2> {log_file} | "
            f"samtools sort -@ {threads} -o {bam_file}"
        )
        
        if logger:
            logger.info(f"Running HISAT2 single-end alignment for sample {sample_name}")
            logger.info(f"Command: {hisat2_cmd}")
        
        # Execute the command
        process = subprocess.run(
            hisat2_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        mapped_reads = 0
        unmapped_reads = 0

        try:
            with open(log_file, 'r') as log:
                for line in log:
                    if "aligned exactly 1 time" in line:
                        mapped_reads += int(line.split()[0])
                    elif "aligned >1 times" in line:
                        mapped_reads += int(line.split()[0])
                    elif "aligned 0 times" in line:
                        unmapped_reads += int(line.split()[0])
            if logger:
                logger.info(f"Sample {sample_name}: {mapped_reads} reads mapped, {unmapped_reads} reads not mapped")
        except Exception as e:
            if logger:
                logger.warning(f"Could not parse HISAT2 log for {sample_name}: {str(e)}")
        
        if process.returncode != 0:
            error_msg = f"HISAT2 alignment failed for sample {sample_name}: {process.stderr}"
            if logger:
                logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Verify that the BAM file was created
        if not bam_file.exists():
            raise RuntimeError(f"BAM file not created: {bam_file}")
        
        # Index the BAM file
        subprocess.run(
            ['samtools', 'index', str(bam_file)],
            check=True
        )
        
        if logger:
            logger.info(f"Alignment completed for sample {sample_name}")
            logger.info(f"Output BAM: {bam_file}")
            logger.info(f"Log file: {log_file}")
        
        return str(bam_file)
        
    except subprocess.CalledProcessError as e:
        error_msg = f"HISAT2 alignment failed for sample {sample_name}: {e.stderr}"
        if logger:
            logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    except Exception as e:
        error_msg = f"Error during alignment for sample {sample_name}: {str(e)}"
        if logger:
            logger.error(error_msg)
        raise RuntimeError(error_msg)

def traverse_and_align(
    input_dir: str,
    output_dir: str,
    hisat2_index: str,
    threads: int = 4,
    is_paired: bool = True,
    logger: logging.Logger = None
):
    """
    Traverse the input directory for FASTQ files and run HISAT2 alignment.
    
    Args:
        input_dir: Directory containing FASTQ files
        output_dir: Directory for output files
        hisat2_index: Path prefix to HISAT2 index files
        threads: Number of threads to use
        is_paired: Whether to use paired-end alignment (True) or single-end alignment (False)
        logger: Logger instance
    """
    input_dir_path = Path(input_dir)
    
    if is_paired:
        # Paired-end mode: find all files ending with '_1.fastq.gz' or '_1_trimmed.fastq.gz'
        fastq_files_1 = list(input_dir_path.glob("*_1*.fastq.gz"))
        if not fastq_files_1:
            msg = f"No paired FASTQ files found in {input_dir}"
            if logger:
                logger.error(msg)
            raise FileNotFoundError(msg)
        
        for file1 in fastq_files_1:
            # Extract sample name, handling different naming conventions
            if "_1_trimmed.fastq.gz" in file1.name:
                sample_name = file1.name.replace("_1_trimmed.fastq.gz", "")
                file2 = input_dir_path / f"{sample_name}_2_trimmed.fastq.gz"
            else:
                sample_name = file1.name.replace("_1.fastq.gz", "")
                file2 = input_dir_path / f"{sample_name}_2.fastq.gz"
                
            if not file2.exists():
                if logger:
                    logger.warning(f"Paired file for {file1} not found. Skipping sample {sample_name}.")
                continue
            try:
                run_hisat2_alignment_pair(
                    str(file1),
                    str(file2),
                    output_dir,
                    hisat2_index,
                    threads,
                    logger
                )
            except Exception as e:
                if logger:
                    logger.error(f"Failed alignment for sample {sample_name}: {str(e)}")
                else:
                    print(f"Failed alignment for sample {sample_name}: {str(e)}", file=sys.stderr)
    else:
        # Single-end mode: find all fastq files
        fastq_files = list(input_dir_path.glob("*.fastq.gz"))
        if not fastq_files:
            msg = f"No FASTQ files found in {input_dir}"
            if logger:
                logger.error(msg)
            raise FileNotFoundError(msg)
        
        for file in fastq_files:
            try:
                run_hisat2_alignment_single(
                    str(file),
                    output_dir,
                    hisat2_index,
                    threads,
                    logger
                )
            except Exception as e:
                sample_name = file.stem
                if logger:
                    logger.error(f"Failed alignment for sample {sample_name}: {str(e)}")
                else:
                    print(f"Failed alignment for sample {sample_name}: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HISAT2 alignment for RNA-seq data")
    parser.add_argument("--input_dir", required=True, help="Directory containing input FASTQ files")
    parser.add_argument("--output_dir", required=True, help="Directory for output files")
    parser.add_argument("--hisat2_index", required=True, help="Path prefix to HISAT2 index files")
    parser.add_argument("--threads", type=int, default=8, help="Number of threads to use")
    parser.add_argument("--paired", action="store_true", help="Use paired-end mode (default)")
    parser.add_argument("--single", action="store_true", help="Use single-end mode")
    args = parser.parse_args()
    
    # Setup logger
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    
    # Determine alignment mode
    is_paired = not args.single
    if args.paired and args.single:
        logger.warning("Both --paired and --single flags provided. Using paired-end mode.")
        is_paired = True
    
    traverse_and_align(
        args.input_dir,
        args.output_dir,
        args.hisat2_index,
        args.threads,
        is_paired,
        logger
    )
