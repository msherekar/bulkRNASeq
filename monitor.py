import time
import subprocess
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('monitor.log')
    ]
)

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Check if the created file is a .fq.gz file
        if event.is_directory or not event.src_path.endswith('.fq.gz'):
            return
        
        logging.info(f"New file detected: {event.src_path}")
        
        # Wait a short time to ensure file is completely written
        time.sleep(5)
        
        # Trigger Snakemake
        try:
            logging.info("Starting Snakemake workflow...")
            result = subprocess.run(
                ["snakemake", "--use-conda", "-j", "8", "--rerun-incomplete"],
                check=True,
                capture_output=True,
                text=True
            )
            logging.info("Snakemake completed successfully.")
            logging.debug(result.stdout)
            logging.error(result.stderr)  # Capture any error output
        except subprocess.CalledProcessError as e:
            logging.error(f"Error triggering Snakemake: {e}")
            logging.error(f"Snakemake output: {e.output}")
            logging.error(f"Snakemake stderr: {e.stderr}")  # Capture stderr for more details

if __name__ == "__main__":
    path = "tests/data/raw_fastq"  # Path to monitor
    
    # Ensure the monitored directory exists
    Path(path).mkdir(parents=True, exist_ok=True)
    
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)

    logging.info(f"Starting to monitor {path} for new files...")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping file monitoring...")
        observer.stop()
    observer.join()