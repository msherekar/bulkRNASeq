from pathlib import Path
import os
import glob
import logging

# Load configuration
configfile: "config/snakemake_config.yaml"

# Function to get sample names from fastq files
def get_samples():
    fastq_files = glob.glob(os.path.join(config["directories"]["raw_data"], "*.fq.gz"))
    sample_names = [os.path.basename(f).replace(".fq.gz", "") for f in fastq_files]
    if not sample_names:
        logging.warning("No sample files found in the specified directory.")
    logging.info(f"Detected samples: {sample_names}")
    return sample_names

# Create output directories
for dir_name in config["directories"].values():
    Path(dir_name).mkdir(parents=True, exist_ok=True)

# Create additional required directories
required_dirs = [
    os.path.join(config["directories"]["results"], "qc"),
    os.path.join(config["directories"]["results"], "aligned"),
    os.path.join(config["directories"]["results"], "kallisto"),
    os.path.join(config["directories"]["results"], "counts"),
    os.path.join(config["directories"]["logs"], "fastqc"),
    os.path.join(config["directories"]["logs"], "hisat2"),
    os.path.join(config["directories"]["logs"], "kallisto"),
    os.path.join(config["directories"]["logs"], "featurecounts")
]

for dir_path in required_dirs:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# Rule to run the bulkRNASeq pipeline
rule run_bulkRNASeq:
    input:
        expand("tests/data/raw_fastq/{sample}.fq.gz", sample=get_samples())
    output:
        "tests/data/results/{sample}_final_report.md"  # Use sample name for the report
    params:
        mode="pre_post",  # or "preprocessing" or "postprocessing" as needed
        config="config/combined_config.yaml"  # Path to your config file
    shell:
        """
        bulkrnaseq --mode {params.mode} --config {params.config}
        """

# Target rule that generates everything
rule all:
    input:
        expand("tests/data/results/{sample}_final_report.md", sample=get_samples())  # Ensure this returns concrete names
