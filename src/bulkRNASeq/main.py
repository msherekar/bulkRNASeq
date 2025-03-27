# main file for entry into bulk RNAseq pipeline
# Users can choose to run pipeline in three modes - preprocessing, postprocessing, or full pipeline
# Users can also choose to resume pipeline from last successful step - Later not now

# Arguments just include type of mode and config file

import argparse
from src.bulkRNASeq.preprocessing import run_preprocessing
from src.bulkRNASeq.postprocessing import run_postprocessing


def main():
    parser = argparse.ArgumentParser(description="Bulk RNAseq pipeline")
    parser.add_argument("--mode", required=True, help="Mode to run the pipeline in")
    parser.add_argument("--config", required=True, help="Path to the config file")
    args = parser.parse_args()

    if args.mode == "preprocessing":
        run_preprocessing(args.config)
    elif args.mode == "postprocessing":
        run_postprocessing(args.config)
    elif args.mode == "full":
        run_preprocessing(args.config)
        run_postprocessing(args.config)
    else:
        print("Invalid mode")

if __name__ == "__main__":
    main()

