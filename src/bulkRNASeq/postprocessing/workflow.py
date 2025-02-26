#!/usr/bin/env python3

import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time

logger = logging.getLogger(__name__)

def run_exploratory_analysis(counts_file, output_dir, params):
    """
    Run exploratory data analysis on RNA-seq counts.
    """
    try:
        logger.info("Running exploratory data analysis...")
        
        # Load feature counts
        logger.info(f"Loading feature count file: {counts_file}")
        df = load_counts(counts_file)
        logger.info("Feature count file loaded successfully.")
        
        # Generate summary results file
        generate_summary_file(df, counts_file, output_dir, params)
        
        # Plot expression distribution
        if params.get('distribution', True):
            logger.info("Plotting expression distribution...")
            plot_distribution(df, output_dir)
        
        # Get top genes
        top_n = params.get('top_genes', 10)
        logger.info(f"Finding top {top_n} expressed genes...")
        top_genes = get_top_genes(df, top_n)
        top_genes_file = os.path.join(output_dir, 'top_genes.tsv')
        top_genes.to_csv(top_genes_file, sep='\t', index=False)
        
        # Plot top genes
        logger.info(f"Plotting top {top_n} expressed genes...")
        plot_top_genes(df, top_n, output_dir)
        
        return True
    
    except Exception as e:
        logger.error(f"Error in EDA: {str(e)}")
        return False

def generate_summary_file(df, input_file, output_dir, params):
    """
    Generate a comprehensive summary results file.
    """
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
    top_genes = get_top_genes(df, top_n)
    
    # Create the results file
    results_path = os.path.join(output_dir, 'postprocessing_results.txt')
    with open(results_path, 'w') as f:
        f.write("===== Postprocessing Results =====\n\n")
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

def load_counts(file_path):
    """
    Load and format feature counts file.
    """
    df = pd.read_csv(file_path, sep='\t', comment='#')
    
    # The last column contains the actual counts
    sample_col = df.columns[-1]
    
    # Create a new column 'raw_counts' from the sample column
    df['raw_counts'] = df[sample_col].copy().astype(int)
    
    return df

def plot_distribution(df, output_dir):
    """
    Plot distribution of gene expression.
    """
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
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'expression_distribution.png'))
    plt.close()

def get_top_genes(df, n=10):
    """
    Get top expressed genes.
    """
    return df.sort_values('raw_counts', ascending=False).head(n)

def plot_top_genes(df, n=10, output_dir='.'):
    """
    Plot top expressed genes.
    """
    top_genes = get_top_genes(df, n)
    
    plt.figure(figsize=(12, 6))
    plt.bar(top_genes['Geneid'], top_genes['raw_counts'])
    plt.title(f'Top {n} Highly Expressed Genes')
    plt.xlabel('Gene ID')
    plt.ylabel('Raw Counts')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save figure
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'top_genes.png'))
    plt.close()