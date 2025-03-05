import time
import os
import subprocess
import logging
from pathlib import Path
import update_sample  # Ensure the correct import

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

WATCH_DIR = "tests/data/raw_fastq"
CHECK_INTERVAL = 5  # Check every 5 seconds

# Ensure directory exists
Path(WATCH_DIR).mkdir(parents=True, exist_ok=True)

# Store seen files
seen_files = set(os.listdir(WATCH_DIR))

logging.info(f"Monitoring {WATCH_DIR} for new files...")

LOCK_FILE = ".snakemake_lock"

def is_snakemake_running():
    return os.path.exists(LOCK_FILE)

def run_snakemake():
    if is_snakemake_running():
        logging.info("Snakemake is already running. Exiting.")
        return

    # Create a lock file
    with open(LOCK_FILE, 'w') as f:
        f.write("Locked")

    try:
        logging.info("Starting Snakemake...")
        result = subprocess.run(
            ["snakemake", "--use-conda", "-j", "8", "--rerun-incomplete"],
            check=True,
            capture_output=True,
            text=True
        )
        logging.info("Snakemake completed successfully.")
        logging.debug(result.stdout)
        logging.error(result.stderr)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error triggering Snakemake: {e}")
        logging.error(f"Snakemake output: {e.output}")
        logging.error(f"Snakemake stderr: {e.stderr}")
    finally:
        # Remove the lock file after Snakemake finishes
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        else:
            logging.warning("Lock file not found, it may have been removed manually.")

while True:
    try:
        logging.info("Checking for new files...")
        # Get the current set of files
        current_files = set(os.listdir(WATCH_DIR))

        # Detect new files
        new_files = current_files - seen_files
        if new_files:
            for file in new_files:
                if file.endswith(".fq.gz"):
                    file_path = os.path.join(WATCH_DIR, file)
                    logging.info(f"New file detected: {file_path}")

                    # Update the sample list
                    logging.info("Updating sample list...")
                    update_sample.update_sample_list()

                    # Run Snakemake
                    run_snakemake()

            # Update seen files
            seen_files = current_files

        time.sleep(CHECK_INTERVAL)  # Wait before checking again

    except KeyboardInterrupt:
        logging.info("Stopping monitoring...")
        break
