#!/usr/bin/env python3

import os
import json
import logging
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)

class ReportManager:
    def __init__(self, output_dir):
        """
        Initialize report manager
        
        Args:
            output_dir (Path): Base output directory
        """
        self.output_dir = output_dir
    
    def save_pipeline_stats(self, stats):
        """
        Save pipeline statistics to JSON file
        
        Args:
            stats (dict): Pipeline statistics
        """
        stats_file = self.output_dir / 'pipeline_stats.json'
        
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=4)
        
        logger.info(f"Pipeline statistics saved to {stats_file}")
    
    def run_multiqc(self, directory, output_dir=None, sample_name=None):
        """
        Run MultiQC on the specified directory.
        
        Args:
            directory (str): Directory containing reports to analyze
            output_dir (str, optional): Output directory for the report
            sample_name (str, optional): Sample name to use as prefix
        """
        logger.info(f"Running MultiQC on {directory}")
        
        if output_dir is None:
            output_dir = os.path.join(directory, "multiqc_report")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Build MultiQC command with sample name prefix if provided
        multiqc_cmd = ["multiqc", directory, "-o", output_dir]
        
        if sample_name:
            # Use sample name as prefix for the report
            multiqc_cmd.extend(["--filename", f"{sample_name}_multiqc_report"])
            logger.info(f"Using sample name '{sample_name}' as MultiQC report prefix")
        
        try:
            subprocess.run(multiqc_cmd, check=True)
            logger.info(f"MultiQC report generated at {output_dir}")
            return os.path.join(output_dir, f"{'multiqc_report.html' if not sample_name else f'{sample_name}_report.html'}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running MultiQC: {e}")
            return None 