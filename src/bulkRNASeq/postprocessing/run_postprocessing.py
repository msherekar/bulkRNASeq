# This code will respont to postprocessing argument in the main.py file
# It will run the postprocessing pipeline step by step
# (eda->differential gene expression->enrichment) analysis  

# It will also save the results in the results/postprocessing directory
# It will also save the logs in the logs/postprocessing directory
# It will also save the reports in the reports/postprocessing directory

import argparse, logging, os, sys, json
#from bulkRNASeq.postprocessing.eda import run_eda
from bulkRNASeq.postprocessing.kallisto import perform_pca, plot_clustering_heatmap, plot_abundance_distribution
from bulkRNASeq.postprocessing.diffexp import run_deseq2
from bulkRNASeq.postprocessing.enrichment import perform_go_enrichment, perform_network_analysis

from bulkRNASeq.utils.check import check_config, check_postprocessing_directories

def run_postprocessing(config):
    """
    Run the postprocessing pipeline step by step
    Args:
        config: Path to the config file
    Returns:
        Postprocessing pipeline results in the results/postprocessing directory
        Postprocessing pipeline logs in the logs/postprocessing directory
        Postprocessing pipeline reports in the reports/postprocessing directory
    """
    # Load the config file
    with open(config, 'r') as f:
        config = json.load(f)   

    # Do the basic checks on config file
    check_config(config)

    # Create the directories if they don't exist
    check_postprocessing_directories(config)

    # Run basic exploratory data analysis
    # TODO: add the eda step

    # Run Kallisto related postprocessing steps
    perform_pca(config['input']['kallisto_dir'], config['output']['pca_dir'])
    plot_clustering_heatmap(config['input']['kallisto_dir'], config['output']['clustering_heatmap_dir'])
    plot_abundance_distribution(config['input']['kallisto_dir'], config['output']['abundance_distribution_dir'])

    # Run differential gene expression analysis
    run_deseq2(config['input']['kallisto_dir'], config['output']['deseq2_dir'])

    # Run enrichment analysis
    perform_go_enrichment(config['input']['kallisto_dir'], config['output']['enrichment_dir'])
    perform_network_analysis(config['input']['kallisto_dir'], config['output']['network_dir'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the postprocessing pipeline")
    parser.add_argument("--config", type=str, required=True, help="Path to the config file")
    args = parser.parse_args()
    run_postprocessing(args.config)


    
    



    # Run the postprocessing pipeline step by step






