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
if not SAMPLES:
    print("⚠️ No samples found in config/samples.txt")
    SAMPLES = ["NO_SAMPLES_FOUND"]

rule all:
    input:
        # Final reports (one per sample)
        expand(config["reports"]["final_report"], sample=SAMPLES),
        # FastQC HTML reports per sample
        expand(config["output"]["qc_dir"] + "/{sample}_fastqc.html", sample=SAMPLES),
        # MultiQC reports (one per sample)
        expand(config["output"]["pre_results_dir"] + "/{sample}_multiqc_report.html", sample=SAMPLES)

rule run_bulkRNASeq:
    input:
        fastq = config["input"]["fastq_dir"] + "/{sample}.fq.gz"
    output:
        report = config["reports"]["final_report"]
    params:
        mode = "postprocessing",
        config_file = "config/snakemake_config.yaml",
        results_dir = config["output"]["pre_results_dir"],
        post_results_dir = config["output"]["post_results_dir"]
    log:
        config["output"]["logs"] + "/{sample}_bulkrnaseq.log"
    resources:
        mem_mb = lambda wildcards, attempt: attempt * int(config["parameters"]["memory"].rstrip("G")) * 1024
    shell:
        """
        mkdir -p {params.results_dir} {params.post_results_dir} $(dirname {log})
        (set -x; bulkrnaseq \
            --mode {params.mode} \
            --config {params.config_file} \
            --sample {wildcards.sample} \
            --output {output.report}) 2>&1 | tee {log}
        """


rule fastqc:
    input:
        fastq = config["input"]["fastq_dir"] + "/{sample}.fq.gz"
    output:
        html = config["output"]["qc_dir"] + "/{sample}_fastqc.html",
        zip = config["output"]["qc_dir"] + "/{sample}_fastqc.zip"
    params:
        outdir = config["output"]["qc_dir"]
    threads: config["fastqc"]["threads"]
    log:
        config["output"]["logs"] + "/fastqc/{sample}.log"
    shell:
        """
        mkdir -p {params.outdir} $(dirname {log})
        fastqc --threads {threads} --outdir {params.outdir} {input.fastq} 2>&1 | tee {log}
        """

rule align:
    input:
        fastq = config["input"]["fastq_dir"] + "/{sample}.fq.gz"
    output:
        bam = config["output"]["aligned_dir"] + "/{sample}.bam" if config["parameters"]["aligner"] == "hisat2" else [],
        kallisto_dir = directory(config["output"]["pre_results_dir"] + "/{sample}_kallisto") if config["parameters"]["aligner"] == "kallisto" else []
    params:
        aligner = config["parameters"]["aligner"],
        index_hisat2 = config["aligners"]["hisat2"]["index_prefix"],
        index_kallisto = config["aligners"]["kallisto"]["index"],
        fragment_length = config["aligners"]["kallisto"]["fragment_length"],
        fragment_sd = config["aligners"]["kallisto"]["fragment_sd"],
        bootstrap = config["aligners"]["kallisto"]["bootstrap"]
    threads: config["aligners"][config["parameters"]["aligner"]]["threads"]
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

rule multiqc:
    input:
        fastqc_zip = config["output"]["qc_dir"] + "/{sample}_fastqc.zip"
    output:
        report = config["output"]["pre_results_dir"] + "/{sample}_multiqc_report.html"
    log:
        config["output"]["logs"] + "/multiqc/{sample}.log"
    shell:
        """
        mkdir -p $(dirname {log})
        multiqc {input.fastqc_zip} -o $(dirname {output.report}) -n $(basename {output.report}) 2>&1 | tee {log}
        """