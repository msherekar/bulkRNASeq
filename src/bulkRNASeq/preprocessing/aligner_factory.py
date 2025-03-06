#!/usr/bin/env python3

import logging

from .hisat2_aligner import Hisat2Aligner
from .kallisto_aligner import KallistoAligner
from .salmon_aligner import SalmonAligner

logger = logging.getLogger(__name__)

class AlignerFactory:
    """Factory class for creating aligner instances"""
    
    @staticmethod
    def create_aligner(aligner_name, config_handler, output_base_dir):
        """
        Create an aligner instance based on the aligner name
        
        Args:
            aligner_name (str): Name of the aligner to create
            config_handler: Configuration handler
            output_base_dir (Path): Base output directory
            
        Returns:
            Aligner instance or None if aligner not supported
        """
        if aligner_name == 'hisat2':
            return Hisat2Aligner(config_handler, output_base_dir)
        elif aligner_name == 'kallisto':
            return KallistoAligner(config_handler, output_base_dir)
        
        else:
            logger.warning(f"Unsupported aligner: {aligner_name}")
            return None
    
    @staticmethod
    def get_available_aligners(config_handler):
        """
        Get list of available aligners based on configuration
        
        Args:
            config_handler: Configuration handler
            
        Returns:
            list: List of available aligner names
        """
        params = config_handler.get_pipeline_parameters()
        run_multi_aligner = params.get('multi_aligner', False)
        
        if run_multi_aligner:
            # Run all available aligners defined in config
            available_aligners = list(config_handler.config.get('aligners', {}).keys())
            logger.info(f"Multi-aligner mode: Running all available aligners: {available_aligners}")
            return available_aligners
        else:
            # Run only the single specified aligner
            default_aligner = 'kallisto'
            selected_aligner = params.get('aligner', default_aligner)
            logger.info(f"Running single aligner: {selected_aligner}")
            return [selected_aligner] 