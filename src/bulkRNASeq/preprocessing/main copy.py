import argparse
import os
from .qc import run_fastqc
from .trimming import conditional_trimming_step
from .histat2 import run_hisat2_alignment
from .salmon import run_salmon_quant
from .kallisto import run_kallisto_quant
from .bam_processing import run_bam_processing
from .featurecounts import run_featurecounts
#from .diffexp import run_deseq2
import logging

def main():
    parser = argparse.ArgumentParser(
        description="Preprocessing Pipeline for Bulk RNA-seq Data"
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=["qc", "trim", "alignment", "bam", "quant", "salmon", "kallisto", "diff", "normalization"],
        required=True,
        help="Pipeline step to execute."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to the input file (raw FASTQ for qc/trim/salmon, sorted BAM for quant)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Directory for output files"
    )
    # Parameters for trimming step
    parser.add_argument(
        "--fastqc-summary",
        type=str,
        help="Path to the FastQC summary file (for adapter check)"
    )
    parser.add_argument(
        "--trimmed-output",
        type=str,
        help="Output path for trimmed reads"
    )
    parser.add_argument(
        "--adapter-seq",
        type=str,
        default=None,
        help="Adapter sequence to trim (if needed)"
    )
    # Parameters for HISAT2 alignment
    parser.add_argument(
        "--hisat2-index",
        type=str,
        help="Path to the HISAT2 index prefix"
    )
    # Parameters for featureCounts quantification
    parser.add_argument(
        "--annotation",
        type=str,
        help="Path to the gene annotation GTF file (for featureCounts quantification)"
    )
    # Parameters for differential expression analysis
    parser.add_argument(
        "--counts", "-c",
        type=str,
        help="Path to the counts file (for diff analysis)"
    )
    parser.add_argument(
        "--design", "-d",
        type=str,
        help="Path to the design file (for diff analysis)"
    )
    # Parameter for Salmon quantification
    parser.add_argument(
        "--salmon-index",
        type=str,
        help="Path to the Salmon index directory"
    )

    # Parameter for Kallisto quantification
    parser.add_argument(
        "--kallisto-index",
        type=str,
        help="Path to the Kallisto index directory"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=8,
        help="Number of threads to use (default: 8)"
    )
    # Add trimming-specific arguments
    parser.add_argument("--min-quality", type=int, default=20,
                      help="Minimum quality score for trimming")
    parser.add_argument("--min-length", type=int, default=50,
                      help="Minimum read length to keep")
    
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        if args.step == "qc":
            run_fastqc(args.input, args.output)
        elif args.step == "trim":
            # Construct output filename for trimmed file
            output_file = os.path.join(args.output, "trimmed",
                                     os.path.basename(args.input).replace(".fq.gz", "_trimmed.fq.gz"))
            conditional_trimming_step(
                input_file=args.input,
                output_file=output_file,
                min_quality=args.min_quality,
                min_length=args.min_length
            )
        elif args.step == "alignment":
            if not args.hisat2_index:
                raise ValueError("--hisat2-index is required for alignment step")
                
            run_hisat2_alignment(
                input_file=args.input,
                output_dir=args.output,
                hisat2_index=args.hisat2_index,
                threads=args.threads,
                logger=logger
            )
        elif args.step == "salmon":
            run_salmon_quant(args.input, args.output, args.salmon_index, args.threads)
        elif args.step == "kallisto":
            run_kallisto_quant(args.input, args.output, args.kallisto_index, args.threads)
        elif args.step == "bam":
            # Call BAM processing step if applicable
            run_bam_processing(args.input, args.output)
        elif args.step == "quant":
            run_featurecounts(args.input, args.output, args.annotation, args.threads)

        elif args.step == "diff":
            if args.counts is None or args.design is None:
                print("For differential expression analysis, please provide --counts and --design files.")
                exit(1)
            run_deseq2(args.counts, args.design, args.output)
        
        elif args.step == "normalization":
            print("Normalization is typically performed as part of differential expression analysis.")
        else:
            print("Unknown step specified.")
            exit(1)

    except Exception as e:
        logger.error(f"Error in {args.step} step: {str(e)}")
        raise

if __name__ == "__main__":
    main()
