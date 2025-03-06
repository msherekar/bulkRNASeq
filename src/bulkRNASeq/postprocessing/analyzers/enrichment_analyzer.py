#!/usr/bin/env python3

import os
import logging
import pandas as pd
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class EnrichmentAnalyzer:
    """Functional enrichment analysis for RNA-seq data"""
    
    def __init__(self, output_dir):
        """
        Initialize enrichment analyzer
        
        Args:
            output_dir (str): Directory for output files
        """
        self.output_dir = Path(output_dir) / 'enrichment'
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_analysis(self, counts_df, params=None):
        """
        Run enrichment analysis on RNA-seq counts
        
        Args:
            counts_df (DataFrame): Counts data
            params (dict): Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        params = params or {}
        results = {}
        
        try:
            # Get top genes for enrichment analysis
            top_percent = params.get('top_percent', 5)
            top_gene_count = max(10, int(len(counts_df) * top_percent / 100))
            
            # Extract and clean gene IDs
            top_gene_list = counts_df.sort_values('raw_counts', ascending=False).head(top_gene_count)['Geneid'].tolist()
            cleaned_gene_list = [gene.split('.')[0] for gene in top_gene_list]  # Remove version numbers
            
            # Run GO enrichment if enabled
            if params.get('go_enrichment', False):
                go_results = self._run_go_enrichment(cleaned_gene_list)
                results['go_enrichment'] = go_results
            
            # Run network analysis if enabled
            if params.get('network_analysis', False):
                network_results = self._run_network_analysis(cleaned_gene_list)
                results['network_analysis'] = network_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error in enrichment analysis: {str(e)}")
            return {'error': str(e)}
    
    def _run_go_enrichment(self, gene_list):
        """Run Gene Ontology enrichment analysis"""
        try:
            logger.info(f"Performing GO enrichment analysis on {len(gene_list)} genes")
            
            # Import the actual enrichment function
            from ..enrichment import perform_go_enrichment
            
            # Run GO enrichment (returns a DataFrame)
            go_results = perform_go_enrichment(gene_list)
            
            if not isinstance(go_results, pd.DataFrame):
                logger.warning("GO enrichment did not return a DataFrame")
                return {'error': 'Invalid GO enrichment results'}
            
            # Save full results as TSV
            full_results_file = self.output_dir / 'go_enrichment_full.tsv'
            go_results.to_csv(full_results_file, sep='\t', index=False)
            
            # Create summary text file with top 20 terms
            summary_file = self.output_dir / 'go_enrichment_summary.txt'
            self._write_go_summary(go_results, len(gene_list), summary_file)
            
            return {
                'full_results_file': str(full_results_file),
                'summary_file': str(summary_file),
                'term_count': len(go_results),
                'top_terms': go_results.head(5)['Term'].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in GO enrichment: {str(e)}")
            error_file = self.output_dir / 'go_enrichment_error.txt'
            with open(error_file, 'w') as f:
                f.write(str(e))
            return {'error': str(e), 'error_file': str(error_file)}
    
    def _write_go_summary(self, go_results, gene_count, output_file):
        """Write GO enrichment summary to file"""
        top_terms = go_results.head(20)
        
        with open(output_file, 'w') as f:
            f.write("Gene Ontology Enrichment Analysis Results\n")
            f.write("-----------------------------------------\n")
            f.write(f"Number of genes analyzed: {gene_count}\n\n")
            f.write("Top enriched GO terms:\n\n")
            
            for idx, row in top_terms.iterrows():
                f.write(f"{idx+1}. {row['Term']} - {row['Adjusted P-value']:.6f}\n")
                f.write(f"   GO ID: {row['GO_id']}\n")
                f.write(f"   Genes: {row['Genes']}\n\n")
    
    def _run_network_analysis(self, gene_list):
        """Run STRING network analysis"""
        try:
            logger.info(f"Performing STRING network analysis on {len(gene_list)} genes")
            
            # Import the actual network analysis function
            from ..enrichment import perform_network_analysis
            
            # Run network analysis
            network_results = perform_network_analysis(gene_list)
            
            # Save JSON response
            json_file = self.output_dir / 'string_network.json'
            with open(json_file, 'w') as f:
                json.dump(network_results, f, indent=2)
            
            # Create summary text file
            summary_file = self.output_dir / 'string_network_summary.txt'
            self._write_network_summary(network_results, len(gene_list), summary_file)
            
            return {
                'json_file': str(json_file),
                'summary_file': str(summary_file),
                'interaction_count': len(network_results) if isinstance(network_results, list) else 0
            }
            
        except Exception as e:
            logger.error(f"Error in network analysis: {str(e)}")
            error_file = self.output_dir / 'string_network_error.txt'
            with open(error_file, 'w') as f:
                f.write(str(e))
            return {'error': str(e), 'error_file': str(error_file)}
    
    def _write_network_summary(self, network_results, gene_count, output_file):
        """Write network analysis summary to file"""
        with open(output_file, 'w') as f:
            f.write("STRING Network Analysis Results\n")
            f.write("-------------------------------\n")
            f.write(f"Number of genes submitted: {gene_count}\n")
            
            if isinstance(network_results, list) and len(network_results) > 0:
                f.write(f"Number of interactions found: {len(network_results)}\n\n")
                f.write("Top interactions:\n")
                
                for i, interaction in enumerate(network_results[:10]):
                    if i >= 10:
                        break
                    f.write(f"{i+1}. {interaction.get('preferredName_A', interaction.get('stringId_A', 'Unknown'))} - ")
                    f.write(f"{interaction.get('preferredName_B', interaction.get('stringId_B', 'Unknown'))}: ")
                    f.write(f"Score {interaction.get('score', 'Unknown')}\n") 