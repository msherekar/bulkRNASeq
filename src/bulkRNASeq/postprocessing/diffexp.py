import argparse
import logging
import os
import sys

# rpy2 interfaces
from rpy2.robjects import r, pandas2ri, globalenv
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
import pandas as pd

pandas2ri.activate()

def setup_logger(prefix, output_dir):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    log_filename = os.path.join(output_dir, f"{prefix}_deseq2.log")
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    return logger

def run_deseq2(counts_file, design_file, output_dir):
    """
    Runs differential expression analysis using DESeq2 via rpy2.
    
    Parameters:
      counts_file: Path to a tab-delimited counts file (genes as rows, samples as columns). 
                   The first column should be gene identifiers.
      design_file: Path to a tab-delimited design file with at least two columns: sample and condition.
      output_dir: Directory to write DESeq2 results.
      
    DESeq2 performs its own normalization as part of the analysis.
    """
    prefix = os.path.basename(counts_file).split('.')[0]
    logger = setup_logger(prefix, output_dir)
    
    logger.info("Loading counts and design files...")
    try:
        counts = pd.read_csv(counts_file, sep='\t', index_col=0)
        design = pd.read_csv(design_file, sep='\t')
    except Exception as e:
        logger.error("Error loading input files: " + str(e))
        sys.exit(1)
        
    # Ensure the design file contains the required "condition" column.
    if 'condition' not in design.columns:
        logger.error("Design file must contain a 'condition' column.")
        sys.exit(1)
    
    # Transfer data to R environment.
    globalenv['counts'] = pandas2ri.py2rpy(counts)
    globalenv['coldata'] = pandas2ri.py2rpy(design)
    
    logger.info("Running DESeq2 differential expression analysis...")
    
    try:
        # Create the DESeq2 dataset and perform the analysis.
        r('dds <- DESeqDataSetFromMatrix(countData = counts, colData = coldata, design = ~ condition)')
        r('dds <- DESeq(dds)')
        r('res <- results(dds)')
        r('resOrdered <- res[order(res$pvalue),]')
        r('resDF <- as.data.frame(resOrdered)')
    except Exception as e:
        logger.error("Error during DESeq2 analysis: " + str(e))
        sys.exit(1)
    
    # Write out results to a tab-delimited text file.
    output_file = os.path.join(output_dir, f"{prefix}_deseq2_results.txt")
    try:
        r(f'write.table(resDF, file="{output_file}", sep="\t", quote=FALSE, row.names=TRUE)')
    except Exception as e:
        logger.error("Error writing DESeq2 results: " + str(e))
        sys.exit(1)
    
    logger.info("DESeq2 analysis completed successfully.")
    logger.info("Results written to: " + output_file)
    print("DESeq2 analysis completed. Results:", output_file)
