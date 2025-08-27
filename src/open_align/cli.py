from typing import Optional
import typer
from rich import print as rprint
from .core import align as align_cmd
from . import __version__ 
from pathlib import Path
import typer
from rich import print as rprint

app = typer.Typer(help="open-align: CLI + optional GUI")

def version_callback(value: bool):
    if value:
        rprint(f"[bold green]open-align[/] v{__version__}")
        raise typer.Exit()

@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Show version and exit",
        callback=version_callback, is_eager=True
    ),
):
    """Entry point for shared options."""
    pass

@app.command()
def align(
    files: list[Path] = typer.Argument(..., help="List of image files"),
    nfeatures: int = typer.Option(4000, "--nfeatures", "-n", help="Number of ORB features to detect"),
):
    """
    Validate that each file exists and echo the absolute path.
    """
    align_cmd(files, nfeatures)

@app.command()
def gui():
    """Launch the Tkinter GUI."""
    from .gui import launch_gui
    launch_gui()

def main():
    app()
