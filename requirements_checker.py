import subprocess
import sys

try:
    from rich import print as rich_print
except ImportError:
    import re

    def rich_print(*args, **kwargs):
        content = "".join(map(str, args))
        # Remove [color] tags like [red], [bold], etc.
        cleaned = re.sub(r'\[(?:[^\]|\\\.)*?\]', '', content)
        print(cleaned, **kwargs)


def check_requirements() -> None:
    """Checks if all required packages are installed and verifies Ollama status."""
    rich_print("[cyan]Checking Requirements...[/cyan]")

    # Read requirements from file
    required_packages = []
    try:
        with open("requirements.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    required_packages.append(line)
    except FileNotFoundError:
        rich_print(f"[red]Error: requirements.txt not found. Skipping dependency check.[/red]")
        exit(1)

    missing_packages = []
    for package in required_packages:
        if package == "pyyaml":
            # Unique case - it's installed as 'pyyaml', but imported as 'yaml'
            package = "yaml"
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        rich_print(f"\n[red]Missing Required Packages:[/red]")
        for pkg in missing_packages:
            rich_print(f"  - {pkg}")
        rich_print(f"\nTo install dependencies, run: [bold]pip install {' '.join(required_packages)}[/bold]")
    else:
        rich_print("[green]All required packages are installed.[/green]")

    print("\n")
    rich_print("[cyan]Ollama & Model Status Check...[/cyan]")

    try:
        # Check if Ollama is running
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            rich_print(f"[green]✓ Ollama is running properly.[/green]")
            if result.stdout.strip():
                print(result.stdout.strip())
        else:
            rich_print(f"[red]✗ Ollama is not running.[/red]")
            rich_print("Please install Ollama first: https://ollama.com/download")

        # Check for configured models
        from config_manager import DEFAULT_MODEL, FAST_MODEL, STRONG_MODEL
        import ollama
        
        models_to_check = [DEFAULT_MODEL, FAST_MODEL, STRONG_MODEL]
        
        rich_print("\nChecking Model Availability...")
        for model in set(models_to_check):
            if not model: continue
            try:
                info = ollama.show(model=model)
                rich_print(f"  - [green]✓{model}[/green] is available.")
            except Exception:
                rich_print(f"  - [red]✗{model}[/red] is NOT available. Please run 'ollama pull {model}'")

    except FileNotFoundError:
        rich_print(f"[red]✗ Ollama binary not found![/red]")
        rich_print("Please install Ollama first: https://ollama.com/download")
    except Exception as e:
        rich_print(f"[yellow]⚠ Warning: Could not verify Ollama status ({e})[/yellow]")
        rich_print("Make sure Ollama is installed and running.")

    print("\n")
    rich_print("[cyan]Starting Application...[/cyan]")

if __name__ == "__main__":
    check_requirements()