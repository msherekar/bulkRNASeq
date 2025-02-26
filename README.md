# Bulk RNA Sequencing Analysis Pipeline

A comprehensive Snakemake-based pipeline for analyzing bulk RNA sequencing data, from raw FASTQ files to differential expression and pathway analysis.

## Features

- Quality control with FastQC
- Read alignment with HISAT2
- Transcript quantification with Kallisto
- Gene expression counting with featureCounts
- Differential expression analysis
- GO enrichment analysis using GSEAPY
- Comprehensive final report generation
- Automated workflow management with Snakemake

## Prerequisites

- Python ≥3.8
- Conda package manager
  - If you don't have conda, install it from [here](https://docs.conda.io/en/latest/miniconda.html)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/msherekar/bulkRNASeq.git
cd bulkRNASeq
```

2. Install the package and dependencies:
```bash
# Install with all dependencies
pip install -e .[all]

# Or install specific components
pip install -e .[qc,align]  # For just QC and alignment
pip install -e .[post]      # For just postprocessing
```

## Usage

### Configuration

1. Edit `config/snakemake_config.yaml` to set:
   - Sample information
   - Input/output directories
   - Reference genome paths
   - Tool-specific parameters

### Running the Pipeline

1. **Dry run** (see what will be executed):
```bash
snakemake --configfile config/snakemake_config.yaml -n
```

2. **Run the full pipeline**:
```bash
snakemake --configfile config/snakemake_config.yaml --use-conda -j 4
```

3. **Run specific steps**:
```bash
# Run just QC
snakemake --configfile config/snakemake_config.yaml --use-conda -j 4 results/qc/{sample}_fastqc.html

# Run up to alignment
snakemake --configfile config/snakemake_config.yaml --use-conda -j 4 results/aligned/{sample}.bam
```

4. **Generate workflow visualization**:
```bash
snakemake --configfile config/snakemake_config.yaml --dag | dot -Tpdf > workflow.pdf
```

### Output Structure

```
results/
├── qc/                  # FastQC reports
├── aligned/             # HISAT2 BAM files
├── kallisto/            # Kallisto quantification
├── counts/              # featureCounts output
└── final_report.md      # Comprehensive analysis report
```

## Pipeline Steps

1. **Quality Control**
   - FastQC analysis of raw reads
   - Quality metrics and contamination check

2. **Alignment & Quantification**
   - HISAT2 alignment to reference genome
   - Kallisto transcript quantification
   - BAM file generation and indexing

3. **Expression Analysis**
   - Gene-level counting with featureCounts
   - Expression level visualization
   - Sample correlation analysis

4. **Functional Analysis**
   - GO enrichment analysis
   - Pathway visualization
   - Final report generation

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.












- Activate the conda environment
- Run the pipeline with your specified parameters
- Save logs in the `logs` directory

### Pipeline Flow

The execution follows this path:
1. `launch.sh` → Submits job with parameters
2. `bulkrnaseq.sh` → Sets up environment and runs Python
3. `__main__.py` → Entry point for the package
4. `main.py` → Contains main pipeline logic

## Usage Modes

### 1. Preprocessing Mode
```bash
bulkrnaseq --mode preprocessing [additional args]
```
Handles raw sequencing data processing:
- Quality control with FastQC
- Read alignment with STAR/HISAT2
- Count generation

### 2. Postprocessing Mode
```bash
bulkrnaseq --mode postprocessing [additional args]
```
Performs downstream analysis:
- Differential expression analysis
- Pathway analysis
- Visualization

### 3. Complete Processing Mode
```bash
bulkrnaseq --mode processing [additional args]
```
Runs both preprocessing and postprocessing pipelines sequentially.

## Directory Structure
```
bulkrnaseq/
├── main.py              # Main pipeline logic
├── __main__.py         # Package entry point
├── preprocessing/       # Preprocessing pipeline
│   └── main.py
├── postprocessing/     # Postprocessing pipeline
│   └── main.py
├── scripts/            # Utility scripts
│   └── create_env.py   # Environment setup
├── launch.sh           # HPC job submission script
├── bulkrnaseq.sh       # Pipeline execution script
└── pyproject.toml      # Project configuration
```

## Required Input Structure

Place your input files in the following structure:
```
data/
└── raw/
    ├── sample1_R1.fastq.gz
    ├── sample1_R2.fastq.gz
    ├── sample2_R1.fastq.gz
    └── sample2_R2.fastq.gz

