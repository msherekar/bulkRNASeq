#!/usr/bin/env python3

import logging
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AlignerBase(ABC):
    """Base class for all aligners"""
    
    def __init__(self, config_handler, output_base_dir):
        """
        Initialize aligner base
        
        Args:
            config_handler: Configuration handler
            output_base_dir (Path): Base output directory
        """
        self.config_handler = config_handler
        self.output_base_dir = output_base_dir
        self.pipeline_params = config_handler.get_pipeline_parameters()
        self.genome_paths = config_handler.get_genome_paths()
        self.name = self.__class__.__name__.lower().replace('aligner', '')
    
    def get_output_dir(self, input_file):
        """Get aligner-specific output directory"""
        output_dir = self.output_base_dir / f'aligned_reads_{self.name}'
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    @abstractmethod
    def run(self, input_file, run_quantification=True):
        """Run alignment and quantification"""
        pass
    
    def get_threads(self):
        """Get number of threads to use"""
        return self.pipeline_params.get('threads', 4) 