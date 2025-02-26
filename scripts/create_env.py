import tomli
import subprocess
import tempfile
import os

def create_conda_env_from_toml():
    # Read the pyproject.toml file
    with open("pyproject.toml", "rb") as f:
        config = tomli.load(f)
    
    conda_config = config["tool"]["conda-env"]
    
    # Create temporary environment.yml
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp:
        tmp.write(f"name: {conda_config['name']}\n")
        tmp.write("channels:\n")
        for channel in conda_config['channels']:
            tmp.write(f"  - {channel}\n")
        tmp.write("dependencies:\n")
        for dep in conda_config['dependencies']:
            tmp.write(f"  - {dep}\n")
        if 'pip_dependencies' in conda_config:
            tmp.write("  - pip:\n")
            for pip_dep in conda_config['pip_dependencies']:
                tmp.write(f"    - {pip_dep}\n")
    
    # Create conda environment
    try:
        subprocess.run(['conda', 'env', 'create', '-f', tmp.name], check=True)
    finally:
        os.unlink(tmp.name)

if __name__ == "__main__":
    create_conda_env_from_toml() 