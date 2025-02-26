#!/usr/bin/env python3

# Script to run the RNAseq pipeline
# Script to call both preprocessing and postprocessing scripts

import argparse
import logging
import sys
import os
import yaml
from datetime import datetime
from .utils.logger import setup_logging
from .pipeline.step_runner import run_pipeline_step
from .utils.checkpoint import CheckpointManager

def load_config(config_file):
    """Load configuration from YAML file"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='bulkRNASeq: RNA-seq preprocessing and postprocessing pipeline')
    
    parser.add_argument('--mode', required=True, 
                        choices=['preprocessing', 'postprocessing', 'pre_post'],
                        help='Analysis mode to run')
    
    parser.add_argument('--config', required=True, 
                        help='Path to configuration YAML file')
    
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    
    return parser.parse_args()

def main():
    """Main entry point for the pipeline"""
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        sys.exit(1)
    
    # Initialize checkpoint manager
    checkpoint_dir = os.path.join(
        config.get('output', {}).get('results_dir', 'results'),
        '.checkpoints'
    )
    checkpoint_mgr = CheckpointManager(checkpoint_dir)
    
    # Run the selected pipeline mode
    try:
        if args.mode == 'preprocessing':
            logger.info("Running preprocessing pipeline")
            run_pipeline_step('preprocessing', config, logger, checkpoint_mgr, 'preprocessing')
            success = True
        elif args.mode == 'postprocessing':
            logger.info("Running postprocessing pipeline")
            run_pipeline_step('postprocessing', config, logger, checkpoint_mgr, 'postprocessing')
            success = True
        elif args.mode == 'pre_post':
            # Mode to run preprocessing and postprocessing
            logger.info("Running preprocessing and postprocessing pipeline")
            run_pipeline_step('preprocessing', config, logger, checkpoint_mgr, 'preprocessing')
            logger.info("Preprocessing completed, now running postprocessing")
            run_pipeline_step('postprocessing', config, logger, checkpoint_mgr, 'postprocessing')
            success = True
        
        if success:
            logger.info(f"{args.mode.capitalize()} pipeline completed successfully")
            sys.exit(0)
        else:
            logging.error(f"{args.mode.capitalize()} pipeline failed")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Pipeline error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
