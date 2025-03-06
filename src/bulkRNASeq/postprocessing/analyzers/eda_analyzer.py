#!/usr/bin/env python3

import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

logger = logging.getLogger(__name__)

class EDAAnalyzer:
    """Exploratory Data Analysis for RNA-seq data"""
    
    def __init__(self, output_dir):
        """
        Initialize EDA analyzer
        
        Args:
            output_dir (str): Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run_analysis(self, counts_file, params=None):
        """
        Run exploratory data analysis on RNA-seq counts
        
        Args:
            counts_file (str): Path to counts file
            params (dict): Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        params = params or {}
        try:
            logger.info("Running exploratory data analysis...")
            
            # Load feature counts
            logger.info(f"Loading feature count file: {counts_file}")
            df = self._load_counts(counts_file)
            logger.info("Feature count file loaded successfully.")
            
            # Generate summary results file
            summary_file = self.output_dir / 'eda_summary.txt'
            self._generate_summary_file(df, counts_file, summary_file, params)
            
            # Plot expression distribution
            if params.get('distribution', True):
                logger.info("Plotting expression distribution...")
                dist_file = self.output_dir / 'expression_distribution.png'
                self._plot_distribution(df, dist_file)
            
            # Get top genes
            top_n = params.get('top_genes', 10)
            logger.info(f"Finding top {top_n} expressed genes...")
            top_genes = self._get_top_genes(df, top_n)
            top_genes_file = self.output_dir / 'top_genes.tsv'
            top_genes.to_csv(top_genes_file, sep='\t', index=False)
            
            # Plot top genes
            logger.info(f"Plotting top {top_n} expressed genes...")
            top_genes_plot = self.output_dir / 'top_genes.png'
            self._plot_top_genes(df, top_n, top_genes_plot)
            
            return {
                'summary_file': str(summary_file),
                'distribution_plot': str(dist_file) if params.get('distribution', True) else None,
                'top_genes_file': str(top_genes_file),
                'top_genes_plot': str(top_genes_plot),
                'gene_count': len(df),
                'expressed_genes': sum(df['raw_counts'] > 0),
                'top_genes': top_genes['Geneid'].tolist()
            }
        
        except Exception as e:
            logger.error(f"Error in EDA: {str(e)}")
            return {'error': str(e)}
    
    def _load_counts(self, file_path):
        """Load and format feature counts file"""
        df = pd.read_csv(file_path, sep='\t', comment='#')
        sample_col = df.columns[-1]
        df['raw_counts'] = df[sample_col].copy().astype(int)
        return df
    
    def _generate_summary_file(self, df, input_file, output_file, params):
        """Generate a comprehensive summary results file"""
        import time
        
        # Calculate statistics
        total_genes = len(df)
        expressed_genes = sum(df['raw_counts'] > 0)
        threshold = params.get('gene_threshold', 10)
        genes_above_threshold = sum(df['raw_counts'] >= threshold)
        total_reads = df['raw_counts'].sum()
        max_expressed_gene = df.loc[df['raw_counts'].idxmax(), 'Geneid']
        max_expression = df['raw_counts'].max()
        
        # Get top expressed genes
        top_n = params.get('top_genes', 10)
        top_genes = self._get_top_genes(df, top_n)
        
        # Create the results file
        with open(output_file, 'w') as f:
            f.write("===== Exploratory Data Analysis Results =====\n\n")
            f.write(f"Analysis Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Input File: {os.path.basename(input_file)}\n\n")
            
            f.write("--- Summary Statistics ---\n")
            f.write(f"Total Genes Analyzed: {total_genes:,}\n")
            f.write(f"Expressed Genes (counts > 0): {expressed_genes:,} ({expressed_genes/total_genes:.2%})\n")
            f.write(f"Genes Above Threshold ({threshold}): {genes_above_threshold:,} ({genes_above_threshold/total_genes:.2%})\n")
            f.write(f"Total Mapped Reads: {total_reads:,}\n")
            f.write(f"Highest Expressed Gene: {max_expressed_gene} ({max_expression:,} counts)\n\n")
            
            f.write("--- Top Expressed Genes ---\n")
            for i, (_, gene) in enumerate(top_genes.iterrows(), 1):
                f.write(f"{i}. {gene['Geneid']}: {gene['raw_counts']:,} counts\n")
            
            f.write("\n--- Analysis Parameters ---\n")
            for param, value in params.items():
                f.write(f"{param}: {value}\n")
    
    def _plot_distribution(self, df, output_file):
        """Plot distribution of gene expression"""
        plt.figure(figsize=(10, 6))
        
        # Log-transform counts for better visualization
        nonzero_counts = df[df['raw_counts'] > 0]['raw_counts']
        log_counts = np.log10(nonzero_counts + 1)
        
        # Plot histogram
        sns.histplot(log_counts, kde=True)
        plt.title('Gene Expression Distribution')
        plt.xlabel('log10(counts + 1)')
        plt.ylabel('Number of genes')
        
        # Save figure
        plt.savefig(output_file)
        plt.close()
    
    def _get_top_genes(self, df, n=10):
        """Get top expressed genes"""
        return df.sort_values('raw_counts', ascending=False).head(n)
    
    def _plot_top_genes(self, df, n=10, output_file=None):
        """Plot top expressed genes"""
        top_genes = self._get_top_genes(df, n)
        
        plt.figure(figsize=(12, 6))
        plt.bar(top_genes['Geneid'], top_genes['raw_counts'])
        plt.title(f'Top {n} Highly Expressed Genes')
        plt.xlabel('Gene ID')
        plt.ylabel('Raw Counts')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save figure
        plt.savefig(output_file)
        plt.close() 