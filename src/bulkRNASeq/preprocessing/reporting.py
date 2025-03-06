#!/usr/bin/env python3

import os
import json
import logging
from pathlib import Path

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
    
    def run_multiqc(self, include_subfolders=True):
        """
        Run MultiQC to generate comprehensive report
        
        Args:
            include_subfolders (bool): Whether to include subfolders in MultiQC analysis
        """
        multiqc_output_dir = self.output_dir / "multiqc_report"
        multiqc_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Construct multiqc command
        search_dir = str(self.output_dir)
        multiqc_cmd = f"multiqc {search_dir} -o {multiqc_output_dir}"
        
        logger.info(f"Running MultiQC on {search_dir}")
        os.system(multiqc_cmd)  # Execute MultiQC command
        
        logger.info(f"MultiQC report generated at {multiqc_output_dir}") 