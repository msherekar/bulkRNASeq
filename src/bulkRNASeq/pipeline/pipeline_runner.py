import sys
import logging
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from .step_runner import run_pipeline_step
from ..utils.checkpoint import CheckpointManager

def run_full_pipeline(config: dict, logger: logging.Logger, resume: bool = False) -> None:
    """Run full pipeline with checkpoint management."""
    steps = ['qc', 'alignment', 'quantification']
    checkpoint_mgr = CheckpointManager(config)

    if not resume:
        logger.info("[yellow]Starting new pipeline run (clearing previous checkpoints)[/]")
        checkpoint_mgr.clear_checkpoints()
    else:
        last_step = checkpoint_mgr.get_last_successful_step()
        if last_step:
            logger.info(f"[yellow]Resuming pipeline from after {last_step}[/]")
        else:
            logger.info("[yellow]No previous successful steps found, starting from beginning[/]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        overall_progress = progress.add_task("[cyan]Overall Progress", total=len(steps))
        
        for step in steps:
            try:
                run_pipeline_step(step, config, logger, checkpoint_mgr)
                progress.update(overall_progress, advance=1)
                
            except Exception as e:
                logger.error(f"[red]Pipeline failed at {step} step[/]")
                logger.error(f"[red]Error: {str(e)}[/]")
                logger.info("[yellow]To resume pipeline, run with --resume flag[/]")
                sys.exit(1) 