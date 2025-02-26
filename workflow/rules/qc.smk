rule fastqc:
    input:
        fastq=config["directories"]["raw_data"] + "/{sample}.fq.gz"
    output:
        html=config["directories"]["results"] + "/qc/{sample}_fastqc.html",
        zip=config["directories"]["results"] + "/qc/{sample}_fastqc.zip"
    log:
        config["directories"]["logs"] + "/fastqc/{sample}.log"
    params:
        outdir=config["directories"]["results"] + "/qc"
    conda:
        "../envs/qc.yaml"
    threads: 
        config["fastqc"]["threads"]
    shell:
        "fastqc --threads {threads} {input.fastq} --outdir {params.outdir} 2> {log}"
