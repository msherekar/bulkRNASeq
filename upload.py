from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import shutil
import logging
from pathlib import Path
import uvicorn
import subprocess

# Start monitor.py in the background
subprocess.Popen(["python", "monitor.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Set up logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

UPLOAD_DIR = "tests/data/raw_fastq"
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
    """Save uploaded file."""
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    logging.info(f"File saved at: {file_location}")

    # DO NOT trigger Snakemake here! Let `monitor.py` handle it.
    
    return {"filename": file.filename, "message": "File uploaded successfully."}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
