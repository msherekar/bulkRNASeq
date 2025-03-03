rule hisat2_align:
    input:
        fastq=config["directories"]["raw_data"] + "/{sample}.fq.gz",
        index=multiext(config["aligners"]["hisat2"]["index_prefix"],
                      ".1.ht2", ".2.ht2", ".3.ht2", ".4.ht2",
                      ".5.ht2", ".6.ht2", ".7.ht2", ".8.ht2")
    output:
        bam=config["directories"]["results"] + "/aligned/{sample}.bam",
        bai=config["directories"]["results"] + "/aligned/{sample}.bam.bai"
    log:
        config["directories"]["logs"] + "/hisat2/{sample}.log"
    
    threads: 
        config["aligners"]["hisat2"]["threads"]
    params:
        index_prefix=lambda wildcards: config["aligners"]["hisat2"]["index_prefix"]
    shell:
        """
        hisat2 -p {threads} -x {params.index_prefix} -U {input.fastq} 2> {log} | \
        samtools sort -@ {threads} -o {output.bam} - && \
        samtools index {output.bam}
        """

rule kallisto_quant:
    input:
        fastq=config["directories"]["raw_data"] + "/{sample}.fq.gz",
        index=lambda wildcards: config["aligners"]["kallisto"]["index"]
    output:
        directory(config["directories"]["results"] + "/kallisto/{sample}"),
        abundance=config["directories"]["results"] + "/kallisto/{sample}/abundance.h5"
    params:
        fragment_length=lambda wildcards: config["aligners"]["kallisto"].get("fragment_length", 200),
        sd=lambda wildcards: config["aligners"]["kallisto"].get("fragment_sd", 20)
    log:
        config["directories"]["logs"] + "/kallisto/{sample}.log"
    
    threads: 
        config["aligners"]["kallisto"]["threads"]
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
