#!/usr/bin/env python3

import os
import logging
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd

# Import local modules
try:
    from .workflow import run_exploratory_analysis  
    from .qa import gene_detection, mapping_efficiency, generate_stats_report
    from .enrichment import perform_go_enrichment, perform_network_analysis
    from .kallisto import perform_pca, plot_clustering_heatmap, plot_abundance_distribution
except ImportError:
    # Fallback imports for direct module execution
    from bulkRNASeq.postprocessing.workflow import run_exploratory_analysis
    from bulkRNASeq.postprocessing.qa import gene_detection, mapping_efficiency, generate_stats_report
    from bulkRNASeq.postprocessing.enrichment import perform_go_enrichment, perform_network_analysis
    from bulkRNASeq.postprocessing.kallisto import perform_pca, plot_clustering_heatmap, plot_abundance_distribution

logger = logging.getLogger(__name__)

def run_postprocessing_pipeline(config, checkpoint_mgr=None):
    """
    Main function to run the RNA-seq postprocessing pipeline.
    """
    try:
        # Get configuration parameters
        input_counts_file = config['input']['counts_file']
        output_dir = config['output'].get('results_dir', 'results/postprocessing')
        params = config.get('parameters', {})
        visualization = config.get('visualization', {})
        
        # Handle different count file naming patterns
        if not os.path.exists(input_counts_file):
            # Try with _counts.tsv suffix
            base_name = os.path.basename(input_counts_file).replace('_counts.tsv', '').replace('.bam_counts.tsv', '')
            alt_counts_file = os.path.join(os.path.dirname(input_counts_file), f"{base_name}_counts.tsv")
            if os.path.exists(alt_counts_file):
                input_counts_file = alt_counts_file
                logger.info(f"Using alternative counts file: {input_counts_file}")
            else:
                logger.error(f"Input counts file not found: {input_counts_file} or {alt_counts_file}")
                return False
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Run exploratory data analysis
        if not checkpoint_mgr or not checkpoint_mgr.should_skip_step('eda'):
            logger.info("Running exploratory data analysis")
            success = run_exploratory_analysis(input_counts_file, output_dir, params)
            if not success:
                logger.error("Exploratory data analysis failed")
                return False
            if checkpoint_mgr:
                checkpoint_mgr.save_checkpoint('eda', 'completed')
        else:
            logger.info("Skipping exploratory analysis (already completed)")
        
        # Load count data for QA
        df = pd.read_csv(input_counts_file, sep='\t', comment='#')
        sample_col = df.columns[-1]
        df['raw_counts'] = df[sample_col].copy()
        
        # Generate quality metrics
        if not checkpoint_mgr or not checkpoint_mgr.should_skip_step('qa'):
            logger.info("Generating quality metrics")
            gene_threshold = params.get('gene_threshold', 10)
            expected_library_size = params.get('expected_library_size', 0)
            
            qa_stats = generate_stats_report(
                df, 
                threshold=gene_threshold,
                expected_library_size=expected_library_size,
                output_file=os.path.join(output_dir, 'quality_stats.txt')
            )
            
            if checkpoint_mgr:
                checkpoint_mgr.save_checkpoint('qa', 'completed', {'qa_stats': qa_stats})
        else:
            logger.info("Skipping quality metrics (already completed)")
        
        # Check if Kallisto output files are specified
        kallisto_abundance_file = config['input'].get('kallisto_abundance', None)
        
        # Run Kallisto-specific analyses if file is provided
        if kallisto_abundance_file and os.path.exists(kallisto_abundance_file) and \
           (not checkpoint_mgr or not checkpoint_mgr.should_skip_step('kallisto')):
            logger.info(f"Running Kallisto analyses on {kallisto_abundance_file}")
            
            # Load Kallisto data
            try:
                kallisto_data = pd.read_csv(kallisto_abundance_file, sep='\t')
                
                # Identify sample columns (all except metadata columns)
                # This assumes the first two columns are not sample data
                sample_cols = kallisto_data.columns[2:]
                
                if len(sample_cols) > 0:
                    # Create a directory for Kallisto results
                    kallisto_dir = os.path.join(output_dir, 'kallisto_analysis')
                    Path(kallisto_dir).mkdir(parents=True, exist_ok=True)
                    
                    # Run PCA 
                    logger.info("Performing PCA on Kallisto data")
                    pca_params = visualization.get('pca', {})
                    pca_output = os.path.join(kallisto_dir, 'pca_plot.png')
                    perform_pca(
                        kallisto_data[sample_cols], 
                        sample_cols, 
                        output_file=pca_output
                    )
                    
                    # Run clustering heatmap
                    logger.info("Creating sample correlation heatmap")
                    heatmap_output = os.path.join(kallisto_dir, 'sample_correlation_heatmap.png')
                    plot_clustering_heatmap(
                        kallisto_data[sample_cols],
                        output_file=heatmap_output
                    )
                    
                    # Plot abundance distributions for each sample
                    logger.info("Plotting transcript abundance distributions")
                    for sample in sample_cols:
                        sample_output = os.path.join(kallisto_dir, f'abundance_distribution_{sample}.png')
                        plot_abundance_distribution(
                            kallisto_data[sample_cols],
                            sample,
                            output_file=sample_output
                        )
                
                    logger.info("Kallisto analyses completed successfully")
                    if checkpoint_mgr:
                        checkpoint_mgr.save_checkpoint('kallisto', 'completed')
                else:
                    logger.warning("No sample columns found in Kallisto data")
            
            except Exception as e:
                logger.error(f"Error in Kallisto analyses: {str(e)}")
                # Continue with other analyses even if Kallisto analysis fails
        
        # ====== Functional Enrichment Analysis ======
        # Create enrichment directory
        enrichment_dir = os.path.join(output_dir, 'enrichment')
        Path(enrichment_dir).mkdir(parents=True, exist_ok=True)
        
        # Functional enrichment if requested
        if params.get('go_enrichment', False) and \
           (not checkpoint_mgr or not checkpoint_mgr.should_skip_step('enrichment')):
            logger.info("Performing GO enrichment analysis")
            top_percent = params.get('top_percent', 5)
            top_gene_count = max(10, int(len(df) * top_percent / 100))
            
            # Get top genes and clean them for enrichment
            top_gene_list = df.sort_values('raw_counts', ascending=False).head(top_gene_count)['Geneid'].tolist()
            # Remove version numbers from Ensembl IDs if present (e.g., ENSG00000115414.21 -> ENSG00000115414)
            cleaned_gene_list = [gene.split('.')[0] for gene in top_gene_list]
            
            # Run GO enrichment (returns a DataFrame)
            go_results = perform_go_enrichment(cleaned_gene_list)
            
            # Save results
            if isinstance(go_results, pd.DataFrame):
                # Save the full results as TSV
                go_results.to_csv(os.path.join(enrichment_dir, 'go_enrichment_full.tsv'), sep='\t', index=False)
                
                # Create a summary text file with the top 20 terms
                top_terms = go_results.head(20)
                with open(os.path.join(enrichment_dir, 'go_enrichment_summary.txt'), 'w') as f:
                    f.write("Gene Ontology Enrichment Analysis Results\n")
                    f.write("-----------------------------------------\n")
                    f.write(f"Number of genes analyzed: {len(cleaned_gene_list)}\n\n")
                    f.write("Top enriched GO terms:\n\n")
                    
                    for idx, row in top_terms.iterrows():
                        f.write(f"{idx+1}. {row['Term']} - {row['Adjusted P-value']:.6f}\n")
                        f.write(f"   GO ID: {row['GO_id']}\n")
                        f.write(f"   Genes: {row['Genes']}\n\n")
            else:
                # Handle error case
                with open(os.path.join(enrichment_dir, 'go_enrichment_error.txt'), 'w') as f:
                    f.write(str(go_results))
        
        # Network analysis if requested
        if params.get('network_analysis', False):
            logger.info("Performing STRING network analysis")
            top_percent = params.get('top_percent', 5)
            top_gene_count = max(10, int(len(df) * top_percent / 100))
            
            # Get top genes and clean them for network analysis
            top_gene_list = df.sort_values('raw_counts', ascending=False).head(top_gene_count)['Geneid'].tolist()
            # Remove version numbers from Ensembl IDs if present (e.g., ENSG00000115414.21 -> ENSG00000115414)
            cleaned_gene_list = [gene.split('.')[0] for gene in top_gene_list]
            
            # Run network analysis
            network_results = perform_network_analysis(cleaned_gene_list)
            
            # Save results
            if isinstance(network_results, dict) or isinstance(network_results, list):
                # Save the JSON response
                with open(os.path.join(enrichment_dir, 'string_network.json'), 'w') as f:
                    json.dump(network_results, f, indent=2)
                
                # Create a summary text file
                with open(os.path.join(enrichment_dir, 'string_network_summary.txt'), 'w') as f:
                    f.write("STRING Network Analysis Results\n")
                    f.write("-------------------------------\n")
                    f.write(f"Number of genes submitted: {len(cleaned_gene_list)}\n")
                    
                    if isinstance(network_results, list) and len(network_results) > 0:
                        f.write(f"Number of interactions found: {len(network_results)}\n\n")
                        f.write("Top interactions:\n")
                        
                        for i, interaction in enumerate(network_results[:10]):
                            if i >= 10:
                                break
                            f.write(f"{i+1}. {interaction.get('preferredName_A', interaction.get('stringId_A', 'Unknown'))} - ")
                            f.write(f"{interaction.get('preferredName_B', interaction.get('stringId_B', 'Unknown'))}: ")
                            f.write(f"Score {interaction.get('score', 'Unknown')}\n")
            else:
                # Handle error case
                with open(os.path.join(enrichment_dir, 'string_network_error.txt'), 'w') as f:
                    f.write(str(network_results))
        
        # Generate final comprehensive report
        logger.info("Generating final report")
        final_report_path = os.path.join(output_dir, 'final_report.md')
        
        with open(final_report_path, 'w') as f:
            # Title
            f.write("# RNA-Seq Analysis Final Report\n\n")
            f.write(f"*Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # Input Data Summary
            f.write("## Input Data Summary\n")
            f.write(f"- Input counts file: `{os.path.basename(input_counts_file)}`\n")
            f.write(f"- Total genes analyzed: {len(df):,}\n\n")
            
            # Quality Metrics
            f.write("## Quality Control Metrics\n")
            qa_file = os.path.join(output_dir, 'quality_stats.txt')
            if os.path.exists(qa_file):
                with open(qa_file, 'r') as qa:
                    f.write("```\n" + qa.read() + "\n```\n\n")
            
            # Top Expressed Genes
            f.write("## Top Expressed Genes\n")
            top_genes = df.sort_values('raw_counts', ascending=False).head(15)
            f.write("| Gene ID | Raw Counts |\n|----------|------------|\n")
            for _, row in top_genes.iterrows():
                f.write(f"| {row['Geneid']} | {row['raw_counts']:,} |\n")
            f.write("\n")
            
            # GO Enrichment Results
            f.write("## Gene Ontology Enrichment Analysis\n")
            go_summary = os.path.join(enrichment_dir, 'go_enrichment_summary.txt')
            if os.path.exists(go_summary):
                with open(go_summary, 'r') as go:
                    f.write("```\n" + go.read() + "\n```\n\n")
            
            # Network Analysis Results
            f.write("## STRING Network Analysis\n")
            network_summary = os.path.join(enrichment_dir, 'string_network_summary.txt')
            if os.path.exists(network_summary):
                with open(network_summary, 'r') as net:
                    f.write("```\n" + net.read() + "\n```\n\n")
            
            # Kallisto Results
            if kallisto_abundance_file and os.path.exists(kallisto_abundance_file):
                f.write("## Kallisto Quantification Results\n")
                f.write(f"- Kallisto abundance file: `{os.path.basename(kallisto_abundance_file)}`\n")
                kallisto_dir = os.path.join(output_dir, 'kallisto_analysis')
                if os.path.exists(kallisto_dir):
                    plots = [p for p in os.listdir(kallisto_dir) if p.endswith('.png')]
                    f.write("\nGenerated visualizations:\n")
                    for plot in plots:
                        f.write(f"- `{plot}`\n")
            
            # Generated Files Summary
            f.write("\n## Generated Files Summary\n")
            f.write("### Main Results\n")
            f.write("- `final_report.md`: This comprehensive report\n")
            f.write("- `quality_stats.txt`: Detailed quality control metrics\n")
            f.write("- `go_enrichment_full.tsv`: Complete GO enrichment results\n")
            f.write("- `string_network.json`: Full protein-protein interaction data\n")
            
            f.write("\n### Visualizations\n")
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if file.endswith(('.png', '.pdf')):
                        rel_path = os.path.relpath(os.path.join(root, file), output_dir)
                        f.write(f"- `{rel_path}`: {file.replace('_', ' ').replace('.png', '').replace('.pdf', '')}\n")
        
        logger.info(f"Final report generated at: {final_report_path}")
        logger.info("Postprocessing completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in postprocessing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False 