"""Preprocessing modules for RNA-seq data."""
from .main import main
from .pipeline_runner import run_preprocessing_pipeline

# This makes the function available when importing from bulkRNASeq.preprocessing
__all__ = ['run_preprocessing_pipeline']
