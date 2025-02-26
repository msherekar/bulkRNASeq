#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_feature_counts(file_path):
    """
    Load and parse a featureCounts output file.
    """
    try:
        # Log what we're doing
        logger.info(f"Loading featureCounts file: {file_path}")
        
        # Load the featureCounts output file
        df = pd.read_csv(file_path, sep='\t', comment='#')
        
        logger.info(f"File loaded with columns: {df.columns.tolist()}")
        
        # FORCE create raw_counts from the last column (sample column)
        # In featureCounts format, the last column contains the counts
        last_col = df.columns[-1]
        df['raw_counts'] = df[last_col].copy()
        
        logger.info(f"Created 'raw_counts' column from '{last_col}' column")
        logger.info(f"Loaded {len(df)} genes")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading count file: {str(e)}")
        raise

def plot_expression_distribution(df, output_folder='.'):
    """
    Generate histogram of gene expression distribution.
    """
    try:
        # Ensure raw_counts column exists
        if 'raw_counts' not in df.columns:
            raise ValueError("'raw_counts' column not found in data frame")
        
        plt.figure(figsize=(10, 6))
        
        # Add pseudocount of 1 and log-transform (for genes with non-zero counts)
        nonzero_counts = df[df['raw_counts'] > 0]['raw_counts']
        if len(nonzero_counts) == 0:
            logger.warning("No genes with non-zero counts found!")
            nonzero_counts = pd.Series([1])  # Add dummy data to avoid plotting error
            
        log_counts = np.log10(nonzero_counts + 1)
        
        # Plot histogram
        sns.histplot(log_counts, kde=True)
        plt.title('Gene Expression Distribution')
        plt.xlabel('log10(counts + 1)')
        plt.ylabel('Number of genes')
        
        # Save figure
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        output_path = os.path.join(output_folder, 'expression_distribution.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    except Exception as e:
        logger.error(f"Error in plot_expression_distribution: {str(e)}")
        raise

def get_top_genes(df, n=10):
    """
    Return the top n highly expressed genes.
    """
    try:
        # Ensure raw_counts column exists
        if 'raw_counts' not in df.columns:
            raise ValueError("'raw_counts' column not found in data frame")
            
        return df.sort_values('raw_counts', ascending=False).head(n)
    except Exception as e:
        logger.error(f"Error in get_top_genes: {str(e)}")
        raise

def plot_top_genes(df, n=10, output_folder='.'):
    """
    Plot bar chart of top expressed genes.
    """
    try:
        # Ensure raw_counts column exists
        if 'raw_counts' not in df.columns:
            raise ValueError("'raw_counts' column not found in data frame")
            
        top_genes = get_top_genes(df, n)
        
        plt.figure(figsize=(12, 6))
        plt.bar(top_genes['Geneid'], top_genes['raw_counts'])
        plt.title(f'Top {n} Highly Expressed Genes')
        plt.xlabel('Gene ID')
        plt.ylabel('Raw Counts')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save figure
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        output_path = os.path.join(output_folder, 'top_genes.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    except Exception as e:
        logger.error(f"Error in plot_top_genes: {str(e)}")
        raise 