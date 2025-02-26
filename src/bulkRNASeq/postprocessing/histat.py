import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
# TODO: imporve plotting of expression distribution

def load_feature_counts(file_path: str) -> pd.DataFrame:
    """
    Load the feature count file and rename the raw count column for clarity.
    """
    df = pd.read_csv(file_path, sep="\t")
    raw_count_col = "output/pranay_hisat2_sorted.bam"
    df = df.rename(columns={raw_count_col: "raw_counts"})
    return df

def plot_expression_distribution(df: pd.DataFrame, output_folder: str = "output", output_filename: str = "expression_distribution.png"):
    """
    Plot the distribution of gene expression counts as a histogram with a density curve.
    The plot will be saved to the specified output folder.
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, output_filename)
    
    plt.figure(figsize=(10, 6))
    sns.histplot(df["raw_counts"], kde=True, bins=50)
    plt.xlabel("Raw Counts")
    plt.ylabel("Frequency")
    plt.title("Distribution of Gene Expression")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.show()

def get_top_genes(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Return the top N highly expressed genes sorted by their raw count.
    """
    return df.sort_values(by="raw_counts", ascending=False).head(top_n)

def plot_scatter_matrix(df: pd.DataFrame, sample_columns: list, output_folder: str = "output", output_filename: str = "scatter_matrix.png"):
    """
    Create and save a scatterplot matrix for the provided sample columns.
    Intended for comparing multiple samples.
    """
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, output_filename)
    
    pairplot = sns.pairplot(df[sample_columns])
    pairplot.fig.suptitle("Scatterplot Matrix for Gene Expression Across Samples", y=1.02)
    pairplot.savefig(output_path)
    plt.show()
