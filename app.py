from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import shutil
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Directory to save uploaded files
UPLOAD_DIR = "tests/data/raw_fastq"

# Ensure the upload directory exists
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <body>
            <h1>Upload a File</h1>
            <form action="/upload/" method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <input type="submit" value="Upload">
            </form>
        </body>
    </html>
    """

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Save the uploaded file
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    logging.info(f"File saved at: {file_location}")

    # Trigger the Snakemake workflow
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
    except subprocess.CalledProcessError as e:
        logging.error(f"Error triggering Snakemake: {e}")
        logging.error(f"Snakemake output: {e.output}")
        return {"error": "Failed to trigger Snakemake"}

    return {"filename": file.filename, "message": "File uploaded and Snakemake workflow triggered."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 