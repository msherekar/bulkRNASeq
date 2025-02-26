#!/usr/bin/env python3

import argparse
import logging
import yaml
import sys
from ..utils.logger import setup_logging
from .pipeline_runner import run_postprocessing_pipeline

def main():
    """Main entry point for postprocessing pipeline."""
    parser = argparse.ArgumentParser(description="RNA-seq Postprocessing Pipeline")
    parser.add_argument("--config", required=True, help="Path to configuration file")
    parser.add_argument("--resume", action="store_true", help="Resume pipeline from last successful step")
    
    args = parser.parse_args()
    logger = setup_logging()
    
    try:
        # Load configuration
        with open(args.config) as f:
            config = yaml.safe_load(f)
            
        # Run pipeline
        run_postprocessing_pipeline(config, logger, args.resume)
        
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
