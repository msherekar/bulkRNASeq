rule feature_counts:
    input:
        bam="results/aligned_reads/{sample}.bam",
        gtf=lambda wildcards: config["genome"]["gtf_file"]
    output:
        counts="results/counts/{sample}_counts.tsv",
        summary="results/counts/{sample}_counts.tsv.summary"
    log:
        "logs/featurecounts/{sample}.log"
    conda:
        "../envs/counts.yaml"
    threads: 4
    shell:
        """
        featureCounts \
            -T {threads} \
            -a {input.gtf} \
            -o {output.counts} \
            {input.bam} \
            2> {log}
        """
