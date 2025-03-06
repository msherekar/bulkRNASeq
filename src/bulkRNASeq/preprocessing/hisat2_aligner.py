#!/usr/bin/env python3

import logging
from pathlib import Path
import os

from .aligner_base import AlignerBase
from .histat2 import run_hisat2_alignment
from .featurecounts import run_featurecounts

logger = logging.getLogger(__name__)

class Hisat2Aligner(AlignerBase):
    """HISAT2 aligner implementation"""
    
    def run(self, input_file, run_quantification=True):
        """
        Run HISAT2 alignment and optionally feature counting
        
        Args:
            input_file (str): Path to input FASTQ file
            run_quantification (bool): Whether to run feature counting
            
        Returns:
            dict: Results of alignment and quantification
        """
        output_dir = self.get_output_dir(input_file)
        aligner_config = self.config_handler.get_aligner_config('hisat2')
        
        if not aligner_config:
            logger.warning("No configuration found for HISAT2")
            return None
        
        hisat2_index = aligner_config.get('index_prefix')
        if not hisat2_index:
            logger.warning("HISAT2 index not specified")
            return None
        
        logger.info(f"Using HISAT2 index: {hisat2_index}")
        
        # Verify that the HISAT2 index files exist
        index_file_1 = Path(f"{hisat2_index}.1.ht2")
        if not index_file_1.exists():
            logger.warning(f"HISAT2 index file not found: {index_file_1}")
            logger.warning("Make sure the index prefix is correct (without .*.ht2 extension)")
            
            # List files in the directory to help debug
            index_dir = Path(hisat2_index).parent
            if index_dir.exists():
                logger.info(f"Files in {index_dir}:")
                for file in index_dir.glob("*"):
                    logger.info(f"  - {file.name}")
            return None
        
        # Run HISAT2 alignment
        bam_file = run_hisat2_alignment(
            input_file,
            output_dir=str(output_dir),
            hisat2_index=str(hisat2_index),
            threads=self.get_threads()
        )
        
        # Add validation check
        if not bam_file:
            logger.error("HISAT2 alignment failed to return a valid BAM file path")
            return None
        
        # Continue only if bam_file is valid
        results = {
            'aligner': 'hisat2',
            'bam_file': bam_file
        }
        
        # Generate counts using featureCounts if requested
        if run_quantification and self.genome_paths['gtf_file']:
            counts_dir = self.output_base_dir / f'counts_hisat2'
            counts_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                if not os.path.exists(bam_file):
                    logger.error(f"BAM file does not exist: {bam_file}")
                    return results  # Return without counts_file in results
                
                logger.info(f"Running featureCounts on BAM file: {bam_file}")
                logger.info(f"Using annotation file: {self.genome_paths['gtf_file']}")
                logger.info(f"Output directory: {counts_dir}")
                
                # Ensure correct parameter names based on featurecounts.py implementation
                run_featurecounts(
                    bam_file=bam_file,  # Use explicit named parameter
                    output_dir=str(counts_dir),
                    annotation_file=str(self.genome_paths['gtf_file']),
                    threads=self.get_threads()
                )
                
                # Verify the output file was created
                base_name = Path(input_file).stem.replace('.fq', '').replace('.fastq', '')
                counts_file = str(counts_dir / f"{base_name}_counts.tsv")
                
                if not os.path.exists(counts_file):
                    logger.warning(f"Expected counts file not found: {counts_file}")
                else:
                    logger.info(f"Counts file generated: {counts_file}")
                    results['counts_file'] = counts_file
                
            except Exception as e:
                logger.error(f"Error in featureCounts: {str(e)}")
                # Continue gracefully - don't add counts_file to results
        
        return results 