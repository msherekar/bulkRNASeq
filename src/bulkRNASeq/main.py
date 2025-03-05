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
    
    # Add new arguments for sample and output
    parser.add_argument('--sample', required=True,
                        help='Sample name to process')
    
    parser.add_argument('--output', required=True,
                        help='Path to output file')
    
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
        
        # Add sample information to config
        if not 'sample' in config:
            config['sample'] = {}
        config['sample']['name'] = args.sample
        config['sample']['output_file'] = args.output
        
        logger.info(f"Processing sample: {args.sample}")
        logger.info(f"Output will be written to: {args.output}")
        
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
            logger.info("Running preprocessing and postprocessing pipeline")
            run_pipeline_step('preprocessing', config, logger, checkpoint_mgr, 'preprocessing')
            logger.info("Preprocessing completed, now running postprocessing")
            run_pipeline_step('postprocessing', config, logger, checkpoint_mgr, 'postprocessing')
            success = True
        
        # Generate the final report
        if success:
            logger.info("Generating final report")
            generate_final_report(config, args.output)
            logger.info(f"{args.mode.capitalize()} pipeline completed successfully")
            sys.exit(0)
        else:
            logging.error(f"{args.mode.capitalize()} pipeline failed")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Pipeline error: {str(e)}")
        sys.exit(1)

def generate_final_report(config, output_file):
    """Generate the final report for the sample"""
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Just before generating the report
    print(f"About to generate report at: {args.output}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Output directory exists: {os.path.exists(os.path.dirname(args.output))}")
    
    # Write a simple report
    with open(output_file, 'w') as f:
        f.write(f"# Analysis Report for {config['sample']['name']}\n\n")
        f.write(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Configuration\n\n")
        f.write("```yaml\n")
        yaml.dump(config, f, default_flow_style=False)
        f.write("```\n")
        f.flush()  # Ensure all data is written to disk
    
    # Verify file was created
    if os.path.exists(output_file):
        print(f"Final report successfully written to {output_file}")
    else:
        print(f"WARNING: Failed to create final report at {output_file}")

if __name__ == "__main__":
    main()
