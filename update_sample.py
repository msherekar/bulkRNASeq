import glob
import os

SAMPLE_DIR = "tests/data/raw_fastq"
SAMPLE_LIST_FILE = "config/samples.txt"

def update_sample_list():
    """Update the list of sample names before Snakemake runs."""
    fastq_files = glob.glob(os.path.join(SAMPLE_DIR, "*.fq.gz"))
    sample_names = [os.path.basename(f).replace(".fq.gz", "") for f in fastq_files]

    with open(SAMPLE_LIST_FILE, "w") as f:
        f.write("\n".join(sample_names))

    print(f"Updated sample list: {sample_names}")

if __name__ == "__main__":
    update_sample_list()
