rule feature_counts:
    input:
        bam=config["directories"]["results"] + "/aligned/{sample}.bam",
        gtf=lambda wildcards: config["genome"]["gtf"]
    output:
        counts=config["directories"]["results"] + "/counts/{sample}_counts.tsv",
        summary=config["directories"]["results"] + "/counts/{sample}_counts.tsv.summary"
    log:
        config["directories"]["logs"] + "/featurecounts/{sample}.log"
    params:
        strand=config["featurecounts"]["strand"]
   

    threads: 
        config["featurecounts"]["threads"]
    shell:
        """
        featureCounts \
            -T {threads} \
            -s {params.strand} \
            -a {input.gtf} \
            -o {output.counts} \
            {input.bam} \
            2> {log}
        """