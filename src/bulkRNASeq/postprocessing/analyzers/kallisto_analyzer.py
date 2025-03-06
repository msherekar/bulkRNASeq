#!/usr/bin/env python3

import os
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class KallistoAnalyzer:
    """Kallisto-specific analysis for RNA-seq data"""
    
    def __init__(self, output_dir):
        """
        Initialize Kallisto analyzer
        
        Args:
            output_dir (str): Directory for output files
        """
        self.output_dir = Path(output_dir) / 'kallisto_analysis'
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_analysis(self, kallisto_file, params=None):
        """
        Run Kallisto-specific analyses
        
        Args:
            kallisto_file (str): Path to Kallisto abundance file
            params (dict): Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        params = params or {}
        results = {}
        
        try:
            if not os.path.exists(kallisto_file):
                logger.warning(f"Kallisto file not found: {kallisto_file}")
                return {'error': f"File not found: {kallisto_file}"}
            
            logger.info(f"Running Kallisto analyses on {kallisto_file}")
            
            # Load Kallisto data
            kallisto_data = pd.read_csv(kallisto_file, sep='\t')
            
            # Identify sample columns (all except metadata columns)
            # This assumes the first two columns are not sample data
            sample_cols = kallisto_data.columns[2:]
            
            if len(sample_cols) == 0:
                logger.warning("No sample columns found in Kallisto data")
                return {'error': "No sample columns found in Kallisto data"}
            
            logger.info(f"Found {len(sample_cols)} samples in Kallisto data")
            
            # Run PCA
            results['pca'] = self._run_pca(kallisto_data, sample_cols)
            
            # Run clustering heatmap
            results['heatmap'] = self._run_clustering_heatmap(kallisto_data, sample_cols)
            
            # Run abundance distributions
            results['distributions'] = self._run_abundance_distributions(kallisto_data, sample_cols)
            
            logger.info("Kallisto analyses completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in Kallisto analysis: {str(e)}")
            return {'error': str(e)}
    
    def _run_pca(self, kallisto_data, sample_cols):
        """Run PCA on Kallisto data"""
        try:
            logger.info("Performing PCA on Kallisto data")
            
            # Import the PCA function
            from ..kallisto import perform_pca
            
            # Run PCA
            pca_output = self.output_dir / 'pca_plot.png'
            perform_pca(
                kallisto_data[sample_cols],
                sample_cols,
                output_file=str(pca_output)
            )
            
            return {'pca_plot': str(pca_output)}
            
        except Exception as e:
            logger.error(f"Error in PCA: {str(e)}")
            return {'error': str(e)}
    
    def _run_clustering_heatmap(self, kallisto_data, sample_cols):
        """Run clustering heatmap on Kallisto data"""
        try:
            logger.info("Creating sample correlation heatmap")
            
            # Import the heatmap function
            from ..kallisto import plot_clustering_heatmap
            
            # Run heatmap
            heatmap_output = self.output_dir / 'sample_correlation_heatmap.png'
            plot_clustering_heatmap(
                kallisto_data[sample_cols],
                output_file=str(heatmap_output)
            )
            
            return {'heatmap_plot': str(heatmap_output)}
            
        except Exception as e:
            logger.error(f"Error in clustering heatmap: {str(e)}")
            return {'error': str(e)}
    
    def _run_abundance_distributions(self, kallisto_data, sample_cols):
        """Run abundance distributions for each sample"""
        distribution_plots = {}
        
        try:
            logger.info("Plotting transcript abundance distributions")
            
            # Import the distribution function
            from ..kallisto import plot_abundance_distribution
            
            # Run for each sample
            for sample in sample_cols:
                sample_output = self.output_dir / f'abundance_distribution_{sample}.png'
                plot_abundance_distribution(
                    kallisto_data[sample_cols],
                    sample,
                    output_file=str(sample_output)
                )
                distribution_plots[sample] = str(sample_output)
            
            return {'distribution_plots': distribution_plots}
            
        except Exception as e:
            logger.error(f"Error in abundance distributions: {str(e)}")
            return {'error': str(e)} 