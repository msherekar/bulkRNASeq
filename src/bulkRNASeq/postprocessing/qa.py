#!/usr/bin/env python3

import numpy as np
import pandas as pd
import os
from pathlib import Path

def gene_detection(df, threshold=10):
    """
    Count genes detected above threshold.
    """
    detected = sum(df['raw_counts'] >= threshold)
    total = len(df)
    percentage = (detected / total) * 100 if total > 0 else 0
    
    return {
        "detected_genes": detected,
        "total_genes": total,
        "detection_percentage": percentage
    }

def mapping_efficiency(df, expected_library_size):
    """
    Calculate mapping efficiency if expected library size is provided.
    """
    total_mapped_reads = df['raw_counts'].sum()
    
    if expected_library_size > 0:
        efficiency = (total_mapped_reads / expected_library_size) * 100
    else:
        efficiency = None
        
    return {
        "total_mapped_reads": total_mapped_reads,
        "mapping_efficiency": efficiency
    }

def generate_stats_report(df, threshold=10, expected_library_size=0, output_file=None):
    """
    Generate a comprehensive statistics report.
    """
    detection_stats = gene_detection(df, threshold)
    mapping_stats = mapping_efficiency(df, expected_library_size)
    
    # Calculate additional statistics
    nonzero_genes = sum(df['raw_counts'] > 0)
    nonzero_percentage = (nonzero_genes / len(df)) * 100 if len(df) > 0 else 0
    
    # Combine all statistics
    stats = {
        **detection_stats,
        **mapping_stats,
        "nonzero_genes": nonzero_genes,
        "nonzero_percentage": nonzero_percentage,
        "mean_counts": df['raw_counts'].mean(),
        "median_counts": df['raw_counts'].median(),
        "max_counts": df['raw_counts'].max()
    }
    
    # Write to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            for key, value in stats.items():
                if isinstance(value, float):
                    f.write(f"{key}: {value:.2f}\n")
                else:
                    f.write(f"{key}: {value}\n")
    
    return stats
