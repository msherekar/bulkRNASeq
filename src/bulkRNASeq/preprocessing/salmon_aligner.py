#!/usr/bin/env python3

import logging
from pathlib import Path

from .aligner_base import AlignerBase
from .salmon import run_salmon_quant

logger = logging.getLogger(__name__)

class SalmonAligner(AlignerBase):
    """Salmon aligner implementation"""
    
    def run(self, input_file, run_quantification=True):
        """
        Run Salmon quantification
        
        Args:
            input_file (str): Path to input FASTQ file
            run_quantification (bool): Not used for Salmon (included for API compatibility)
            
        Returns:
            dict: Results of salmon quantification
        """
        output_dir = self.get_output_dir(input_file)
        aligner_config = self.config_handler.get_aligner_config('salmon')
        
        if not aligner_config:
            logger.warning("No configuration found for Salmon")
            return None
        
        salmon_index = aligner_config.get('index')
        if not salmon_index:
            logger.warning("Salmon index not specified")
            return None
        
        logger.info(f"Using Salmon index: {salmon_index}")
        
        # Run Salmon quantification
        result_file = run_salmon_quant(
            input_file,
            output_dir=str(output_dir),
            index=str(salmon_index),
            threads=self.get_threads(),
            library_type=aligner_config.get('library_type', 'A')
        )
        
        return {
            'aligner': 'salmon',
            'result_file': result_file
        } 