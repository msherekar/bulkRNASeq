import logging
from pathlib import Path
from typing import Dict, Optional
from .deseq import run_deseq_analysis
from .visualization import RNASeqVisualizer
import pandas as pd

def run_deseq_step(
    config: Dict,
    logger: logging.Logger,
    checkpoint_mgr: Optional['CheckpointManager'] = None
) -> None:
    """Run DESeq2 analysis step."""
    try:
        if checkpoint_mgr:
            checkpoint_mgr.save_checkpoint('deseq', 'running')
            
        output_dir = Path(config['output']['deseq_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        run_deseq_analysis(
            counts_file=config['input']['counts_file'],
            metadata_file=config['input']['metadata_file'],
            output_dir=str(output_dir),
            design_formula=config['parameters'].get('design_formula', '~condition'),
            contrast=config['parameters'].get('contrast', None),
            threads=8,
            logger=logger
        )
        
        if checkpoint_mgr:
            checkpoint_mgr.save_checkpoint('deseq', 'completed')
            
    except Exception as e:
        if checkpoint_mgr:
            checkpoint_mgr.save_checkpoint('deseq', 'failed', {'error': str(e)})
        raise

def run_visualization_step(
    config: Dict,
    logger: logging.Logger,
    checkpoint_mgr: Optional['CheckpointManager'] = None
) -> None:
    """Run visualization step."""
    try:
        if checkpoint_mgr:
            checkpoint_mgr.save_checkpoint('visualization', 'running')
            
        output_dir = Path(config['output']['plots_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        deseq_results = pd.read_csv(
            Path(config['output']['deseq_dir']) / "deseq2_results.csv"
        )
        counts_data = pd.read_csv(config['input']['counts_file'], index_col=0)
        metadata = pd.read_csv(config['input']['metadata_file'], index_col=0)
        
        # Generate visualizations
        visualizer = RNASeqVisualizer(str(output_dir), logger)
        visualizer.plot_pca(counts_data, metadata)
        visualizer.plot_volcano(deseq_results)
        
        if checkpoint_mgr:
            checkpoint_mgr.save_checkpoint('visualization', 'completed')
            
    except Exception as e:
        if checkpoint_mgr:
            checkpoint_mgr.save_checkpoint('visualization', 'failed', {'error': str(e)})
        raise 