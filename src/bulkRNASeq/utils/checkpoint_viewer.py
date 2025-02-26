import json
import yaml
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def get_status_style(status: str) -> tuple:
    """Get status display text and style."""
    status_styles = {
        'completed': ('COMPLETED', 'green'),
        'failed': ('FAILED', 'red bold'),
        'running': ('RUNNING', 'yellow'),
        'pending': ('PENDING', 'blue')
    }
    return status_styles.get(status, (status.upper(), 'white'))

def view_checkpoints(config_file: str):
    """View current checkpoint status with rich formatting."""
    console = Console()
    
    try:
        # Read config file
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        results_dir = Path(config['output']['results_dir'])
        checkpoint_file = results_dir / '.pipeline_checkpoint.json'
        
        if not checkpoint_file.exists():
            console.print(Panel(
                "[yellow]No checkpoint file found. Pipeline hasn't been run yet.",
                title="Pipeline Status",
                border_style="yellow"
            ))
            return
            
        with open(checkpoint_file) as f:
            checkpoints = json.load(f)
        
        # Create main status table
        table = Table(
            title="Pipeline Checkpoint Status",
            title_style="bold cyan",
            border_style="blue",
            header_style="bold magenta"
        )
        
        # Add columns
        table.add_column("Step", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Start Time", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("Error Details", style="red", max_width=50)
        
        # Add rows
        current_time = datetime.now()
        for step, details in checkpoints['steps'].items():
            status = details['status']
            timestamp = datetime.fromisoformat(details['timestamp'])
            
            # Calculate duration
            if status == 'running':
                duration = str(current_time - timestamp).split('.')[0]
            elif 'end_time' in details:
                end_time = datetime.fromisoformat(details['end_time'])
                duration = str(end_time - timestamp).split('.')[0]
            else:
                duration = "N/A"
            
            # Get error details if any
            error = details.get('metadata', {}).get('error', '')
            if error:
                error = Text(error, style="red", overflow="fold")
            
            # Get styled status
            status_text, status_style = get_status_style(status)
            
            table.add_row(
                step,
                f"[{status_style}]{status_text}[/]",
                format_timestamp(details['timestamp']),
                duration,
                str(error)
            )
        
        # Print the table
        console.print("\n")
        console.print(table)
        
        # Print summary panel
        last_step = checkpoints.get('last_completed_step')
        summary_text = []
        if last_step:
            summary_text.append(f"Last completed step: [green]{last_step}[/]")
        
        failed_steps = [s for s, d in checkpoints['steps'].items() if d['status'] == 'failed']
        if failed_steps:
            summary_text.append(f"Failed steps: [red]{', '.join(failed_steps)}[/]")
            summary_text.append("\n[yellow]To resume pipeline from the last successful step, run:[/]")
            summary_text.append(f"[blue]bulkrnaseq --config {config_file} --resume[/]")
        
        if summary_text:
            console.print(Panel(
                "\n".join(summary_text),
                title="Pipeline Summary",
                border_style="cyan"
            ))
            
    except Exception as e:
        console.print(Panel(
            f"[red]Error reading checkpoint file: {str(e)}[/]",
            title="Error",
            border_style="red"
        ))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        view_checkpoints(sys.argv[1])
    else:
        console = Console()
        console.print("[red]Please provide config file path[/]") 