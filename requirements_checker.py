import subprocess
import logging

logger = logging.getLogger("Assistant")

def check_requirements() -> None:
    """Checks if all required packages are installed and verifies Ollama status."""
    print("=" * 50)
    print("Checking Requirements...")
    print("=" * 50)

    # Read requirements from file
    required_packages = []
    try:
        with open("requirements.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    required_packages.append(line)
    except FileNotFoundError:
        print("Warning: requirements.txt not found. Skipping dependency check.")
        return

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
        print(f"\nMissing Required Packages:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print(f"\nTo install dependencies, run: pip install {' '.join(required_packages)}")
    else:
        print("All required packages are installed.")

    print("\n")
    print("=" * 50)
    print("Ollama & Model Status Check...")
    print("=" * 50)

    try:
        # Check if Ollama is running
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ Ollama is running properly.")
            if result.stdout.strip():
                print(result.stdout.strip())
        else:
            print("✗ Ollama is not running.")
            print("Please install Ollama first: https://ollama.com/download")

        # Check for configured models
        from config_manager import DEFAULT_MODEL, FAST_MODEL, STRONG_MODEL
        import ollama
        
        models_to_check = [DEFAULT_MODEL, FAST_MODEL, STRONG_MODEL]
        
        print("\nChecking Model Availability...")
        for model in set(models_to_check):
            if not model: continue
            try:
                info = ollama.show(model=model)
                print(f"  - [green]✓{model}[/green] is available.")
            except Exception:
                print(f"  - [red]✗{model}[/red] is NOT available. Please run 'ollama pull {model}'")

    except FileNotFoundError:
        print("✗ Ollama binary not found!")
        print("Please install Ollama first: https://ollama.com/download")
    except Exception as e:
        print(f"⚠ Warning: Could not verify Ollama status ({e})")
        print("Make sure Ollama is installed and running.")

    print("\n")
    print("=" * 50)
    print("Starting Application...")
    print("=" * 50)

if __name__ == "__main__":
    check_requirements()