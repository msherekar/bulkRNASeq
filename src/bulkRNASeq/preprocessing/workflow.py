#!/usr/bin/env python3

import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
from Bio import SeqIO

def calculate_gc_content(sequence):
    """Calculate GC content percentage of a DNA sequence."""
    sequence = sequence.upper()
    gc_count = sequence.count('G') + sequence.count('C')
    total = len(sequence)
    return (gc_count / total * 100) if total > 0 else 0

logger = logging.getLogger(__name__)

def run_preprocessing_workflow(fastq_files, output_dir, params):
    """
    Run preprocessing workflow on RNA-seq FASTQ files.
    
    Args:
        fastq_files (list): List of input FASTQ files
        output_dir (str): Output directory path
        params (dict): Processing parameters
    """
    try:
        logger.info("Running preprocessing workflow...")
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Process each FASTQ file
        for fastq_file in fastq_files:
            logger.info(f"Processing file: {fastq_file}")
            
            # Generate initial QC report
            qc_stats = generate_qc_report(fastq_file, output_dir)
            
            logger.info(f"QC report generated: {qc_stats}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error in preprocessing workflow: {str(e)}")
        return False

def generate_qc_report(fastq_file, output_dir):
    """
    Generate comprehensive QC report for a FASTQ file.
    """
    # Initialize statistics
    stats = {
        'total_reads': 0,
        'total_bases': 0,
        'gc_content': 0,
        'avg_quality': 0,
        'n_content': 0,
        'read_lengths': []
    }
    
    # Process FASTQ file
    with open(fastq_file, 'r') as f:
        for record in SeqIO.parse(f, 'fastq'):
            stats['total_reads'] += 1
            seq = str(record.seq)
            stats['total_bases'] += len(seq)
            stats['gc_content'] += calculate_gc_content(seq)
            stats['read_lengths'].append(len(seq))
            stats['avg_quality'] += sum(record.letter_annotations['phred_quality'])
            stats['n_content'] += seq.count('N')
    
    # Calculate averages
    if stats['total_reads'] > 0:
        stats['gc_content'] /= stats['total_reads']
        stats['avg_quality'] /= stats['total_bases']
        stats['n_content'] = (stats['n_content'] / stats['total_bases']) * 100
    
    # Write report
    report_path = os.path.join(output_dir, f"{os.path.basename(fastq_file)}_qc_report.txt")
    with open(report_path, 'w') as f:
        f.write("===== FastQ Quality Control Report =====\n\n")
        f.write(f"Analysis Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input File: {os.path.basename(fastq_file)}\n\n")
        
        f.write("--- Summary Statistics ---\n")
        f.write(f"Total Reads: {stats['total_reads']:,}\n")
        f.write(f"Total Bases: {stats['total_bases']:,}\n")
        f.write(f"Average Read Length: {stats['total_bases']/stats['total_reads']:.2f}\n")
        f.write(f"GC Content: {stats['gc_content']:.2f}%\n")
        f.write(f"Average Quality Score: {stats['avg_quality']:.2f}\n")
        f.write(f"N Content: {stats['n_content']:.2f}%\n")
    
    return stats

def plot_quality_distribution(fastq_file, output_dir):
    """
    Plot distribution of base qualities across reads.
    """
    qualities = []
    positions = []
    
    with open(fastq_file, 'r') as f:
        for record in SeqIO.parse(f, 'fastq'):
            qual_scores = record.letter_annotations['phred_quality']
            for pos, score in enumerate(qual_scores):
                qualities.append(score)
                positions.append(pos + 1)
    
    plt.figure(figsize=(10, 6))
    sns.boxplot(x=positions, y=qualities)
    plt.xlabel('Position in Read')
    plt.ylabel('Quality Score')
    plt.title('Quality Scores Distribution Across Read Positions')
    plt.savefig(os.path.join(output_dir, f"{os.path.basename(fastq_file)}_quality_dist.png"))
    plt.close()

def plot_length_distribution(fastq_file, output_dir):
    """
    Plot distribution of read lengths.
    """
    lengths = []
    
    with open(fastq_file, 'r') as f:
        for record in SeqIO.parse(f, 'fastq'):
            lengths.append(len(record.seq))
    
    plt.figure(figsize=(10, 6))
    sns.histplot(lengths, bins=50)
    plt.xlabel('Read Length')
    plt.ylabel('Count')
    plt.title('Read Length Distribution')
    plt.savefig(os.path.join(output_dir, f"{os.path.basename(fastq_file)}_length_dist.png"))
    plt.close()

def plot_base_composition(fastq_file, output_dir):
    """
    Plot base composition across read positions.
    """
    base_counts = {}
    max_length = 0
    
    with open(fastq_file, 'r') as f:
        for record in SeqIO.parse(f, 'fastq'):
            seq = str(record.seq)
            max_length = max(max_length, len(seq))
            
            for pos, base in enumerate(seq):
                if pos not in base_counts:
                    base_counts[pos] = {'A': 0, 'C': 0, 'G': 0, 'T': 0, 'N': 0}
                base_counts[pos][base] += 1
    
    positions = list(range(1, max_length + 1))
    bases = ['A', 'C', 'G', 'T', 'N']
    data = {base: [base_counts[pos][base] for pos in range(max_length)] for base in bases}
    
    plt.figure(figsize=(15, 8))
    for base in bases:
        plt.plot(positions, data[base], label=base)
    
    plt.xlabel('Position in Read')
    plt.ylabel('Count')
    plt.title('Base Composition Across Read Positions')
    plt.legend()
    plt.savefig(os.path.join(output_dir, f"{os.path.basename(fastq_file)}_base_composition.png"))
    plt.close()