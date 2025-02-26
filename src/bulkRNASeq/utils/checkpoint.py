import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class CheckpointManager:
    """Manages pipeline checkpoints and progress tracking."""
    
    def __init__(self, checkpoint_dir: str):
        """Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory path where checkpoint files will be stored
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_file = self.checkpoint_dir / '.pipeline_checkpoint.json'
        self.checkpoints = self._load_checkpoints()
    
    def _load_checkpoints(self) -> Dict:
        """Load existing checkpoints if any."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file) as f:
                return json.load(f)
        return {
            'last_completed_step': None,
            'steps': {},
            'last_updated': None
        }
    
    def save_checkpoint(self, step: str, status: str, metadata: Optional[Dict] = None):
        """Save checkpoint for a step."""
        self.checkpoints['steps'][step] = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.checkpoints['last_updated'] = datetime.now().isoformat()
        
        if status == 'completed':
            self.checkpoints['last_completed_step'] = step
        
        # Ensure directory exists
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save checkpoint file
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoints, f, indent=2)
    
    def get_last_successful_step(self) -> Optional[str]:
        """Get the last successfully completed step."""
        return self.checkpoints.get('last_completed_step')
    
    def should_run_step(self, step: str, steps: List[str]) -> bool:
        """Determine if a step should be run based on checkpoint status."""
        last_step = self.get_last_successful_step()
        if not last_step:
            return True
        
        # Find indices in the pipeline
        try:
            last_idx = steps.index(last_step)
            current_idx = steps.index(step)
            return current_idx > last_idx
        except ValueError:
            return True
    
    def should_skip_step(self, step: str) -> bool:
        """Check if a step should be skipped (already completed successfully)."""
        step_info = self.checkpoints.get('steps', {}).get(step, {})
        return step_info.get('status') == 'completed'
    
    def clear_checkpoints(self):
        """Clear all checkpoints."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        self.checkpoints = {
            'last_completed_step': None,
            'steps': {},
            'last_updated': None
        } 