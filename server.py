import os
import sys
import time
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer

console = Console()

VIVE_ENV_PATH = os.path.join(os.path.dirname(__file__), "vive", ".env")

def debug_print(msg):
    console.log(f"[bold cyan]DEBUG[/] {time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

def load_config():
    if not os.path.exists(VIVE_ENV_PATH):
        debug_print(f"Config file not found at {VIVE_ENV_PATH}")
        return {}
    load_dotenv(VIVE_ENV_PATH)
    config = {k: v for k, v in os.environ.items() if k.startswith("UNTIS") or k.startswith("VIVE")}
    debug_print(f"Loaded config: {config}")
    return config

def show_menu():
    options = [
        "Show config",
        "Reload config",
        "Start backend services",
        "Stop backend services",
        "Exit"
    ]
    choice = inquirer.select(
        message="Vive Backend Configurator - Use arrow keys to select:",
        choices=options,
        default=options[0],
        pointer="👉"
    ).execute()
    return options.index(choice) + 1

def show_config(config):
    if not config:
        console.print("[yellow]No config loaded.[/yellow]")
        return
    table = Table(title="Current Config", show_header=True, header_style="bold green")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")
    for k, v in config.items():
        table.add_row(k, v)
    console.print(table)

def start_services():
    debug_print("Starting backend services...")
    # Placeholder for actual service start logic
    time.sleep(1)
    debug_print("Backend services started.")

def stop_services():
    debug_print("Stopping backend services...")
    # Placeholder for actual service stop logic
    time.sleep(1)
    debug_print("Backend services stopped.")

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    debug_print("Vive Backend Server starting up...")
    config = load_config()
    running = True
    while running:
        clear_console()
        choice = show_menu()
        if choice == 1:
            debug_print("Displaying current config:")
            show_config(config)
            input("\nPress Enter to return to menu...")
        elif choice == 2:
            debug_print("Reloading config...")
            config = load_config()
            input("\nPress Enter to return to menu...")
        elif choice == 3:
            start_services()
            input("\nPress Enter to return to menu...")
        elif choice == 4:
            stop_services()
            input("\nPress Enter to return to menu...")
        elif choice == 5:
            debug_print("Exiting backend server.")
            running = False

if __name__ == "__main__":
    main()