#!/bin/bash

#SBATCH --job-name=bulkRNA
#SBATCH --output=logs/bulkRNA_%j.out
#SBATCH --error=logs/bulkRNA_%j.err
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=your.email@example.com

# Parameters to pass to the pipeline
MODE="preprocessing"  # preprocessing, postprocessing, or processing
INPUT_DIR="data/raw"
OUTPUT_DIR="results"
GENOME_DIR="ref_genome"
THREADS=8

# Launch the pipeline script
sbatch bulkrnaseq.sh \
    --mode ${MODE} \
    --input ${INPUT_DIR} \
    --output ${OUTPUT_DIR} \
    --genome ${GENOME_DIR} \
    --threads ${THREADS}