ref_genome/
├── genome.fa
└── annotation.gtf
```

## Dependencies

The pipeline uses a combination of Python packages and bioinformatics tools:

### Core Python Packages
- pandas ≥2.2.3
- numpy ≥2.1.3
- scipy ≥1.15.1
- matplotlib ≥3.10.0
- seaborn ≥0.13.2
- scikit-learn ≥1.6.1

### Bioinformatics Tools
- FastQC
- STAR
- HISAT2
- Kallisto
- Samtools
- DESeq2
- MultiQC
- HTSeq

### R Packages
- R ≥4.4.2
- tidyverse
- DESeq2

## Troubleshooting

Common issues and solutions:

1. Environment creation fails:
```bash
# Try updating conda first
conda update -n base conda
# Then retry environment creation
python scripts/create_env.py
```

2. Pipeline fails to start:
```bash
# Check if environment is activated
conda activate rnaseq
# Verify installation
pip list | grep bulkrnaseq
```

3. Job submission fails:
```bash
# Check SLURM queue
squeue -u $USER
# Check error logs
cat logs/bulkRNA_*.err
```

## Development

For development, additional tools are available:
```bash
pip install -e ".[dev]"
```

This installs:
- pytest
- black
- flake8

## License

This project belongs to Mukul Sherekar.

## Contact

Your Name - mukulsherekar@gmail.com

Project Link: [bulkRNASeq](https://github.com/msherekar/bulkRNASeq)

## API Usage

The pipeline can be accessed through a REST API. The service runs on `http://localhost:8000` after starting with Docker Compose.

### Starting the Service
```bash
# Start all services
docker-compose up
```

### Using the API

Users can interact with the API in two ways:

#### 1. Using Postman

1. **Upload Files**:
   - URL: `http://localhost:8000/upload/`
   - Method: POST
   - Body: form-data
     - Key: "files" (select file type)
     - Value: Select your FASTQ files
     - Add "mode" key with value "preprocessing", "postprocessing", or "processing"

2. **Check Job Status**:
   - URL: `http://localhost:8000/status/{job_id}`
   - Method: GET
   - Replace {job_id} with the ID received from upload

3. **Download Results**:
   - URL: `http://localhost:8000/results/{job_id}`
   - Method: GET
   - Results will download as a zip file

4. **Delete Job**:
   - URL: `http://localhost:8000/job/{job_id}`
   - Method: DELETE

#### 2. Using cURL Commands

### Upload Files
```bash
curl -X POST "http://localhost:8000/upload/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@sample1_R1.fastq.gz" \
     -F "files=@sample1_R2.fastq.gz" \
     -F "mode=preprocessing"
```

### Check Job Status
```bash
curl -X GET "http://localhost:8000/status/{job_id}" \
     -H "accept: application/json"
```

### Download Results
```bash
curl -X GET "http://localhost:8000/results/{job_id}" \
     -o results.zip
```

### Delete Job
```bash
curl -X DELETE "http://localhost:8000/status/{job_id}" \
     -H "accept: application/json"
```

### How It Works

1. **Upload Process**:
   - User uploads FASTQ files
   - System generates a unique job ID
   - Files are saved in a job-specific folder
   - User receives the job ID for tracking

2. **Processing**:
   - Files are processed according to the specified mode
   - Progress can be monitored via status endpoint
   - Status will show: "queued" → "processing" → "completed"

3. **Results**:
   - When status shows "completed", results can be downloaded
   - Results are provided as a zip file
   - Results include analysis outputs and logs

### Example Workflow

1. Upload your files:
   ```bash
   curl -X POST "http://localhost:8000/upload/" \
        -F "files=@sample1_R1.fastq.gz" \
        -F "files=@sample1_R2.fastq.gz" \
        -F "mode=preprocessing"
   ```

2. Note the job_id from the response:
   ```json
   {
       "job_id": "550e8400-e29b-41d4-a716-446655440000",
       "message": "Files uploaded successfully. Processing started.",
       "status": "queued"
   }
   ```

3. Check status periodically:
   ```bash
   curl "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000"
   ```

4. Download results when complete:
   ```bash
   curl "http://localhost:8000/results/550e8400-e29b-41d4-a716-446655440000" \
        -o results.zip
   ```

### Troubleshooting API Issues

1. **Service not responding**:
   ```bash
   # Check if containers are running
   docker-compose ps
   
   # Check logs
   docker-compose logs api
   ```

2. **Upload fails**:
   - Ensure files are in .fastq.gz or .fq.gz format
   - Check file permissions
   - Verify file sizes are within limits

3. **Cannot download results**:
   - Verify job status is "completed"
   - Check available disk space
   - Ensure job ID is correct