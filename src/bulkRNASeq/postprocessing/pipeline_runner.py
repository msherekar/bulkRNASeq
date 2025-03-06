#!/usr/bin/env python3

import os
import logging
import pandas as pd
from pathlib import Path
import copy

# Import analysis modules
from .analyzers.eda_analyzer import EDAAnalyzer
from .analyzers.qa_analyzer import QAAnalyzer
from .analyzers.enrichment_analyzer import EnrichmentAnalyzer
from .analyzers.kallisto_analyzer import KallistoAnalyzer
from .reporters.markdown_reporter import MarkdownReporter

logger = logging.getLogger(__name__)

def run_postprocessing_pipeline(config, checkpoint_mgr=None, sample_name=None):
    """
    Main function to run the RNA-seq postprocessing pipeline.
    
    Args:
        config (dict): Configuration dictionary
        checkpoint_mgr: Checkpoint manager
        sample_name: Sample name to use for path substitution
        
    Returns:
        bool: Success status
    """
    try:
        # Perform sample_name substitution in paths if provided
        if sample_name:
            # Make a deep copy of config to avoid modifying the original
            config = copy.deepcopy(config)
            
            # Replace ${sample} in all string values
            for section in config:
                if isinstance(config[section], dict):
                    for key, value in config[section].items():
                        if isinstance(value, str) and "${sample}" in value:
                            config[section][key] = value.replace("${sample}", sample_name)
        
        # Extract configuration
        input_counts_file = config['input']['counts_file']
        output_dir = Path(config['output'].get('base_dir', 'results/postprocessing'))
        params = config.get('parameters', {})
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize results dictionary
        results = {
            'input_file': input_counts_file
        }
        
        # Verify input file exists
        if not os.path.exists(input_counts_file):
            # Try alternative naming pattern
            base_name = Path(input_counts_file).stem.replace('_counts', '').replace('.bam_counts', '')
            alt_counts_file = Path(input_counts_file).parent / f"{base_name}_counts.tsv"
            
            if os.path.exists(alt_counts_file):
                input_counts_file = str(alt_counts_file)
                logger.info(f"Using alternative counts file: {input_counts_file}")
                results['input_file'] = input_counts_file
            else:
                logger.error(f"Input counts file not found: {input_counts_file} or {alt_counts_file}")
                return False
        
        # Load count data for analysis
        df = pd.read_csv(input_counts_file, sep='\t', comment='#')
        sample_col = df.columns[-1]
        df['raw_counts'] = df[sample_col].copy()
        
        # ===== Step 1: Exploratory Data Analysis =====
        if not checkpoint_mgr or not checkpoint_mgr.should_skip_step('eda'):
            eda_analyzer = EDAAnalyzer(output_dir)
            results['eda'] = eda_analyzer.run_analysis(input_counts_file, params)
            
            if checkpoint_mgr:
                checkpoint_mgr.save_checkpoint('eda', 'completed')
        
        # ===== Step 2: Quality Assessment =====
        if not checkpoint_mgr or not checkpoint_mgr.should_skip_step('qa'):
            qa_analyzer = QAAnalyzer(output_dir)
            results['qa'] = qa_analyzer.run_analysis(df, params)
            
            if checkpoint_mgr:
                checkpoint_mgr.save_checkpoint('qa', 'completed')
        
        # ===== Step 3: Kallisto Analysis (if specified) =====
        kallisto_abundance_file = config['input'].get('kallisto_abundance', None)
        if kallisto_abundance_file and os.path.exists(kallisto_abundance_file) and \
           (not checkpoint_mgr or not checkpoint_mgr.should_skip_step('kallisto')):
            kallisto_analyzer = KallistoAnalyzer(output_dir)
            results['kallisto'] = kallisto_analyzer.run_analysis(kallisto_abundance_file, params)
            results['kallisto']['input_file'] = kallisto_abundance_file
            
            if checkpoint_mgr:
                checkpoint_mgr.save_checkpoint('kallisto', 'completed')
        
        # ===== Step 4: Enrichment Analysis =====
        if (params.get('go_enrichment', False) or params.get('network_analysis', False)) and \
           (not checkpoint_mgr or not checkpoint_mgr.should_skip_step('enrichment')):
            enrichment_analyzer = EnrichmentAnalyzer(output_dir)
            results['enrichment'] = enrichment_analyzer.run_analysis(df, params)
            
            if checkpoint_mgr:
                checkpoint_mgr.save_checkpoint('enrichment', 'completed')
        
        # ===== Step 5: Generate Final Report =====
        markdown_reporter = MarkdownReporter(output_dir)
        final_report = markdown_reporter.generate_report(results, df)
        results['final_report'] = final_report
        
        logger.info("Postprocessing completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in postprocessing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False 