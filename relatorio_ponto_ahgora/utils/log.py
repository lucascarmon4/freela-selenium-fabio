# utils_log.py

from rich.console import Console
from rich.markup import escape
from datetime import datetime

class UtilsLog:
    console = Console()
    
    @staticmethod
    def _timestamp():
        return datetime.now().strftime("[%H:%M:%S]")

    @staticmethod
    def info(msg: str):
        UtilsLog.console.print(f"{UtilsLog._timestamp()} [bold cyan]INFO[/bold cyan] - {escape(msg)}")

    @staticmethod
    def success(msg: str):
        UtilsLog.console.print(f"{UtilsLog._timestamp()} [bold green]SUCESSO[/bold green] - {escape(msg)}")

    @staticmethod
    def warning(msg: str):
        UtilsLog.console.print(f"{UtilsLog._timestamp()} [bold yellow]AVISO[/bold yellow] - {escape(msg)}")

    @staticmethod
    def error(msg: str):
        UtilsLog.console.print(f"{UtilsLog._timestamp()} [bold red]ERRO[/bold red] - {escape(msg)}")

    @staticmethod
    def debug(msg: str):
        UtilsLog.console.print(f"{UtilsLog._timestamp()} [dim]DEBUG[/dim] - {escape(msg)}")

    @staticmethod
    def option(title: str, options: dict):
        UtilsLog.console.print(f"\n[bold underline]{escape(title)}[/bold underline]")
        for number, value in options.items():
            UtilsLog.console.print(f"[{number}] - {value}")
