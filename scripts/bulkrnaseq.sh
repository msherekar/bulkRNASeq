#!/bin/bash

# Function to print usage
usage() {
    echo "Usage: $0 --mode <preprocessing|postprocessing|processing> --input <input_dir> --output <output_dir> --genome <genome_dir> --threads <num_threads>"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --mode)
            MODE="$2"
            shift
            shift
            ;;
        --input)
            INPUT_DIR="$2"
            shift
            shift
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift
            shift
            ;;
        --genome)
            GENOME_DIR="$2"
            shift
            shift
            ;;
        --threads)
            THREADS="$2"
            shift
            shift
            ;;
        *)
            usage
            ;;
    esac
done

# Validate required parameters
if [[ -z ${MODE} ]] || [[ -z ${INPUT_DIR} ]] || [[ -z ${OUTPUT_DIR} ]] || [[ -z ${GENOME_DIR} ]] || [[ -z ${THREADS} ]]; then
    usage
fi

# Create output directories if they don't exist
mkdir -p ${OUTPUT_DIR}
mkdir -p logs

# Load modules if needed (uncomment and modify as per your HPC setup)
# module load python/3.12
# module load r/4.4

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate rnaseq

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export NUM_THREADS=${THREADS}

# Run the pipeline
echo "Starting bulk RNA-seq pipeline in ${MODE} mode..."
python -m bulkrnaseq \
    --mode ${MODE} \
    --input-dir ${INPUT_DIR} \
    --output-dir ${OUTPUT_DIR} \
    --genome-dir ${GENOME_DIR} \
    --threads ${THREADS}

# Check exit status
if [ $? -eq 0 ]; then
    echo "Pipeline completed successfully"
    exit 0
else
    echo "Pipeline failed"
    exit 1
fi
