#!/usr/bin/env python3

import logging
from pathlib import Path

from .aligner_base import AlignerBase
from .kallisto import run_kallisto_quant

logger = logging.getLogger(__name__)

class KallistoAligner(AlignerBase):
    """Kallisto aligner implementation"""
    
    def run(self, input_file, run_quantification=True):
        """
        Run Kallisto quantification
        
        Args:
            input_file (str): Path to input FASTQ file
            run_quantification (bool): Not used for Kallisto (included for API compatibility)
            
        Returns:
            dict: Results of kallisto quantification
        """
        output_dir = self.get_output_dir(input_file)
        aligner_config = self.config_handler.get_aligner_config('kallisto')
        
        if not aligner_config:
            logger.warning("No configuration found for Kallisto")
            return None
        
        kallisto_index = aligner_config.get('index')
        if not kallisto_index:
            logger.warning("Kallisto index not specified")
            return None
        
        logger.info(f"Using Kallisto index: {kallisto_index}")
        
        # Run Kallisto quantification
        result_file = run_kallisto_quant(
            input_file,
            output_dir=str(output_dir),
            kallisto_index=str(kallisto_index),
            threads=self.get_threads(),
            bootstrap=aligner_config.get('bootstrap', 100)
        )
        
        return {
            'aligner': 'kallisto',
            'result_file': result_file
        } 