#!/usr/bin/env python3

import argparse
import logging
import yaml
import sys
import os
from pathlib import Path
from ..utils.logger import setup_logging
from .pipeline_runner import run_postprocessing_pipeline

def main():
    """Main entry point for postprocessing pipeline."""
    parser = argparse.ArgumentParser(description="RNA-seq Postprocessing Pipeline")
    parser.add_argument("--config", required=True, help="Path to configuration file")
    parser.add_argument("--resume", action="store_true", help="Resume pipeline from last successful step")
    parser.add_argument("--sample", help="Sample name to use (replaces ${sample} in config)")
    
    # Analysis selection arguments
    parser.add_argument("--run-eda", action="store_true", help="Run exploratory data analysis")
    parser.add_argument("--run-qa", action="store_true", help="Run quality assessment")
    parser.add_argument("--run-kallisto", action="store_true", help="Run Kallisto analysis")
    parser.add_argument("--run-enrichment", action="store_true", help="Run enrichment analysis")
    parser.add_argument("--run-all", action="store_true", help="Run all analyses")
    parser.add_argument("--skip-report", action="store_true", help="Skip final report generation")
    
    # Failure behavior
    parser.add_argument("--continue-on-error", action="store_true", 
                        help="Continue pipeline even if an analysis fails")
    
    args = parser.parse_args()
    logger = setup_logging()
    
    try:
        # Load configuration
        with open(args.config) as f:
            config = yaml.safe_load(f)
        
        # Process sample replacements
        if args.sample:
            # Update all paths containing ${sample}
            for section in config:
                if isinstance(config[section], dict):
                    for key, value in config[section].items():
                        if isinstance(value, str) and "${sample}" in value:
                            config[section][key] = value.replace("${sample}", args.sample)
        
        # Initialize enabled_analyses if not present
        if 'enabled_analyses' not in config:
            config['enabled_analyses'] = {
                'eda': True,
                'qa': True,
                'kallisto': True,
                'enrichment': True,
                'report': True
            }
            
        # Override enabled analyses from command line
        if args.run_all:
            for analysis in ['eda', 'qa', 'kallisto', 'enrichment']:
                config['enabled_analyses'][analysis] = True
        else:
            # Only override if explicitly specified
            if args.run_eda:
                config['enabled_analyses']['eda'] = True
            if args.run_qa:
                config['enabled_analyses']['qa'] = True
            if args.run_kallisto:
                config['enabled_analyses']['kallisto'] = True
            if args.run_enrichment:
                config['enabled_analyses']['enrichment'] = True
        
        # Handle skip report flag
        if args.skip_report:
            config['enabled_analyses']['report'] = False
            
        # Set failure behavior
        if 'parameters' not in config:
            config['parameters'] = {}
        config['parameters']['fail_fast'] = not args.continue_on_error
            
        # Run pipeline
        success = run_postprocessing_pipeline(config)
        
        if success:
            logger.info("Pipeline completed successfully")
            sys.exit(0)
        else:
            logger.error("Pipeline completed with errors")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
