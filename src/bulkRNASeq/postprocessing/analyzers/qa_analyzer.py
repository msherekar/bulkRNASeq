#!/usr/bin/env python3

import os
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class QAAnalyzer:
    """Quality assessment for RNA-seq data"""
    
    def __init__(self, output_dir):
        """
        Initialize QA analyzer
        
        Args:
            output_dir (str): Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_analysis(self, counts_df, params=None):
        """
        Run quality assessment on RNA-seq counts
        
        Args:
            counts_df (DataFrame): Counts data
            params (dict): Analysis parameters
            
        Returns:
            dict: QA statistics
        """
        params = params or {}
        try:
            logger.info("Generating quality metrics...")
            
            gene_threshold = params.get('gene_threshold', 10)
            expected_library_size = params.get('expected_library_size', 0)
            
            # Generate statistics
            stats = self._generate_stats(
                counts_df,
                threshold=gene_threshold,
                expected_library_size=expected_library_size
            )
            
            # Save to file
            stats_file = self.output_dir / 'quality_stats.txt'
            self._write_stats_report(stats, stats_file)
            
            return {
                'qa_stats': stats,
                'stats_file': str(stats_file)
            }
            
        except Exception as e:
            logger.error(f"Error in QA analysis: {str(e)}")
            return {'error': str(e)}
    
    def _generate_stats(self, df, threshold=10, expected_library_size=0):
        """Generate quality statistics from count data"""
        stats = {}
        
        # Total genes and reads
        stats['total_genes'] = len(df)
        stats['total_reads'] = df['raw_counts'].sum()
        
        # Gene detection metrics
        stats['detected_genes'] = sum(df['raw_counts'] > 0)
        stats['detected_percent'] = stats['detected_genes'] / stats['total_genes'] * 100
        
        # Genes above threshold
        stats['genes_above_threshold'] = sum(df['raw_counts'] >= threshold)
        stats['above_threshold_percent'] = stats['genes_above_threshold'] / stats['total_genes'] * 100
        
        # Library size metrics
        stats['library_size'] = stats['total_reads']
        if expected_library_size > 0:
            stats['library_size_percent'] = stats['library_size'] / expected_library_size * 100
        
        # Expression distribution
        stats['mean_expression'] = df['raw_counts'].mean()
        stats['median_expression'] = df['raw_counts'].median()
        stats['max_expression'] = df['raw_counts'].max()
        
        return stats
    
    def _write_stats_report(self, stats, output_file):
        """Write quality statistics to file"""
        with open(output_file, 'w') as f:
            f.write("===== RNA-Seq Quality Assessment =====\n\n")
            
            f.write("--- Gene Detection ---\n")
            f.write(f"Total Genes: {stats['total_genes']:,}\n")
            f.write(f"Detected Genes: {stats['detected_genes']:,} ({stats['detected_percent']:.2f}%)\n")
            f.write(f"Genes Above Threshold: {stats['genes_above_threshold']:,} ({stats['above_threshold_percent']:.2f}%)\n\n")
            
            f.write("--- Library Metrics ---\n")
            f.write(f"Total Reads: {stats['total_reads']:,}\n")
            if 'library_size_percent' in stats:
                f.write(f"Percent of Expected Library Size: {stats['library_size_percent']:.2f}%\n\n")
            
            f.write("--- Expression Statistics ---\n")
            f.write(f"Mean Expression: {stats['mean_expression']:.2f}\n")
            f.write(f"Median Expression: {stats['median_expression']:.0f}\n")
            f.write(f"Maximum Expression: {stats['max_expression']:,}\n") 