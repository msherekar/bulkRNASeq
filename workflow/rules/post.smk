rule combine_counts:
    input:
        expand("results/counts/{sample}_counts.tsv", sample=config["samples"])
    output:
        "results/combined_counts.tsv"
    run:
        import pandas as pd
        
        # Read and combine count files
        dfs = []
        for f in input:
            sample = f.split("/")[-1].replace("_counts.tsv", "")
            df = pd.read_csv(f, sep="\t", skiprows=1)
            df = df[["Geneid", "Count"]]
            df.columns = ["Geneid", sample]
            dfs.append(df)
        
        # Merge all dataframes
        final_df = dfs[0]
        for df in dfs[1:]:
            final_df = final_df.merge(df, on="Geneid")
        
        # Save combined counts
        final_df.to_csv(output[0], sep="\t", index=False)

rule postprocessing:
    input:
        counts="results/combined_counts.tsv",
        kallisto=expand("results/kallisto/{sample}/abundance.h5", sample=config["samples"])
    output:
        report="results/final_report.md"
    params:
        kallisto_dir="results/kallisto",
        output_dir="results"
    conda:
        "../envs/post.yaml"
    script:
        "../scripts/run_postprocessing.py"
