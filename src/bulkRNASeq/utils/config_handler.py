#!/usr/bin/env python3

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigHandler:
    def __init__(self, config, workspace_root=None):
        """
        Initialize configuration handler
        
        Args:
            config (dict): Configuration dictionary
            workspace_root (Path): Root directory of workspace
        """
        self.config = config
        
        # Calculate workspace root if not provided
        if workspace_root is None:
            script_dir = Path(__file__).resolve().parent  # utils
            package_dir = script_dir.parent  # bulkRNASeq
            self.workspace_root = package_dir.parent.parent  # Workspace root
        else:
            self.workspace_root = workspace_root
            
        logger.info(f"Workspace root is {self.workspace_root}")
    
    def resolve_path(self, path_str):
        """Resolve a path relative to workspace root if not absolute"""
        if path_str is None:
            return None
            
        path = Path(path_str)
        if path.is_absolute():
            return path
        return self.workspace_root / path
    
    def get_input_paths(self):
        """Get and resolve input file paths"""
        fastq_dir = self.resolve_path(self.config['input']['fastq_dir'])
        fastq_pattern = self.config['input'].get('fastq_pattern', '*.fq.gz')
        
        return {
            'fastq_dir': fastq_dir,
            'fastq_pattern': fastq_pattern
        }
    
    def get_output_paths(self):
        """Get and resolve output directory paths"""
        output_dir = self.resolve_path(self.config['output'].get('results_dir', 'results/preprocessing'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        qc_output_dir = output_dir / 'fastqc_results'
        qc_output_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            'results_dir': output_dir,
            'fastqc_dir': qc_output_dir
        }
    
    def get_genome_paths(self):
        """Get and resolve genome file paths"""
        genome_config = self.config.get('genome', {})
        gtf_file = self.resolve_path(genome_config.get('gtf_file')) if 'gtf_file' in genome_config else None
        
        return {
            'gtf_file': gtf_file
        }
    
    def get_aligner_config(self, aligner_name):
        """Get configuration for specific aligner"""
        aligner_config = self.config.get('aligners', {}).get(aligner_name, {})
        
        # Resolve paths in the aligner config
        resolved_config = {}
        for key, value in aligner_config.items():
            if key.endswith('_prefix') or key.endswith('_index') or key.endswith('_file'):
                resolved_config[key] = self.resolve_path(value)
            else:
                resolved_config[key] = value
                
        return resolved_config
    
    def get_pipeline_parameters(self):
        """Get general pipeline parameters"""
        return self.config.get('parameters', {})
    
    def get_qc_parameters(self):
        """Get quality control parameters"""
        return self.config.get('qc', {}) 