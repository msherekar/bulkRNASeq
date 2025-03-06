# Analysis Report for mukul

Analysis completed at: 2025-03-06 17:55:31

## Configuration

```yaml
enabled_analyses:
  eda: true
  enrichment: true
  kallisto: true
  qa: true
  report: true
input:
  counts_file: tests/data/results/preprocessing/counts_hisat2/${sample}.bam_counts.tsv
  kallisto_abundance: tests/data/results/preprocessing/${sample}_kallisto/abundance.tsv
  kallisto_h5: tests/data/results/preprocessing/${sample}_kallisto/abundance.h5
output:
  base_dir: tests/data/results/postprocessing
  differential_dir: ${sample_dir}/differential
  eda_dir: ${sample_dir}/exploratory
  enrichment_dir: ${sample_dir}/enrichment
  reports_dir: ${sample_dir}/reports
  sample_dir: ${base_dir}/${sample}
parameters:
  differential:
    log2fc_cutoff: 1.0
    method: DESeq2
    padj_cutoff: 0.05
  eda:
    distribution: true
    expected_library_size: 0
    min_counts: 10
    top_genes: 15
  enrichment:
    go_analysis: true
    kegg_analysis: false
    top_percent: 5
  fail_fast: false
  threads: 8
reports:
  format: markdown
  include_code: false
  include_session_info: true
sample:
  name: mukul
  output_file: mukul_report.md
visualization:
  heatmap:
    cluster_cols: true
    cluster_rows: true
    show_rownames: false
  pca:
    color_by: condition
    components:
    - 1
    - 2
  theme: default
  volcano:
    highlight_genes: []
    log2fc_cutoff: 1.0
    padj_cutoff: 0.05
```
