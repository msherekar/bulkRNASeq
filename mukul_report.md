# Analysis Report for mukul

Analysis completed at: 2025-03-06 00:21:39

## Configuration

```yaml
aligners:
  hisat2:
    index_prefix: genome/genome
  kallisto:
    bootstrap: 100
    fragment_length: 200
    fragment_sd: 20
    index: genome/kallisto_index
  salmon:
    index: genome/salmon_index
    library_type: A
    threads: 8
genome:
  genome_fasta: genome/GRCh38.p13.genome.fa
  gtf_file: genome/gencode.v38.annotation.gtf
  transcriptome_fasta: genome/gencode.v47.transcripts.fa.gz
input:
  fastq_dir: tests/data/raw_fastq
  fastq_pattern: '*.fq.gz'
  paired_end: false
output:
  aligned_dir: tests/data/results/preprocessing/aligned_reads
  counts_dir: tests/data/results/preprocessing/counts
  qc_dir: tests/data/results/preprocessing/qc
  results_dir: tests/data/results/preprocessing
parameters:
  adapter_stringency: 0.9
  aligner: hisat2
  memory: 8G
  min_length: 36
  min_quality: 20
  quality_threshold: 20
  restart_from: quantification
  step: all
  stranded: reverse
  threads: 8
pipeline_steps:
- qc
- alignment
- quantification
- multiqc
sample:
  name: mukul
  output_file: mukul_report.md
```
