configfile: "config/snakemake_config.yaml"

# Read samples from `config/samples.txt`
with open("config/samples.txt") as f:
    SAMPLES = [line.strip() for line in f if line.strip()]

# Debug print to verify the samples list
print(f"🔍 Detected samples: {SAMPLES}")

# Only proceed if there are samples to process
if not SAMPLES:
    print("⚠️ No samples found in config/samples.txt")
    exit(0)

rule all:
    input:
        expand("tests/data/results/{sample}_final_report.md", sample=SAMPLES)


rule run_bulkRNASeq:
    input:
        "tests/data/raw_fastq/{sample}.fq.gz"
    output:
        "tests/data/results/{sample}_final_report.md"
    params:
        mode="pre_post",
        config="config/combined_config.yaml"
    log:
        "logs/{sample}_bulkrnaseq.log"
    shell:
        """
        (set -x; bulkrnaseq --mode {params.mode} --config {params.config} --sample {wildcards.sample} --output {output}) 2>&1 | tee {log}
        """