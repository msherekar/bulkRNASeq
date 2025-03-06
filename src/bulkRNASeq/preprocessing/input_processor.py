#!/usr/bin/env python3

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class InputProcessor:
    def __init__(self, fastq_dir, fastq_pattern='*.fq.gz'):
        """
        Initialize input processor
        
        Args:
            fastq_dir (Path): Directory containing FASTQ files
            fastq_pattern (str): Glob pattern for FASTQ files
        """
        self.fastq_dir = fastq_dir
        self.fastq_pattern = fastq_pattern
    
    def discover_input_files(self):
        """Discover all input FASTQ files matching the pattern"""
        logger.info(f"Looking for FASTQ files in {self.fastq_dir} with pattern {self.fastq_pattern}")
        input_fastq_files = list(self.fastq_dir.glob(self.fastq_pattern))
        
        logger.info(f"Found FASTQ files: {[f.name for f in input_fastq_files]}")
        return input_fastq_files
    
    def filter_by_sample(self, input_files, sample_name):
        """Filter input files based on sample name"""
        if not sample_name:
            return input_files
            
        expected_file = f"{sample_name}.fq.gz"
        filtered_files = [f for f in input_files if f.name == expected_file]
        
        if not filtered_files:
            raise FileNotFoundError(f"No FASTQ files found for sample '{sample_name}' in {self.fastq_dir}")
            
        logger.info(f"Using FASTQ file: {filtered_files[0].name}")
        return filtered_files 