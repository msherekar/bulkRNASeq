#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def perform_pca(expression_df, sample_cols, output_file="PCA_plot.png"):
    """
    Perform PCA on log-transformed expression data and save a scatter plot.
    
    Parameters:
        expression_df (pd.DataFrame): Expression data (TPM values) for each sample.
        sample_cols (list): List of sample column names.
        output_file (str): Filename for the PCA plot.
    """
    # Log2 transform the data (adding 1 to avoid log(0))
    log_expr = np.log2(expression_df + 1)
    
    # Standardize the data (transpose so that samples are rows)
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(log_expr.T)
    
    # Perform PCA
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(scaled_data)
    pca_df = pd.DataFrame(pca_result, columns=["PC1", "PC2"], index=sample_cols)
    
    # Plot PCA results
    plt.figure(figsize=(8,6))
    sns.scatterplot(x="PC1", y="PC2", data=pca_df, s=100)
    for sample in pca_df.index:
        plt.text(pca_df.loc[sample, "PC1"] + 0.1, pca_df.loc[sample, "PC2"] + 0.1, sample)
    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)")
    plt.title("PCA of Kallisto Transcript Abundance")
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def plot_clustering_heatmap(expression_df, output_file="clustering_heatmap.png"):
    """
    Plot a hierarchical clustering heatmap of sample correlation from log-transformed data.
    
    Parameters:
        expression_df (pd.DataFrame): Expression data (TPM values).
        output_file (str): Filename for the heatmap plot.
    """
    # Log2 transform the data
    log_expr = np.log2(expression_df + 1)
    # Compute the correlation matrix of samples
    corr_matrix = log_expr.corr()
    
    # Create a clustered heatmap
    cg = sns.clustermap(corr_matrix, annot=True, cmap="viridis", figsize=(8,6))
    plt.title("Hierarchical Clustering of Sample Correlations", pad=100)
    plt.savefig(output_file)
    plt.close()

def plot_abundance_distribution(expression_df, sample, output_file):
    """
    Plot the distribution (histogram and KDE) of log-transformed transcript abundances for one sample.
    
    Parameters:
        expression_df (pd.DataFrame): Expression data (TPM values).
        sample (str): The sample column name to plot.
        output_file (str): Filename for the distribution plot.
    """
    # Log2 transform the sample's expression values
    log_expr_sample = np.log2(expression_df[sample] + 1)
    
    plt.figure(figsize=(8,6))
    sns.histplot(log_expr_sample, kde=True, bins=50)
    plt.title(f"Transcript Abundance Distribution for {sample}")
    plt.xlabel("log2(TPM+1)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def main():
    # Load kallisto abundance data.
    # Assumes file "kallisto_abundance.tsv" with columns: transcript_id, gene_id, sample1, sample2, ...
    data = pd.read_csv("/Users/mukulsherekar/pythonProject/DEGCNN/kallisto_files/fastq_files_kallisto/abundance.tsv")
    # Assume the first two columns are metadata; the rest are sample TPM values.
    sample_cols = data.columns[2:]
    expression_data = data[sample_cols]
    
    # Perform PCA and save the plot.
    perform_pca(expression_data, sample_cols, output_file="PCA_plot.png")
    
    # Plot hierarchical clustering heatmap of sample correlations.
    plot_clustering_heatmap(expression_data, output_file="clustering_heatmap.png")
    
    # For each sample, plot transcript abundance distribution.
    for sample in sample_cols:
        plot_abundance_distribution(expression_data, sample, output_file=f"abundance_distribution_{sample}.png")

if __name__ == "__main__":
    main()