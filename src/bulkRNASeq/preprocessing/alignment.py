#!/usr/bin/env python3

import os
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

def align_reads(input_file: str, reference_genome: str, output_dir: str, threads: int = 4) -> str:
    """
    Align reads to reference genome using HISAT2.
    
    Args:
        input_file: Path to input FASTQ file
        reference_genome: Path to reference genome FASTA
        output_dir: Output directory for BAM files
        threads: Number of threads to use
        
    Returns:
        Path to output BAM file
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get base name for output
        base_name = os.path.basename(input_file).replace('.fq.gz', '').replace('.fastq.gz', '')
        output_bam = os.path.join(output_dir, f"{base_name}.bam")
        
        # Run HISAT2 alignment and pipe to samtools to create sorted BAM
        hisat2_cmd = f"hisat2 -p {threads} -x {reference_genome} -U {input_file}"
        samtools_cmd = f"samtools sort -@ {threads} -o {output_bam}"
        cmd = f"{hisat2_cmd} | {samtools_cmd}"
        
        logger.info(f"Running alignment with command: {cmd}")
        
        # Run the pipeline
        hisat2_proc = subprocess.Popen(
            hisat2_cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        samtools_proc = subprocess.Popen(
            samtools_cmd.split(),
            stdin=hisat2_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Close hisat2's stdout to signal completion to samtools
        hisat2_proc.stdout.close()
        
        # Get the output and errors
        _, hisat2_stderr = hisat2_proc.communicate()
        _, samtools_stderr = samtools_proc.communicate()
        
        # Check return codes
        if hisat2_proc.returncode != 0:
            logger.error("HISAT2 alignment encountered an error:")
            logger.error(hisat2_stderr)
            raise subprocess.CalledProcessError(
                hisat2_proc.returncode, hisat2_cmd, stderr=hisat2_stderr
            )
        
        if samtools_proc.returncode != 0:
            logger.error("Samtools sort encountered an error:")
            logger.error(samtools_stderr)
            raise subprocess.CalledProcessError(
                samtools_proc.returncode, samtools_cmd, stderr=samtools_stderr
            )
        
        # Index the BAM file
        index_cmd = f"samtools index {output_bam}"
        logger.info(f"Indexing BAM file: {index_cmd}")
        
        result = subprocess.run(
            index_cmd.split(),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error("BAM indexing encountered an error:")
            logger.error(result.stderr)
            raise subprocess.CalledProcessError(
                result.returncode, index_cmd, result.stdout, result.stderr
            )
        
        logger.info("Alignment and indexing completed successfully")
        return output_bam
        
    except Exception as e:
        logger.error(f"Error in alignment: {str(e)}")
        raise

def generate_counts(bam_file: str, gtf_file: str, output_dir: str, base_name: str = None) -> str:
    """
    Generate count matrix from BAM file using featureCounts.
    
    Args:
        bam_file: Path to input BAM file
        gtf_file: Path to GTF annotation file
        output_dir: Output directory for count files
        
    Returns:
        Path to output counts file
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Use provided base_name or extract from BAM file
        if base_name is None:
            base_name = os.path.basename(bam_file).replace('.bam', '')
        output_file = os.path.join(output_dir, f"{base_name}_counts.tsv")
        
        # Run featureCounts
        cmd = f"featureCounts -a {gtf_file} -o {output_file} {bam_file}"
        logger.info(f"Generating counts with command: {cmd}")
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error("featureCounts encountered an error:")
            logger.error(result.stderr)
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
        
        logger.info("Count generation completed successfully")
        return output_file
        
    except Exception as e:
        logger.error(f"Error generating counts: {str(e)}")
        raise
