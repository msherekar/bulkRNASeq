# this code does the basic checks
# like if config files exists or not and if the config file has all the necessary keys/information
# if the directories exist or not

import os, json, yaml

def check_config(config):
    """
    This function checks if the config file exists and has all the necessary keys/information
    Args:
        config: Either path to the config file (str) or loaded config dict
    Returns:
        True if the config file exists and has all the necessary keys/information, False otherwise
    """
    # If config is a string (file path), load it
    if isinstance(config, str):
        if not os.path.exists(config):
            raise FileNotFoundError(f"The config file {config} does not exist")
        with open(config, 'r') as f:
            config = yaml.safe_load(f)
    
    # check if the config has all the necessary keys/information
    if not all(key in config for key in ['input', 'output', 'genome', 'aligners', 'parameters', 'pipeline_steps']):
        raise ValueError("The config file does not have all the necessary keys/information")
    return True

# TODO: Include sub-parameters withiin all parameters

def check_preprocessing_directories(config):
    """
    This function checks if the preprocessing directories exist and creates them if they don't
    Args:
        config: Config dictionary
    Returns:
        True if the preprocessing directories exist or were created successfully
    """
    # Check input directories
    if not os.path.exists(config['input']['fastq_dir']):
        raise FileNotFoundError(f"The input fastq directory {config['input']['fastq_dir']} does not exist")

    # Create output directories if they don't exist
    output_dirs = [
        config['output']['qc_dir'],
        config['output']['qc_trimmed_dir'],
        config['output']['trimmed_fastq_dir'],
        config['output']['aligned_dir'],
        config['output']['counts_dir'],
        config['output']['results_dir']
    ]

    for dir_path in output_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")

    return True

def check_postprocessing_directories(config):               
    """
    This function checks if the postprocessing directories exist
    Args:
        config: Path to the config file
    Returns:
        True if the postprocessing directories exist, False otherwise
    """
    # check if the results directory exists
    if not os.path.exists(config['results']):
        raise FileNotFoundError(f"The results directory {config['results']} does not exist")
    # check if the logs directory exists
    if not os.path.exists(config['logs']):
        raise FileNotFoundError(f"The logs directory {config['logs']} does not exist")
        