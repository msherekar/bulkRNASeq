configfile: "config/snakemake_config.yaml"

# Read samples from `config/samples.txt`
samples = []
try:
    with open("config/samples.txt") as f:
        samples = [line.strip() for line in f if line.strip()]
    print(f"🔍 Detected samples: {samples}")
except FileNotFoundError:
    print("⚠️ Warning: config/samples.txt not found")

# Define a variable for samples to use globally
SAMPLES = samples if samples else []

# Only proceed if there are samples to process
if not SAMPLES:
    print("⚠️ No samples found in config/samples.txt")
    # Don't use exit() in Snakemake as it causes syntax issues
    # Instead, use an empty list for expansion to prevent rules from running
    SAMPLES = ["NO_SAMPLES_FOUND"]


# Define the target rule
rule all:
    input:
        # Final reports
        expand(config["reports"]["final_report"], sample=SAMPLES),
        # QC outputs
        expand(config["output"]["qc_dir"] + "/{sample}_fastqc.html", sample=SAMPLES),
        # MultiQC report
        config["output"]["pre_results_dir"] + "/multiqc_report.html"



# Rule to run the complete bulk RNA-Seq pipeline
rule run_bulkRNASeq:
    input:
        fastq = config["input"]["fastq_dir"] + "/{sample}.fq.gz"
    output:
        report = config["reports"]["final_report"]
    params:
        mode = "pre_post",
        config_file = "config/snakemake_config.yaml",
        results_dir = config["output"]["pre_results_dir"],
        post_results_dir = config["output"]["post_results_dir"]
    log:
        config["output"]["logs"] + "/{sample}_bulkrnaseq.log"
    threads: 
        config["parameters"]["threads"]
    resources:
        mem_mb = lambda wildcards, attempt: attempt * int(config["parameters"]["memory"].rstrip("G")) * 1024
    shell:
        """
        mkdir -p {params.results_dir} {params.post_results_dir} $(dirname {log})
        (set -x; bulkrnaseq \
            --mode {params.mode} \
            --config {params.config_file} \
            --sample {wildcards.sample} \
            --output {output.report} \
            --threads {threads}) 2>&1 | tee {log}
        """


# Quality control rule
rule fastqc:
    input:
        fastq = config["input"]["fastq_dir"] + "/{sample}.fq.gz"
    output:
        html = config["output"]["qc_dir"] + "/{sample}_fastqc.html",
        zip = config["output"]["qc_dir"] + "/{sample}_fastqc.zip"
    params:
        outdir = config["output"]["qc_dir"]
    threads:
        config["fastqc"]["threads"]
    log:
        config["output"]["logs"] + "/fastqc/{sample}.log"
    shell:
        """
        mkdir -p {params.outdir} $(dirname {log})
        fastqc --threads {threads} --outdir {params.outdir} {input.fastq} 2>&1 | tee {log}
        """


# Alignment with selected aligner
rule align:
    input:
        fastq = config["input"]["fastq_dir"] + "/{sample}.fq.gz"
    output:
        # This is a placeholder; actual output will depend on the chosen aligner
        bam = config["output"]["aligned_dir"] + "/{sample}.bam" if config["parameters"]["aligner"] == "hisat2" else [],
        kallisto_dir = directory(config["output"]["pre_results_dir"] + "/{sample}_kallisto") if config["parameters"]["aligner"] == "kallisto" else []
    params:
        aligner = config["parameters"]["aligner"],
        index_hisat2 = config["aligners"]["hisat2"]["index_prefix"],
        index_kallisto = config["aligners"]["kallisto"]["index"],
        fragment_length = config["aligners"]["kallisto"]["fragment_length"],
        fragment_sd = config["aligners"]["kallisto"]["fragment_sd"],
        bootstrap = config["aligners"]["kallisto"]["bootstrap"]
    threads:
        config["aligners"][config["parameters"]["aligner"]]["threads"]
    log:
        config["output"]["logs"] + "/align/{sample}.log"
    run:
        import os
        os.makedirs(os.path.dirname(log[0]), exist_ok=True)
        
        if params.aligner == "hisat2":
            shell("""
                mkdir -p $(dirname {output.bam})
                hisat2 -p {threads} -x {params.index_hisat2} -U {input.fastq} | \
                samtools view -bS - | samtools sort -o {output.bam} - 2>&1 | tee {log}
                samtools index {output.bam}
            """)
        elif params.aligner == "kallisto":
            shell("""
                mkdir -p {output.kallisto_dir}
                kallisto quant \
                    -i {params.index_kallisto} \
                    -o {output.kallisto_dir} \
                    --single -l {params.fragment_length} -s {params.fragment_sd} \
                    -b {params.bootstrap} \
                    -t {threads} \
                    {input.fastq} 2>&1 | tee {log}
            """)


# Generate MultiQC report
rule multiqc:
    input:
        fastqc_zips = expand(config["output"]["qc_dir"] + "/{sample}_fastqc.zip", sample=SAMPLES),
        # Add other inputs as needed based on enabled analyses
    output:
        report = config["output"]["pre_results_dir"] + "/multiqc_report.html"
    params:
        indir = config["output"]["pre_results_dir"],
        outdir = config["output"]["pre_results_dir"]
    log:
        config["output"]["logs"] + "/multiqc/multiqc.log"
    shell:
        """
        mkdir -p $(dirname {log})
        multiqc {params.indir} -o {params.outdir} -n $(basename {output.report}) 2>&1 | tee {log}
        """