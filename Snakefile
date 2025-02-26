from pathlib import Path

# Load configuration
configfile: "config/snakemake_config.yaml"

# Create output directories
for dir_name in config["directories"].values():
    Path(dir_name).mkdir(parents=True, exist_ok=True)

# Include rule files
include: "workflow/rules/qc.smk"
include: "workflow/rules/align.smk"
include: "workflow/rules/counts.smk"
include: "workflow/rules/post.smk"

# Target rule that generates everything
rule all:
    input:
        # QC outputs
        expand("{results}/qc/{sample}_fastqc.html",
            results=config["directories"]["results"],
            sample=config["samples"]),
        # Alignment outputs
        expand("{results}/aligned/{sample}.bam",
            results=config["directories"]["results"],
            sample=config["samples"]),
        # Kallisto outputs
        expand("{results}/kallisto/{sample}/abundance.h5",
            results=config["directories"]["results"],
            sample=config["samples"]),
        # Count outputs
        expand("{results}/counts/{sample}_counts.tsv",
            results=config["directories"]["results"],
            sample=config["samples"]),
        # Final report
        f"{config['directories']['results']}/final_report.md"
