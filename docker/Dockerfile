# Use conda-forge's mambaforge as base image
FROM condaforge/mambaforge:latest

# Set working directory
WORKDIR /app

# Copy pipeline files
COPY . /app/

# Create input/output directories
RUN mkdir -p /data/input \
    && mkdir -p /data/output \
    && mkdir -p /data/reference \
    && mkdir -p /data/logs

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create conda environment from environment.yml
RUN conda env create -f environment.yml \
    && conda clean -afy

# Add conda environment activation to bash script
RUN echo "source activate rnaseq" > ~/.bashrc
ENV PATH /opt/conda/envs/rnaseq/bin:$PATH

# Install the pipeline package
RUN pip install -e .

# Create entrypoint script
RUN echo '#!/bin/bash\n\
source activate rnaseq\n\
python -m bulkrnaseq \
    --mode ${MODE:-"processing"} \
    --input-dir ${INPUT_DIR:-"/data/input"} \
    --output-dir ${OUTPUT_DIR:-"/data/output"} \
    --genome-dir ${GENOME_DIR:-"/data/reference"} \
    --threads ${THREADS:-"8"}' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Set default environment variables
ENV MODE=processing
ENV INPUT_DIR=/data/input
ENV OUTPUT_DIR=/data/output
ENV GENOME_DIR=/data/reference
ENV THREADS=8

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"] 