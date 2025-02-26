rule hisat2_align:
    input:
        fastq="raw_fastq/{sample}.fq.gz",
        index=lambda wildcards: config["aligners"]["hisat2"]["index_prefix"]
    output:
        bam="results/aligned_reads/{sample}.bam",
        bai="results/aligned_reads/{sample}.bam.bai"
    log:
        "logs/hisat2/{sample}.log"
    conda:
        "../envs/align.yaml"
    threads: 8
    shell:
        """
        hisat2 -p {threads} -x {input.index} -U {input.fastq} 2> {log} | \
        samtools sort -@ {threads} -o {output.bam} - && \
        samtools index {output.bam}
        """

rule kallisto_quant:
    input:
        fastq="raw_fastq/{sample}.fq.gz",
        index=lambda wildcards: config["aligners"]["kallisto"]["index"]
    output:
        directory("results/kallisto/{sample}"),
        abundance="results/kallisto/{sample}/abundance.h5"
    params:
        fragment_length=lambda wildcards: config["aligners"]["kallisto"].get("fragment_length", 200),
        sd=lambda wildcards: config["aligners"]["kallisto"].get("sd", 20)
    log:
        "logs/kallisto/{sample}.log"
    conda:
        "../envs/align.yaml"
    threads: 4
    shell:
        """
        kallisto quant \
            -i {input.index} \
            -o {output[0]} \
            --single \
            -l {params.fragment_length} \
            -s {params.sd} \
            -t {threads} \
            {input.fastq} \
            2> {log}
        """
