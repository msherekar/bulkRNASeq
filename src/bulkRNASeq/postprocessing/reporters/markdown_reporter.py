#!/usr/bin/env python3

import os
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class MarkdownReporter:
    """Generate markdown reports for RNA-seq analysis"""
    
    def __init__(self, output_dir):
        """
        Initialize markdown reporter
        
        Args:
            output_dir (str): Directory for output files
        """
        self.output_dir = Path(output_dir)
    
    def generate_report(self, results, counts_df=None):
        """
        Generate a comprehensive markdown report
        
        Args:
            results (dict): Results from different analysis steps
            counts_df (DataFrame): Original counts data
            
        Returns:
            str: Path to the generated report
        """
        try:
            report_path = self.output_dir / 'final_report.md'
            
            with open(report_path, 'w') as f:
                # Title
                f.write("# RNA-Seq Analysis Final Report\n\n")
                f.write(f"*Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                
                # Input Data Summary
                f.write("## Input Data Summary\n")
                if 'input_file' in results:
                    f.write(f"- Input counts file: `{os.path.basename(results['input_file'])}`\n")
                if counts_df is not None:
                    f.write(f"- Total genes analyzed: {len(counts_df):,}\n")
                f.write("\n")
                
                # Quality Control Metrics
                if 'qa' in results and 'stats_file' in results['qa']:
                    f.write("## Quality Control Metrics\n")
                    qa_file = results['qa']['stats_file']
                    if os.path.exists(qa_file):
                        with open(qa_file, 'r') as qa:
                            f.write("```\n" + qa.read() + "\n```\n\n")
                
                # Top Expressed Genes
                if counts_df is not None:
                    f.write("## Top Expressed Genes\n")
                    top_genes = counts_df.sort_values('raw_counts', ascending=False).head(15)
                    f.write("| Gene ID | Raw Counts |\n|----------|------------|\n")
                    for _, row in top_genes.iterrows():
                        f.write(f"| {row['Geneid']} | {row['raw_counts']:,} |\n")
                    f.write("\n")
                
                # GO Enrichment Results
                if 'enrichment' in results and 'go_enrichment' in results['enrichment']:
                    f.write("## Gene Ontology Enrichment Analysis\n")
                    go_summary = results['enrichment']['go_enrichment'].get('summary_file')
                    if go_summary and os.path.exists(go_summary):
                        with open(go_summary, 'r') as go:
                            f.write("```\n" + go.read() + "\n```\n\n")
                
                # Network Analysis Results
                if 'enrichment' in results and 'network_analysis' in results['enrichment']:
                    f.write("## STRING Network Analysis\n")
                    network_summary = results['enrichment']['network_analysis'].get('summary_file')
                    if network_summary and os.path.exists(network_summary):
                        with open(network_summary, 'r') as net:
                            f.write("```\n" + net.read() + "\n```\n\n")
                
                # Kallisto Results
                if 'kallisto' in results:
                    f.write("## Kallisto Quantification Results\n")
                    if 'input_file' in results['kallisto']:
                        f.write(f"- Kallisto abundance file: `{os.path.basename(results['kallisto']['input_file'])}`\n")
                    
                    # List visualizations
                    plots = []
                    if 'pca' in results['kallisto'] and 'pca_plot' in results['kallisto']['pca']:
                        plots.append(results['kallisto']['pca']['pca_plot'])
                    if 'heatmap' in results['kallisto'] and 'heatmap_plot' in results['kallisto']['heatmap']:
                        plots.append(results['kallisto']['heatmap']['heatmap_plot'])
                    if 'distributions' in results['kallisto'] and 'distribution_plots' in results['kallisto']['distributions']:
                        plots.extend(results['kallisto']['distributions']['distribution_plots'].values())
                    
                    if plots:
                        f.write("\nGenerated visualizations:\n")
                        for plot in plots:
                            f.write(f"- `{os.path.basename(plot)}`\n")
                    f.write("\n")
                
                # Generated Files Summary
                f.write("\n## Generated Files Summary\n")
                f.write("### Main Results\n")
                f.write("- `final_report.md`: This comprehensive report\n")
                
                if 'qa' in results and 'stats_file' in results['qa']:
                    f.write(f"- `{os.path.basename(results['qa']['stats_file'])}`: Detailed quality control metrics\n")
                    
                if 'enrichment' in results:
                    if 'go_enrichment' in results['enrichment'] and 'full_results_file' in results['enrichment']['go_enrichment']:
                        f.write(f"- `{os.path.basename(results['enrichment']['go_enrichment']['full_results_file'])}`: Complete GO enrichment results\n")
                    if 'network_analysis' in results['enrichment'] and 'json_file' in results['enrichment']['network_analysis']:
                        f.write(f"- `{os.path.basename(results['enrichment']['network_analysis']['json_file'])}`: Full protein-protein interaction data\n")
                
                f.write("\n### Visualizations\n")
                for root, _, files in os.walk(self.output_dir):
                    for file in files:
                        if file.endswith(('.png', '.pdf')):
                            rel_path = os.path.relpath(os.path.join(root, file), self.output_dir)
                            f.write(f"- `{rel_path}`: {file.replace('_', ' ').replace('.png', '').replace('.pdf', '')}\n")
            
            logger.info(f"Final report generated at: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return None 