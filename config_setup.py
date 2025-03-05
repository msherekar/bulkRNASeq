# config_setup.py
import yaml
import os
import glob
import logging
from pathlib import Path

# Load configuration
with open("config/snakemake_config.yaml") as f:
    config = yaml.safe_load(f)

# Function to get sample names from fastq files
def get_samples():
    fastq_files = glob.glob(os.path.join(config["directories"]["raw_data"], "*.fq.gz"))
    sample_names = [os.path.basename(f).replace(".fq.gz", "") for f in fastq_files]
    if not sample_names:
        logging.warning("No sample files found in the specified directory.")
    logging.info(f"Detected samples: {sample_names}")
    return sample_names

# Create required directories
for dir_name in config["directories"].values():
    Path(dir_name).mkdir(parents=True, exist_ok=True)

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

# Save detected samples to a file so Snakemake can use it
samples = get_samples()
with open("config/samples.txt", "w") as f:
    f.write("\n".join(samples))
