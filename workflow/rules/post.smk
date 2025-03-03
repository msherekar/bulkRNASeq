rule combine_counts:
    input:
        expand(config["directories"]["results"] + "/counts/{sample}_counts.tsv",
               sample=get_samples())
    output:
        config["directories"]["results"] + "/counts/combined_counts.tsv"
    run:
        import pandas as pd
        
        # Read and combine count files
        dfs = []
        for f in input:
            sample = f.split("/")[-1].replace("_counts.tsv", "")
            # Read the counts file, skipping the first row
            df = pd.read_csv(f, sep="\t", skiprows=1)
            # Print column names for debugging
            print(f"Columns in {f}: {df.columns.tolist()}")
            
            # The actual count column might be the last column
            count_col = df.columns[-1]  # Get the last column name
            df = df[["Geneid", count_col]]  # Select Geneid and count column
            df.columns = ["Geneid", "counts"]  # Rename the count column to 'counts'
            dfs.append(df)
        
        # Merge all dataframes
        final_df = dfs[0]
        for df in dfs[1:]:
            final_df = final_df.merge(df, on="Geneid")
        
        # Save combined counts
        final_df.to_csv(output[0], sep="\t", index=False)

rule postprocessing:
    input:
        counts=config["directories"]["results"] + "/combined_counts.tsv",
        kallisto=expand(config["directories"]["results"] + "/kallisto/{sample}/abundance.h5",
                       sample=get_samples())
    output:
        report=config["directories"]["results"] + "/final_report.md"
    params:
        kallisto_dir=config["directories"]["results"] + "/kallisto",
        output_dir=config["directories"]["results"],
        top_genes=config["analysis"]["top_genes"],
        enrichment_gene_sets=config["analysis"]["enrichment"]["gene_sets"],
        enrichment_pvalue=config["analysis"]["enrichment"]["p_value_cutoff"],
        min_counts=config["analysis"]["clustering"]["min_counts"]
    script:
        "../scripts/run_postprocessing.py"